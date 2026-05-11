# AGENTS.md

## Project Overview

A frontend + Flask backend proof-of-concept for Alibaba Cloud **Qwen3-TTS**. It generates personalized Portuguese audio clips themed around the 2026 FIFA World Cup.

## Architecture

| File | Role |
|---|---|
| `server.py` | Flask dev server - serves static files + `/api/generate` endpoint |
| `qwen_tts.py` | Core TTS logic (`generate_audio()`) + standalone CLI |
| `phrases.txt` | Phrase templates (one per line, include `{name}`) |
| `requirements.txt` | Python dependencies: `flask`, `flask-cors` |
| `backend/` | Backend-only handoff bundle for teammates |
| `index.html` | Single-page UI shell (no API key input) |
| `script.js` | Posts `{name}` to `/api/generate`, receives WAV blob |
| `styles.css` | All styles; CSS custom properties in `:root` |

Data flow: user submits name -> `POST /api/generate` -> `server.py` calls `generate_audio()` from `qwen_tts.py` -> DashScope API -> WAV bytes streamed back -> frontend creates a `Blob` URL for `<audio>` + download link.

## Running the Project

### Web app (Flask)
```powershell
Copy-Item .env.example .env
pip install -r requirements.txt
python server.py
# open http://localhost:5000
```

### Python CLI
```powershell
python qwen_tts.py --name "Carlos" --api-key "sk-..."
# or with env var set:
python qwen_tts.py --name "Carlos"
```

## API Integration Details

- **Endpoint:** `https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`
- **Model:** `qwen3-tts-vc-2026-01-22`
- **Voice ID:** `qwen-tts-vc-roberto_pt-voice-20260429004312101-aab6`
- **Auth:** `Authorization: Bearer <api-key>` (server-side env `DASHSCOPE_API_KEY`)
- **Response audio path:** `data.output.audio.url`
- Text selection: random line from `phrases.txt`, formatted with `{name}`

## Environment Config

`qwen_tts.py` reads `.env` automatically (if present):

- `DASHSCOPE_API_KEY`
- `API_ENDPOINT`
- `MODEL`
- `VOICE`
- `LANGUAGE`

Phrase templates are edited in `phrases.txt` (and `backend/phrases.txt` in the backend handoff bundle).
