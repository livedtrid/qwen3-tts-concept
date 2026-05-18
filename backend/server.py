"""
Backend-only API server for Qwen3-TTS.

Usage (PowerShell):
    Copy-Item .env.example .env
    pip install -r requirements.txt
    python server.py
"""

import os
import random
import tempfile
import wave
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from qwen_tts import (
    OUTPUT_FILE,
    generate_audio,
    generate_audio_from_text,
    get_phrase_count,
    list_phrase_templates,
    render_phrase,
)

BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_FRONTEND_DIR = BACKEND_DIR.parent
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", str(DEFAULT_FRONTEND_DIR))).resolve()
AUDIO_DIR = BACKEND_DIR / "audio"


def _env_flag_enabled(name: str, default: bool = False) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


CHEAP_MODE = _env_flag_enabled("CHEAP_MODE", default=False)


def _list_cheap_mode_audio_files() -> list[Path]:
    return sorted(path for path in AUDIO_DIR.glob("*.wav") if path.is_file())


def _pick_random_cheap_mode_audio() -> Path:
    candidates = _list_cheap_mode_audio_files()
    if not candidates:
        raise ValueError(
            f"CHEAP_MODE is enabled but no .wav files were found in {AUDIO_DIR}."
        )

    return random.choice(candidates)


def _wav_signature(path: Path) -> tuple[int, int, int, str]:
    try:
        with wave.open(str(path), "rb") as handle:
            params = handle.getparams()
            return (
                params.nchannels,
                params.sampwidth,
                params.framerate,
                params.comptype,
            )
    except wave.Error as exc:
        raise ValueError(f"Invalid WAV file at {path}: {exc}")


def _convert_pcm_frames(
    frames: bytes,
    source_signature: tuple[int, int, int, str],
    target_signature: tuple[int, int, int, str],
) -> bytes:
    source_channels, source_width, source_rate, source_comp = source_signature
    target_channels, target_width, target_rate, target_comp = target_signature

    if source_comp != "NONE" or target_comp != "NONE":
        raise ValueError("Only uncompressed PCM WAV files are supported in CHEAP_MODE.")

    if source_channels not in {1, 2} or target_channels not in {1, 2}:
        raise ValueError("CHEAP_MODE currently supports mono/stereo WAV files only.")

    samples = _decode_pcm_frames(
        frames=frames,
        channels=source_channels,
        sample_width=source_width,
    )

    if source_channels != target_channels:
        samples = _convert_channels(samples=samples, target_channels=target_channels)

    if source_rate != target_rate:
        samples = _resample_samples(
            samples=samples,
            source_rate=source_rate,
            target_rate=target_rate,
        )

    if source_width != target_width:
        samples = _convert_sample_width(
            samples=samples,
            source_width=source_width,
            target_width=target_width,
        )

    return _encode_pcm_frames(samples=samples, sample_width=target_width)


def _sample_bounds(sample_width: int) -> tuple[int, int]:
    bits = sample_width * 8
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    return minimum, maximum


def _decode_sample(raw: bytes, sample_width: int) -> int:
    if sample_width == 1:
        # WAV 8-bit PCM is unsigned.
        return raw[0] - 128

    if sample_width == 2:
        return int.from_bytes(raw, byteorder="little", signed=True)

    if sample_width == 3:
        value = raw[0] | (raw[1] << 8) | (raw[2] << 16)
        if value & 0x800000:
            value -= 1 << 24
        return value

    if sample_width == 4:
        return int.from_bytes(raw, byteorder="little", signed=True)

    raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")


def _encode_sample(value: int, sample_width: int) -> bytes:
    minimum, maximum = _sample_bounds(sample_width)
    value = max(minimum, min(maximum, int(value)))

    if sample_width == 1:
        return bytes([value + 128])

    if sample_width == 2:
        return value.to_bytes(2, byteorder="little", signed=True)

    if sample_width == 3:
        if value < 0:
            value += 1 << 24
        return bytes((value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF))

    if sample_width == 4:
        return value.to_bytes(4, byteorder="little", signed=True)

    raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")


def _decode_pcm_frames(frames: bytes, channels: int, sample_width: int) -> list[tuple[int, ...]]:
    frame_size = channels * sample_width
    if frame_size <= 0:
        raise ValueError("Invalid WAV frame size.")

    if len(frames) % frame_size != 0:
        raise ValueError("Invalid WAV frame payload length.")

    decoded: list[tuple[int, ...]] = []
    for offset in range(0, len(frames), frame_size):
        frame_chunk = frames[offset : offset + frame_size]
        frame_values = []
        for channel in range(channels):
            start = channel * sample_width
            end = start + sample_width
            frame_values.append(_decode_sample(frame_chunk[start:end], sample_width))
        decoded.append(tuple(frame_values))

    return decoded


def _convert_channels(
    samples: list[tuple[int, ...]],
    target_channels: int,
) -> list[tuple[int, ...]]:
    if not samples:
        return []

    source_channels = len(samples[0])
    if source_channels == target_channels:
        return samples

    if source_channels == 2 and target_channels == 1:
        return [((left + right) // 2,) for left, right in samples]

    if source_channels == 1 and target_channels == 2:
        return [(mono, mono) for (mono,) in samples]

    raise ValueError("Unsupported channel conversion in CHEAP_MODE.")


def _convert_sample_width(
    samples: list[tuple[int, ...]],
    source_width: int,
    target_width: int,
) -> list[tuple[int, ...]]:
    if source_width == target_width or not samples:
        return samples

    source_min, source_max = _sample_bounds(source_width)
    target_min, target_max = _sample_bounds(target_width)

    # Normalize to [-1, 1], then map to target bit-depth range.
    source_scale = max(abs(source_min), abs(source_max))
    target_scale = max(abs(target_min), abs(target_max))

    converted: list[tuple[int, ...]] = []
    for frame in samples:
        converted_frame = []
        for value in frame:
            normalized = value / source_scale if source_scale else 0.0
            mapped = round(normalized * target_scale)
            converted_frame.append(mapped)
        converted.append(tuple(converted_frame))

    return converted


def _resample_samples(
    samples: list[tuple[int, ...]],
    source_rate: int,
    target_rate: int,
) -> list[tuple[int, ...]]:
    if not samples or source_rate == target_rate:
        return samples

    target_length = max(1, round(len(samples) * target_rate / source_rate))
    max_index = len(samples) - 1

    resampled: list[tuple[int, ...]] = []
    for index in range(target_length):
        position = index * source_rate / target_rate
        left_index = int(position)
        right_index = min(left_index + 1, max_index)
        ratio = position - left_index

        left_frame = samples[left_index]
        right_frame = samples[right_index]
        interpolated = []
        for channel in range(len(left_frame)):
            left_value = left_frame[channel]
            right_value = right_frame[channel]
            value = round(left_value + (right_value - left_value) * ratio)
            interpolated.append(value)
        resampled.append(tuple(interpolated))

    return resampled


def _encode_pcm_frames(samples: list[tuple[int, ...]], sample_width: int) -> bytes:
    encoded = bytearray()
    for frame in samples:
        for value in frame:
            encoded.extend(_encode_sample(value=value, sample_width=sample_width))
    return bytes(encoded)


def _concatenate_wav_files(first_path: Path, second_path: Path, output_path: Path) -> None:
    first_signature = _wav_signature(first_path)
    second_signature = _wav_signature(second_path)

    with wave.open(str(first_path), "rb") as first_file:
        first_params = first_file.getparams()
        first_frames = first_file.readframes(first_file.getnframes())

    with wave.open(str(second_path), "rb") as second_file:
        second_frames = second_file.readframes(second_file.getnframes())

    if first_signature != second_signature:
        second_frames = _convert_pcm_frames(
            frames=second_frames,
            source_signature=second_signature,
            target_signature=first_signature,
        )

    with wave.open(str(output_path), "wb") as merged_file:
        merged_file.setparams(first_params)
        merged_file.writeframes(first_frames)
        merged_file.writeframes(second_frames)

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

    if phrase_index is not None and not CHEAP_MODE:
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

    temp_paths: list[Path] = []
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as response_tmp:
            response_path = Path(response_tmp.name)
        temp_paths.append(response_path)

        if CHEAP_MODE:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tts_tmp:
                generated_path = Path(tts_tmp.name)
            temp_paths.append(generated_path)

            generate_audio_from_text(
                text=name,
                api_key=api_key,
                output_path=str(generated_path),
            )

            suffix_audio_path = _pick_random_cheap_mode_audio()
            _concatenate_wav_files(
                first_path=generated_path,
                second_path=suffix_audio_path,
                output_path=response_path,
            )
        else:
            generate_audio(
                name=name,
                api_key=api_key,
                output_path=str(response_path),
                phrase_index=phrase_index,
            )

        response = send_file(
            str(response_path),
            mimetype="audio/wav",
            as_attachment=True,
            download_name=OUTPUT_FILE,
        )

        @response.call_on_close
        def _cleanup_temp_file() -> None:
            for temp_path in temp_paths:
                if temp_path.exists():
                    temp_path.unlink()

        return response
    except ValueError as exc:
        for temp_path in temp_paths:
            if temp_path.exists():
                temp_path.unlink()
        return jsonify({"error": str(exc)}), 500
    except RuntimeError as exc:
        for temp_path in temp_paths:
            if temp_path.exists():
                temp_path.unlink()
        return jsonify({"error": str(exc)}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[server] Serving frontend from: {FRONTEND_DIR}")
    print(f"[server] CHEAP_MODE={'on' if CHEAP_MODE else 'off'}")
    app.run(host="0.0.0.0", port=port, debug=True)

