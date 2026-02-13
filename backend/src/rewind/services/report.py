import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import anthropic

from rewind.config import settings
from rewind.db import get_db

logger = logging.getLogger(__name__)

# Module-level dict for report statuses (same pattern as import pipeline)
_report_statuses: dict[str, dict] = {}


def get_report_status(report_id: str) -> dict | None:
    return _report_statuses.get(report_id)


def _do_generate(
    report_id: str,
    person_tag_id: int,
    date_from: str | None,
    date_to: str | None,
) -> None:
    status = _report_statuses[report_id]

    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    conn = get_db()
    try:
        # Get person tag
        tag_row = conn.execute(
            "SELECT * FROM tags WHERE id = ?", (person_tag_id,)
        ).fetchone()
        if not tag_row:
            raise ValueError(f"Tag {person_tag_id} not found")
        person_name = tag_row["name"]
        status["person_name"] = person_name
        status["message"] = f"Finding entries about {person_name}..."
        status["progress"] = 0.1

        # Get entries for this person
        where_clauses = [
            "e.uuid IN (SELECT entry_uuid FROM entry_tags WHERE tag_id = ?)"
        ]
        params: list = [person_tag_id]

        if date_from:
            where_clauses.append("e.creation_date >= ?")
            params.append(date_from)
        if date_to:
            where_clauses.append("e.creation_date <= ?")
            params.append(date_to)

        where_sql = " AND ".join(where_clauses)

        entry_rows = conn.execute(
            f"""SELECT e.* FROM entries e
                WHERE {where_sql}
                ORDER BY e.creation_date ASC""",
            params,
        ).fetchall()

        if not entry_rows:
            raise ValueError(f"No entries found for {person_name}")

        status["message"] = f"Found {len(entry_rows)} entries about {person_name}"
        status["progress"] = 0.2

        # Get tags for these entries
        uuids = [r["uuid"] for r in entry_rows]
        placeholders = ",".join("?" * len(uuids))
        tag_rows = conn.execute(
            f"""SELECT et.entry_uuid, t.name, t.tag_type
                FROM entry_tags et JOIN tags t ON t.id = et.tag_id
                WHERE et.entry_uuid IN ({placeholders})""",
            uuids,
        ).fetchall()

        tags_by_uuid: dict[str, list[dict]] = {}
        for r in tag_rows:
            tags_by_uuid.setdefault(r["entry_uuid"], []).append(
                {"name": r["name"], "type": r["tag_type"] or "topic"}
            )

        # Get photos for these entries
        photo_rows = conn.execute(
            f"""SELECT entry_uuid, id, identifier, has_thumbnail
                FROM photos WHERE entry_uuid IN ({placeholders})""",
            uuids,
        ).fetchall()

        photos_by_uuid: dict[str, list[dict]] = {}
        for r in photo_rows:
            photos_by_uuid.setdefault(r["entry_uuid"], []).append({
                "id": r["id"],
                "identifier": r["identifier"],
                "has_thumbnail": bool(r["has_thumbnail"]),
            })

        status["progress"] = 0.3
        status["message"] = "Preparing entries for Claude..."

        # Build entry excerpts for Claude
        entry_excerpts = []
        places: set[str] = set()
        co_people: set[str] = set()

        for r in entry_rows:
            entry_tags = tags_by_uuid.get(r["uuid"], [])
            excerpt = {
                "date": r["creation_date"][:10],
                "text": (r["text"] or "")[:500],
                "place": r["place_name"],
                "tags": [t["name"] for t in entry_tags],
                "starred": bool(r["starred"]),
            }
            entry_excerpts.append(excerpt)

            if r["place_name"]:
                places.add(r["place_name"])
            for t in entry_tags:
                if t["type"] == "person" and t["name"] != person_name:
                    co_people.add(t["name"])

        # Compute stats
        date_range_start = entry_rows[0]["creation_date"][:10]
        date_range_end = entry_rows[-1]["creation_date"][:10]
        total_entries = len(entry_rows)
        starred_count = sum(1 for r in entry_rows if r["starred"])
        total_photos = sum(
            len(photos_by_uuid.get(r["uuid"], [])) for r in entry_rows
        )
        unique_places = len(places)

        status["progress"] = 0.4
        status["message"] = "Generating narrative with Claude..."

        # Call Claude for the narrative
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Limit excerpts to avoid token limits
        selected_excerpts = entry_excerpts
        if len(selected_excerpts) > 100:
            step = max(1, (len(selected_excerpts) - 40) // 60)
            middle = selected_excerpts[20:-20:step][:60]
            selected_excerpts = (
                selected_excerpts[:20] + middle + selected_excerpts[-20:]
            )

        system_prompt = (
            f"You are writing a personal narrative summary about someone named "
            f"{person_name} based on journal entries written by someone who knows them.\n\n"
            f"Write in a warm, personal tone — this is for someone who cares deeply about "
            f"{person_name} and wants to celebrate their relationship.\n\n"
            f"Return a JSON object with exactly these keys:\n"
            f'- "summary": A 2-3 sentence overview of the relationship and its themes (string)\n'
            f'- "themes": An array of 3-5 theme objects, each with "title" (string) and '
            f'"description" (1-2 sentences, string)\n'
            f'- "highlights": An array of 5-8 highlight objects, each with "date" '
            f'(YYYY-MM-DD string), "text" (1-2 sentence description of what happened, string)\n'
            f'- "places_narrative": A 2-3 sentence summary of the places associated with '
            f"{person_name} (string)\n"
            f'- "closing": A warm 1-2 sentence closing reflection (string)\n\n'
            f"Return ONLY valid JSON. No markdown fences, no explanation."
        )

        excerpts_json = json.dumps(selected_excerpts, indent=None)

        user_prompt = (
            f"Here are {total_entries} journal entries mentioning {person_name} "
            f"from {date_range_start} to {date_range_end}.\n\n"
            f"Stats: {total_entries} entries, {starred_count} starred, "
            f"{total_photos} photos, {unique_places} unique places.\n"
            f"Places: {', '.join(sorted(places)[:20])}\n"
            f"Other people mentioned alongside: {', '.join(sorted(co_people)[:15])}\n\n"
            f"Entry excerpts (representative sample):\n{excerpts_json}\n\n"
            f"Generate a personal narrative summary about {person_name}."
        )

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        narrative_text = response.content[0].text.strip()

        # Handle potential markdown fences
        if narrative_text.startswith("```"):
            lines = narrative_text.split("\n")
            narrative_text = "\n".join(lines[1:-1])

        narrative = json.loads(narrative_text)

        status["progress"] = 0.8
        status["message"] = "Building HTML report..."

        # Build HTML
        html = _build_report_html(
            person_name=person_name,
            narrative=narrative,
            stats={
                "total_entries": total_entries,
                "starred_count": starred_count,
                "total_photos": total_photos,
                "unique_places": unique_places,
                "date_range_start": date_range_start,
                "date_range_end": date_range_end,
                "co_people": sorted(co_people),
            },
            places=sorted(places),
            entry_rows=entry_rows,
            photos_by_uuid=photos_by_uuid,
        )

        # Save HTML
        report_path = settings.REPORTS_DIR / f"{report_id}.html"
        report_path.write_text(html, encoding="utf-8")

        status["progress"] = 1.0
        status["status"] = "done"
        status["message"] = "Report ready"

    finally:
        conn.close()


def _build_report_html(
    person_name: str,
    narrative: dict,
    stats: dict,
    places: list[str],
    entry_rows: list,
    photos_by_uuid: dict[str, list[dict]],
) -> str:
    """Build a standalone HTML report."""

    # Collect photo IDs for the gallery (up to 20)
    gallery_photos = []
    for r in entry_rows:
        for p in photos_by_uuid.get(r["uuid"], []):
            if p["has_thumbnail"]:
                gallery_photos.append(p)
                if len(gallery_photos) >= 20:
                    break
        if len(gallery_photos) >= 20:
            break

    # Build themes HTML
    themes_html = ""
    for theme in narrative.get("themes", []):
        themes_html += f'''
        <div class="theme-card">
            <h3>{_escape_html(theme.get("title", ""))}</h3>
            <p>{_escape_html(theme.get("description", ""))}</p>
        </div>'''

    # Build highlights HTML
    highlights_html = ""
    for h in narrative.get("highlights", []):
        date_str = h.get("date", "")
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = d.strftime("%B %d, %Y")
        except ValueError:
            formatted_date = date_str
        highlights_html += f'''
        <div class="highlight">
            <span class="highlight-date">{_escape_html(formatted_date)}</span>
            <p>{_escape_html(h.get("text", ""))}</p>
        </div>'''

    # Build photo gallery HTML
    gallery_html = ""
    if gallery_photos:
        gallery_html = '<div class="photo-gallery">'
        for p in gallery_photos:
            gallery_html += f'''
            <div class="gallery-photo">
                <img src="/api/photos/{p["id"]}/thumbnail" alt="" loading="lazy" />
            </div>'''
        gallery_html += "</div>"

    # Build places list
    places_html = ""
    if places:
        places_items = "".join(
            f"<span class='place-chip'>{_escape_html(p)}</span>"
            for p in places[:15]
        )
        places_html = f'<div class="places-list">{places_items}</div>'

    # Co-people mentioned
    co_people_html = ""
    if stats.get("co_people"):
        co_items = "".join(
            f"<span class='person-chip'>{_escape_html(p)}</span>"
            for p in stats["co_people"][:10]
        )
        co_people_html = f'''
        <div class="section">
            <h2>Also Mentioned With</h2>
            <div class="people-list">{co_items}</div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_escape_html(person_name)} — Rewind Report</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@400;600;700&display=swap');

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
        font-family: 'Inter', -apple-system, sans-serif;
        background: #faf8f5;
        color: #2d2a26;
        line-height: 1.6;
        -webkit-font-smoothing: antialiased;
    }}

    .report {{
        max-width: 720px;
        margin: 0 auto;
        padding: 60px 24px 80px;
    }}

    .header {{
        text-align: center;
        margin-bottom: 48px;
        padding-bottom: 32px;
        border-bottom: 1px solid #e8e4df;
    }}

    .header h1 {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 42px;
        font-weight: 700;
        color: #c06a45;
        margin-bottom: 8px;
    }}

    .header .date-range {{
        font-size: 15px;
        color: #9b9590;
        font-weight: 400;
    }}

    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 48px;
    }}

    .stat-card {{
        text-align: center;
        padding: 20px 12px;
        background: white;
        border-radius: 10px;
        border: 1px solid #e8e4df;
    }}

    .stat-number {{
        font-size: 28px;
        font-weight: 700;
        color: #c06a45;
        display: block;
    }}

    .stat-label {{
        font-size: 12px;
        color: #9b9590;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }}

    .section {{
        margin-bottom: 40px;
    }}

    .section h2 {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 16px;
        color: #2d2a26;
    }}

    .section p {{
        color: #6b6560;
        font-size: 15px;
        line-height: 1.7;
    }}

    .themes {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-top: 16px;
    }}

    .theme-card {{
        padding: 20px;
        background: white;
        border-radius: 10px;
        border: 1px solid #e8e4df;
    }}

    .theme-card h3 {{
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 8px;
        color: #c06a45;
    }}

    .theme-card p {{
        font-size: 14px;
        color: #6b6560;
        line-height: 1.5;
    }}

    .highlight {{
        padding: 16px 0;
        border-bottom: 1px solid #e8e4df;
    }}

    .highlight:last-child {{
        border-bottom: none;
    }}

    .highlight-date {{
        font-size: 12px;
        font-weight: 600;
        color: #c06a45;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .highlight p {{
        margin-top: 4px;
        font-size: 15px;
        color: #6b6560;
    }}

    .photo-gallery {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 8px;
        margin-top: 16px;
    }}

    .gallery-photo {{
        aspect-ratio: 1;
        border-radius: 8px;
        overflow: hidden;
    }}

    .gallery-photo img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}

    .place-chip {{
        display: inline-block;
        padding: 4px 12px;
        margin: 4px;
        background: #e8f5ee;
        color: #4a9e7a;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
    }}

    .person-chip {{
        display: inline-block;
        padding: 4px 12px;
        margin: 4px;
        background: #ede8f5;
        color: #7c6bc4;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
    }}

    .closing {{
        text-align: center;
        padding: 40px 20px;
        margin-top: 48px;
        border-top: 1px solid #e8e4df;
    }}

    .closing p {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 18px;
        font-style: italic;
        color: #6b6560;
        line-height: 1.6;
    }}

    .footer {{
        text-align: center;
        margin-top: 48px;
        padding-top: 24px;
        border-top: 1px solid #e8e4df;
    }}

    .footer p {{
        font-size: 12px;
        color: #9b9590;
    }}

    @media (max-width: 600px) {{
        .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .header h1 {{ font-size: 32px; }}
    }}
</style>
</head>
<body>
<div class="report">
    <div class="header">
        <h1>{_escape_html(person_name)}</h1>
        <p class="date-range">{_escape_html(stats["date_range_start"])} — {_escape_html(stats["date_range_end"])}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <span class="stat-number">{stats["total_entries"]}</span>
            <span class="stat-label">Entries</span>
        </div>
        <div class="stat-card">
            <span class="stat-number">{stats["starred_count"]}</span>
            <span class="stat-label">Starred</span>
        </div>
        <div class="stat-card">
            <span class="stat-number">{stats["total_photos"]}</span>
            <span class="stat-label">Photos</span>
        </div>
        <div class="stat-card">
            <span class="stat-number">{stats["unique_places"]}</span>
            <span class="stat-label">Places</span>
        </div>
    </div>

    <div class="section">
        <h2>Overview</h2>
        <p>{_escape_html(narrative.get("summary", ""))}</p>
    </div>

    <div class="section">
        <h2>Themes</h2>
        <div class="themes">{themes_html}</div>
    </div>

    <div class="section">
        <h2>Highlights</h2>
        {highlights_html}
    </div>

    <div class="section">
        <h2>Places</h2>
        <p>{_escape_html(narrative.get("places_narrative", ""))}</p>
        {places_html}
    </div>

    {co_people_html}

    <div class="section">
        <h2>Photos</h2>
        {gallery_html}
    </div>

    <div class="closing">
        <p>{_escape_html(narrative.get("closing", ""))}</p>
    </div>

    <div class="footer">
        <p>Generated by Rewind</p>
    </div>
</div>
</body>
</html>'''

    return html


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
