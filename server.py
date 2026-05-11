"""
Qwen3-TTS Local Dev Server
Serves the static frontend and proxies TTS requests to DashScope server-side,
eliminating the need for the cors-anywhere proxy.

Usage:
    $env:DASHSCOPE_API_KEY = "sk-..."   # PowerShell
    python server.py

Then open http://localhost:5000 in your browser.
"""

import os
import sys
import tempfile

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from qwen_tts import OUTPUT_FILE, generate_audio

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "Name is required."}), 400

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        return jsonify(
            {"error": "DASHSCOPE_API_KEY is not set on the server."}
        ), 500

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        generate_audio(name=name, api_key=api_key, output_path=tmp_path)

        response = send_file(
            tmp_path,
            mimetype="audio/wav",
            as_attachment=True,
            download_name=OUTPUT_FILE,
        )

        @response.call_on_close
        def _cleanup_temp_file() -> None:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        return response
    except RuntimeError as exc:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        return jsonify({"error": str(exc)}), 502


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    api_key_set = bool(os.environ.get("DASHSCOPE_API_KEY"))

    if not api_key_set:
        print(
            "[server] WARNING: DASHSCOPE_API_KEY is not set.\n"
            "         Set it before starting: $env:DASHSCOPE_API_KEY='sk-...'",
            file=sys.stderr,
        )

    print(f"[server] Starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

