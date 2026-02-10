import json
import re
from pathlib import Path


def parse_journal_json(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_entries = data.get("entries", [])
    parsed = []

    for raw in raw_entries:
        location = raw.get("location") or {}
        weather = raw.get("weather") or {}
        text = raw.get("text", "")

        entry = {
            "uuid": raw["uuid"],
            "creation_date": raw.get("creationDate", ""),
            "modified_date": raw.get("modifiedDate"),
            "timezone": raw.get("timeZone"),
            "text": text,
            "snippet": make_snippet(text) if text else None,
            "starred": 1 if raw.get("starred") else 0,
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "place_name": location.get("placeName"),
            "locality": location.get("localityName"),
            "admin_area": location.get("administrativeArea"),
            "country": location.get("country"),
            "weather_description": weather.get("conditionsDescription"),
            "weather_temp_c": weather.get("temperatureCelsius"),
            "duration": raw.get("duration"),
            "word_count": len(text.split()) if text else 0,
            "tags": raw.get("tags", []),
            "photos": [
                {
                    "identifier": p["identifier"],
                    "md5": p.get("md5"),
                    "file_type": p.get("type"),
                    "width": p.get("width"),
                    "height": p.get("height"),
                }
                for p in raw.get("photos", [])
            ],
        }
        parsed.append(entry)

    return parsed


def strip_markdown(text: str) -> str:
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\(.*?\)", r"\1", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"(\*{1,3}|_{1,3})(.*?)\1", r"\2", text)
    text = re.sub(r"~~(.*?)~~", r"\1", text)
    text = re.sub(r"`{1,3}.*?`{1,3}", "", text, flags=re.DOTALL)
    text = re.sub(r"^[>\-\*\+]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{2,}", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_snippet(text: str, max_len: int = 200) -> str:
    stripped = strip_markdown(text)
    if len(stripped) <= max_len:
        return stripped
    truncated = stripped[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > max_len // 2:
        truncated = truncated[:last_space]
    return truncated + "..."
