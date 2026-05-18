"""
Backend-only API server for Qwen3-TTS.

Usage (PowerShell):
    Copy-Item .env.example .env
    pip install -r requirements.txt
    python server.py
"""

import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from qwen_tts import OUTPUT_FILE, generate_audio, get_phrase_count, list_phrase_templates, render_phrase

BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_FRONTEND_DIR = BACKEND_DIR.parent
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", str(DEFAULT_FRONTEND_DIR))).resolve()

app = Flask(__name__)
CORS(app)


@app.get("/")
def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return jsonify({"error": f"Frontend not found at {index_path}"}), 404

    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(FRONTEND_DIR, path)

    return jsonify({"error": "Not found."}), 404


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/phrases")
def phrases():
    name = (request.args.get("name") or "Carlos").strip() or "Carlos"
    templates = list_phrase_templates()

    return jsonify(
        {
            "count": get_phrase_count(),
            "phrases": [
                {
                    "index": index,
                    "template": template,
                    "text": render_phrase(name=name, phrase_index=index),
                }
                for index, template in enumerate(templates, start=1)
            ],
        }
    )


@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phrase_index = data.get("phraseIndex")
    if not name:
        return jsonify({"error": "Name is required."}), 400

    if phrase_index is not None:
        try:
            phrase_index = int(phrase_index)
        except (TypeError, ValueError):
            return jsonify({"error": "phraseIndex must be an integer."}), 400

        if phrase_index < 1 or phrase_index > get_phrase_count():
            return jsonify(
                {"error": f"phraseIndex must be between 1 and {get_phrase_count()}."}
            ), 400

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        return jsonify({"error": "DASHSCOPE_API_KEY is not set on the server."}), 500

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        generate_audio(
            name=name,
            api_key=api_key,
            output_path=tmp_path,
            phrase_index=phrase_index,
        )

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
    print(f"[server] Serving frontend from: {FRONTEND_DIR}")
    app.run(host="0.0.0.0", port=port, debug=True)

