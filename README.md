# qwen3-tts-concept

Proof-of-concept for the [Alibaba Cloud Qwen3-TTS](https://www.alibabacloud.com/help/en/model-studio/qwen-tts-api) voice-cloning API. Generates personalized Portuguese audio clips themed around the 2026 FIFA World Cup.

## Quick Start

### Web app (Flask server - recommended)

The frontend is served by a local Flask server that calls DashScope server-side, so there's no CORS proxy needed.

Copy `.env.example` to `.env` and set values (`DASHSCOPE_API_KEY`, `API_ENDPOINT`, `MODEL`, `VOICE`, `LANGUAGE`).

Edit phrase templates in `phrases.txt` (one phrase per line; keep `{name}` placeholder).

```powershell
Copy-Item .env.example .env
pip install -r requirements.txt
python server.py
```

Then open <http://localhost:5000>.

### Python CLI (no browser needed)

```powershell
python qwen_tts.py --name "Carlos" --api-key "sk-..."
# or with env var set:
python qwen_tts.py --name "Carlos"
```

Saves output as `qwen-tts-synthesis.wav`. Override with `--output <path>`.

## Project Structure

| File | Description |
|---|---|
| `server.py` | Flask server - serves frontend + `/api/generate` endpoint |
| `qwen_tts.py` | Core TTS logic + standalone CLI |
| `phrases.txt` | Editable phrase templates (one per line, `{name}` placeholder) |
| `requirements.txt` | Python dependencies (`flask`, `flask-cors`) |
| `index.html` | Frontend UI |
| `script.js` | Frontend logic (posts to `/api/generate`, plays blob response) |
| `styles.css` | Glassmorphism design system |

## Backend Handoff Bundle

A backend-only package is available in `backend/` with:

- `backend/server.py`
- `backend/qwen_tts.py`
- `backend/phrases.txt`
- `backend/.env.example`
- `backend/API_CONTRACT.md`
- `backend/README.md`
