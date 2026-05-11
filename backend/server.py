"""
Backend-only API server for Qwen3-TTS.

Usage (PowerShell):
    Copy-Item .env.example .env
    pip install -r requirements.txt
    python server.py
"""

import os
import tempfile

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from qwen_tts import OUTPUT_FILE, generate_audio

app = Flask(__name__)
CORS(app)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required."}), 400

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        return jsonify({"error": "DASHSCOPE_API_KEY is not set on the server."}), 500

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

