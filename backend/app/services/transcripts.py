from __future__ import annotations

import json
import re
from dataclasses import dataclass


class TranscriptParseError(ValueError):
    """Raised when an uploaded transcript cannot be safely interpreted."""


@dataclass(frozen=True)
class ParsedSegment:
    speaker: str | None
    start_time_ms: int
    end_time_ms: int
    text: str


_VTT_TIME = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})")
_TXT_LINE = re.compile(
    r"^\s*\[(?P<start>[^\]-]+)(?:\s*(?:-|–|—)\s*(?P<end>[^\]]+))?\]\s*(?:(?P<speaker>[^:]{1,100}):\s*)?(?P<text>.+?)\s*$"
)


def parse_transcript(filename: str, content: bytes) -> list[ParsedSegment]:
    if len(content) > 5 * 1024 * 1024:
        raise TranscriptParseError("Transcript files must be 5 MB or smaller")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TranscriptParseError("Transcript files must be UTF-8 encoded") from exc
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix == "txt":
        segments = _parse_txt(text)
    elif suffix == "vtt":
        segments = _parse_vtt(text)
    elif suffix == "json":
        segments = _parse_json(text)
    else:
        raise TranscriptParseError("Supported transcript formats are .txt, .vtt, and .json")
    if not segments:
        raise TranscriptParseError("The transcript did not contain any usable segments")
    return sorted(segments, key=lambda segment: (segment.start_time_ms, segment.end_time_ms))


def _milliseconds(value: str | int | float) -> int:
    if isinstance(value, (int, float)):
        if value < 0:
            raise TranscriptParseError("Timestamps cannot be negative")
        return int(value)
    candidate = value.strip()
    if candidate.isdigit():
        return int(candidate)
    match = _VTT_TIME.fullmatch(candidate)
    if not match:
        raise TranscriptParseError(f"Invalid timestamp: {value}")
    hours, minutes, seconds, milliseconds = match.groups()
    return ((int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)) * 1000) + int(milliseconds)


def _parse_txt(text: str) -> list[ParsedSegment]:
    """Accept `[00:00:01.000 - 00:00:05.000] Speaker: text` per line."""
    segments: list[ParsedSegment] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        match = _TXT_LINE.match(line)
        if not match:
            raise TranscriptParseError(
                f"Invalid TXT line {line_number}. Use [start - end] Speaker: text."
            )
        start = _milliseconds(match.group("start"))
        end = _milliseconds(match.group("end")) if match.group("end") else start + 5_000
        if end < start:
            raise TranscriptParseError(f"TXT line {line_number} ends before it starts")
        segments.append(ParsedSegment(match.group("speaker"), start, end, match.group("text")))
    return segments


def _parse_vtt(text: str) -> list[ParsedSegment]:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    if not lines or not lines[0].lstrip("\ufeff").startswith("WEBVTT"):
        raise TranscriptParseError("A VTT transcript must start with WEBVTT")
    segments: list[ParsedSegment] = []
    cursor = 1
    while cursor < len(lines):
        if not lines[cursor].strip():
            cursor += 1
            continue
        if "-->" not in lines[cursor]:
            cursor += 1  # optional cue identifier
        if cursor >= len(lines) or "-->" not in lines[cursor]:
            raise TranscriptParseError("Invalid VTT cue timing")
        start_raw, end_raw = [part.strip().split(" ")[0] for part in lines[cursor].split("-->", 1)]
        start, end = _milliseconds(start_raw), _milliseconds(end_raw)
        if end < start:
            raise TranscriptParseError("A VTT cue ends before it starts")
        cursor += 1
        cue: list[str] = []
        while cursor < len(lines) and lines[cursor].strip():
            cue.append(lines[cursor].strip())
            cursor += 1
        value = " ".join(cue).strip()
        if not value:
            raise TranscriptParseError("A VTT cue cannot be empty")
        speaker = None
        speaker_match = re.match(r"(?:<v\s+([^>]+)>|([^:]{1,100}):)\s*(.*)", value, re.I)
        if speaker_match:
            speaker = (speaker_match.group(1) or speaker_match.group(2)).strip()
            value = speaker_match.group(3).strip()
        value = re.sub(r"<[^>]+>", "", value).strip()
        if value:
            segments.append(ParsedSegment(speaker, start, end, value))
    return segments


def _parse_json(text: str) -> list[ParsedSegment]:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TranscriptParseError("Invalid JSON transcript") from exc
    entries = raw.get("segments") if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        raise TranscriptParseError("JSON must be a segment array or an object with a segments array")
    segments: list[ParsedSegment] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise TranscriptParseError(f"JSON segment {index} must be an object")
        try:
            start = _milliseconds(entry.get("start_time_ms", entry.get("start_time")))
            end = _milliseconds(entry.get("end_time_ms", entry.get("end_time")))
        except (TypeError, AttributeError) as exc:
            raise TranscriptParseError(f"JSON segment {index} has invalid timestamps") from exc
        value = entry.get("text")
        if not isinstance(value, str) or not value.strip() or end < start:
            raise TranscriptParseError(f"JSON segment {index} has invalid text or time range")
        speaker = entry.get("speaker")
        if speaker is not None and (not isinstance(speaker, str) or len(speaker) > 255):
            raise TranscriptParseError(f"JSON segment {index} has an invalid speaker")
        segments.append(ParsedSegment(speaker.strip() if speaker else None, start, end, value.strip()))
    return segments
