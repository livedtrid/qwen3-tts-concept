# AGENTS.md

## Project Overview

A frontend + Flask backend proof-of-concept for Alibaba Cloud **Qwen3-TTS**. It generates personalized Portuguese audio clips themed around the 2026 FIFA World Cup.

## Architecture

| File | Role |
|---|---|
| `backend/server.py` | Flask dev server - serves `/api/generate`, `/api/phrases`, and optionally the root frontend |
| `backend/qwen_tts.py` | Core TTS logic (`generate_audio()`) + standalone CLI |
| `backend/phrases.txt` | Phrase templates (one per line, include `{name}`) |
| `backend/requirements.txt` | Python dependencies: `flask`, `flask-cors` |
| `index.html` | Single-page UI shell (no API key input) |
| `script.js` | Posts `{name}` to the backend API, receives WAV blob |
| `styles.css` | All styles; CSS custom properties in `:root` |

Data flow: user submits name -> `POST /api/generate` -> `backend/server.py` calls `generate_audio()` from `backend/qwen_tts.py` -> DashScope API -> WAV bytes streamed back -> frontend creates a `Blob` URL for `<audio>` + download link.

## Running the Project

### Web app (Flask)
```powershell
Copy-Item backend/.env.example backend/.env
pip install -r backend/requirements.txt
python backend/server.py
# open http://localhost:5000
```

### Python CLI
```powershell
python backend/qwen_tts.py --name "Carlos" --api-key "sk-..."
# or with env var set:
python backend/qwen_tts.py --name "Carlos"
```

## API Integration Details

- **Endpoint:** `https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`
- **Model:** `qwen3-tts-vc-2026-01-22`
- **Voice ID:** `qwen-tts-vc-roberto_pt-voice-20260429004312101-aab6`
- **Auth:** `Authorization: Bearer <api-key>` (server-side env `DASHSCOPE_API_KEY`)
- **Response audio path:** `data.output.audio.url`
- Text selection: random line from `backend/phrases.txt`, formatted with `{name}`

## Environment Config

`backend/qwen_tts.py` reads `backend/.env` automatically (if present):

- `DASHSCOPE_API_KEY`
- `API_ENDPOINT`
- `MODEL`
- `VOICE`
- `LANGUAGE`

Phrase templates are edited in `backend/phrases.txt`.
