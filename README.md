# qwen3-tts-concept

Proof-of-concept for the [Alibaba Cloud Qwen3-TTS](https://www.alibabacloud.com/help/en/model-studio/qwen-tts-api) voice-cloning API. Generates personalized Portuguese audio clips themed around the 2026 FIFA World Cup.

## Quick Start

### Web app (backend server + frontend shell)

The backend code now lives only in `backend/`. The root files are the frontend shell (`index.html`, `script.js`, `styles.css`).

For local development, `backend/server.py` can also serve the root frontend directly, so you still open a single local URL in the browser.

Copy `backend/.env.example` to `backend/.env` and set values (`DASHSCOPE_API_KEY`, `API_ENDPOINT`, `MODEL`, `VOICE`, `LANGUAGE`).

For backwards compatibility, the backend also falls back to a legacy repo-root `.env` if you already have one, but `backend/.env` is now the preferred location.

Edit phrase templates in `backend/phrases.txt` (one phrase per line; keep `{name}` placeholder).

```powershell
Copy-Item backend/.env.example backend/.env
pip install -r backend/requirements.txt
python backend/server.py
```

Then open <http://localhost:5000>.

If you prefer running the frontend from another local origin (for example a static server or `file:///`), `script.js` now falls back to `http://localhost:5000` automatically during local development.

### Python CLI (no browser needed)

```powershell
python backend/qwen_tts.py --name "Carlos" --api-key "sk-..."
# or with env var set:
python backend/qwen_tts.py --name "Carlos"
```

Saves output as `qwen-tts-synthesis.wav`. Override with `--output <path>`.

## Project Structure

| File | Description |
|---|---|
| `index.html` | Frontend UI |
| `script.js` | Frontend logic (posts to backend API, plays blob response) |
| `styles.css` | Glassmorphism design system |
| `backend/server.py` | Flask backend + optional frontend static serving |
| `backend/qwen_tts.py` | Core TTS logic + standalone CLI |
| `backend/phrases.txt` | Editable phrase templates (one per line, `{name}` placeholder) |
| `backend/requirements.txt` | Python dependencies (`flask`, `flask-cors`) |
| `backend/smoke_test.ps1` | PowerShell smoke test, including all-phrases mode |

## Backend Handoff Bundle

The backend source of truth is in `backend/`:

- `backend/server.py`
- `backend/qwen_tts.py`
- `backend/phrases.txt`
- `backend/.env.example`
- `backend/API_CONTRACT.md`
- `backend/README.md`

### Smoke test all phrases

```powershell
pwsh ./backend/smoke_test.ps1 -AllPhrases -Name "Carlos"
```

That generates one WAV per phrase (for example `sample-phrase-1.wav`, `sample-phrase-2.wav`, `sample-phrase-3.wav`).

