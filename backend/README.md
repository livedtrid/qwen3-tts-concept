# Backend Handoff Bundle

This folder is a backend-only package for the Qwen3-TTS PoC.

## Files

- `server.py` - Flask API (`POST /api/generate`, `GET /health`, `GET /api/phrases`) + optional frontend static serving
- `qwen_tts.py` - DashScope TTS call + WAV download logic
- `phrases.txt` - editable phrase templates (one phrase per line)
- `requirements.txt` - backend dependencies
- `.env.example` - environment variable template
- `API_CONTRACT.md` - request/response contract for integration

## Setup

1. Copy env template:
   - `Copy-Item .env.example .env`
2. Fill `.env` with your real `DASHSCOPE_API_KEY`.
   - Optional tuning keys: `API_ENDPOINT`, `MODEL`, `VOICE`, `LANGUAGE`
3. Edit `phrases.txt` (one phrase per line, use `{name}` placeholder).
4. Install deps and run server.

```powershell
pip install -r requirements.txt
python server.py
```

Server defaults to `http://localhost:5000`.

If this backend sits inside the main repo, it will automatically serve the frontend files from the parent folder, so you can open `http://localhost:5000` and test the UI locally without duplicating backend files at the repo root.

## Smoke Test (PowerShell)

```powershell
./smoke_test.ps1 -Name "Carlos"
./smoke_test.ps1 -PhraseIndex 2 -OutFile "phrase-2.wav"
./smoke_test.ps1 -AllPhrases -Name "Carlos"
```
