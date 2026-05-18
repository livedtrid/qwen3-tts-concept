"""
Qwen3-TTS Voice Cloning - Backend utility
Alibaba Cloud DashScope API
Docs: https://www.alibabacloud.com/help/en/model-studio/qwen-tts-api
"""

import argparse
import json
import os
import random
import sys
import urllib.error
import urllib.request


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)


def _load_dotenv(env_path: str | None = None) -> None:
    """Load KEY=VALUE pairs from local .env files into os.environ.

    Preference order:
    1. Explicit ``env_path`` when provided
    2. ``backend/.env``
    3. Legacy repo-root ``.env`` for backwards compatibility
    """
    candidate_paths = [env_path] if env_path else [
        os.path.join(BASE_DIR, ".env"),
        os.path.join(PROJECT_ROOT, ".env"),
    ]

    for candidate_path in candidate_paths:
        if not candidate_path or not os.path.exists(candidate_path):
            continue

        with open(candidate_path, "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)


_load_dotenv()

API_ENDPOINT = os.environ.get(
    "API_ENDPOINT",
    "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
)
MODEL = os.environ.get("MODEL", "qwen3-tts-vc-2026-01-22")
VOICE = os.environ.get("VOICE", "qwen-tts-vc-roberto_pt-voice-20260429004312101-aab6")
LANGUAGE = os.environ.get("LANGUAGE", "Portuguese")
OUTPUT_FILE = "qwen-tts-synthesis.wav"
PHRASES_FILE = os.path.join(BASE_DIR, "phrases.txt")

DEFAULT_PHRASES = [
    "{name}! Faltavas tu. A nossa seleção precisa de ti para os momentos decisivos. Vive a seleção de corpo e alma.",
    "{name}! Precisamos da tua energia e juntamente com a Sagres vamos viver cada momento de corpo e alma.",
    "{name}! Fazes parte do grupo. A seleção conta contigo para fazeres a diferença e viveres cada emoção de corpo e alma.",
]


def _load_phrases_from_file(file_path: str) -> list[str]:
    """Load phrase templates from a text file (one phrase per line)."""
    if not os.path.exists(file_path):
        return DEFAULT_PHRASES

    with open(file_path, "r", encoding="utf-8") as phrases_file:
        phrases = [
            line.strip()
            for line in phrases_file
            if line.strip() and not line.strip().startswith("#")
        ]

    return phrases or DEFAULT_PHRASES


PHRASES = _load_phrases_from_file(PHRASES_FILE)


def list_phrase_templates() -> list[str]:
    """Return all available phrase templates."""
    return PHRASES.copy()


def get_phrase_count() -> int:
    """Return the number of available phrase templates."""
    return len(PHRASES)


def _resolve_phrase_template(phrase_index: int | None = None) -> str:
    """Return a specific phrase template or a random one when omitted.

    ``phrase_index`` is 1-based for friendlier API/CLI usage.
    """
    if phrase_index is None:
        return random.choice(PHRASES)

    if phrase_index < 1 or phrase_index > len(PHRASES):
        raise ValueError(
            f"phrase_index must be between 1 and {len(PHRASES)} (received {phrase_index})."
        )

    return PHRASES[phrase_index - 1]


def render_phrase(name: str, phrase_index: int | None = None) -> str:
    """Render the selected phrase with the provided recipient name."""
    return _resolve_phrase_template(phrase_index=phrase_index).format(name=name)


def _call_dashscope_tts(text: str, api_key: str) -> str:
    """Call DashScope TTS API and return the generated audio URL."""
    payload = {
        "model": MODEL,
        "input": {
            "text": text,
            "voice": VOICE,
            "language_type": LANGUAGE,
        },
    }
    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        API_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.reason
        try:
            error_json = json.loads(exc.read().decode("utf-8"))
            detail = error_json.get("message") or error_json.get("code") or detail
        except Exception:
            pass
        raise RuntimeError(f"API error {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}")

    try:
        data = json.loads(response_data)
    except json.JSONDecodeError:
        raise RuntimeError("Invalid JSON response from DashScope API.")

    audio_url = ((data.get("output") or {}).get("audio") or {}).get("url")
    if not audio_url:
        raise RuntimeError("No audio URL found in API response.")
    return audio_url


def generate_audio(
    name: str,
    api_key: str,
    output_path: str = OUTPUT_FILE,
    phrase_index: int | None = None,
) -> str:
    """Synthesize a random Portuguese phrase and save it to *output_path*."""
    text = render_phrase(name=name, phrase_index=phrase_index)

    audio_url = _call_dashscope_tts(text=text, api_key=api_key)
    urllib.request.urlretrieve(audio_url, output_path)

    return output_path


def generate_audio_from_text(text: str, api_key: str, output_path: str = OUTPUT_FILE) -> str:
    """Synthesize an audio clip from raw text and save it to *output_path*."""
    audio_url = _call_dashscope_tts(text=text, api_key=api_key)
    urllib.request.urlretrieve(audio_url, output_path)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a personalized Portuguese TTS clip via Qwen3-TTS."
    )
    parser.add_argument(
        "--name",
        "-n",
        required=True,
        help="Recipient name embedded in the spoken phrase (for example 'Carlos').",
    )
    parser.add_argument(
        "--api-key",
        "-k",
        default=os.environ.get("DASHSCOPE_API_KEY"),
        help="DashScope API key. Defaults to DASHSCOPE_API_KEY env var.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=OUTPUT_FILE,
        help=f"Output WAV file path (default: {OUTPUT_FILE}).",
    )
    parser.add_argument(
        "--phrase-index",
        type=int,
        help=(
            "Optional 1-based phrase index to synthesize. "
            f"Available range: 1-{get_phrase_count()}."
        ),
    )
    args = parser.parse_args()

    if not args.api_key:
        parser.error(
            "API key is required. Pass --api-key or set the DASHSCOPE_API_KEY "
            "environment variable."
        )

    try:
        generate_audio(
            name=args.name,
            api_key=args.api_key,
            output_path=args.output,
            phrase_index=args.phrase_index,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"[qwen-tts] Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


