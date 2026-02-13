from fastapi import APIRouter, HTTPException

from rewind.db import get_db
from rewind.importer.classifier import classify_tags
from rewind.models import BulkConfirmRequest, TagResponse, TagUpdateRequest

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags() -> list[TagResponse]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT t.*, COUNT(et.entry_uuid) as entry_count
               FROM tags t
               LEFT JOIN entry_tags et ON et.tag_id = t.id
               GROUP BY t.id
               ORDER BY entry_count DESC"""
        ).fetchall()

        return [
            TagResponse(
                id=r["id"],
                name=r["name"],
                tag_type=r["tag_type"],
                ai_suggested_type=r["ai_suggested_type"],
                user_confirmed=bool(r["user_confirmed"]),
                entry_count=r["entry_count"],
            )
            for r in rows
        ]
    finally:
        conn.close()


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, body: TagUpdateRequest) -> TagResponse:
    if body.tag_type not in ("person", "topic"):
        raise HTTPException(
            status_code=400, detail="tag_type must be 'person' or 'topic'"
        )

    conn = get_db()
    try:
        conn.execute(
            "UPDATE tags SET tag_type = ?, user_confirmed = 1 WHERE id = ?",
            (body.tag_type, tag_id),
        )
        conn.commit()

        row = conn.execute(
            """SELECT t.*, COUNT(et.entry_uuid) as entry_count
               FROM tags t
               LEFT JOIN entry_tags et ON et.tag_id = t.id
               WHERE t.id = ?
               GROUP BY t.id""",
            (tag_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Tag not found")

        return TagResponse(
            id=row["id"],
            name=row["name"],
            tag_type=row["tag_type"],
            ai_suggested_type=row["ai_suggested_type"],
            user_confirmed=bool(row["user_confirmed"]),
            entry_count=row["entry_count"],
        )
    finally:
        conn.close()


@router.post("/classify", response_model=list[TagResponse])
def classify_unclassified_tags() -> list[TagResponse]:
    conn = get_db()
    try:
        unclassified = conn.execute(
            "SELECT name FROM tags WHERE user_confirmed = 0"
        ).fetchall()
        unclassified_names = [r["name"] for r in unclassified]

        if unclassified_names:
            classifications = classify_tags(unclassified_names)
            for tag_name, tag_type in classifications.items():
                conn.execute(
                    "UPDATE tags SET tag_type = ?, ai_suggested_type = ? WHERE name = ?",
                    (tag_type, tag_type, tag_name),
                )
            conn.commit()

        rows = conn.execute(
            """SELECT t.*, COUNT(et.entry_uuid) as entry_count
               FROM tags t
               LEFT JOIN entry_tags et ON et.tag_id = t.id
               GROUP BY t.id
               ORDER BY entry_count DESC"""
        ).fetchall()

        return [
            TagResponse(
                id=r["id"],
                name=r["name"],
                tag_type=r["tag_type"],
                ai_suggested_type=r["ai_suggested_type"],
                user_confirmed=bool(r["user_confirmed"]),
                entry_count=r["entry_count"],
            )
            for r in rows
        ]
    finally:
        conn.close()


@router.post("/bulk-confirm", response_model=list[TagResponse])
def bulk_confirm_tags(body: BulkConfirmRequest) -> list[TagResponse]:
    conn = get_db()
    try:
        if body.tag_ids:
            placeholders = ",".join("?" * len(body.tag_ids))
            conn.execute(
                f"UPDATE tags SET user_confirmed = 1 WHERE id IN ({placeholders})",
                body.tag_ids,
            )
            conn.commit()

        rows = conn.execute(
            """SELECT t.*, COUNT(et.entry_uuid) as entry_count
               FROM tags t
               LEFT JOIN entry_tags et ON et.tag_id = t.id
               GROUP BY t.id
               ORDER BY entry_count DESC"""
        ).fetchall()

        return [
            TagResponse(
                id=r["id"],
                name=r["name"],
                tag_type=r["tag_type"],
                ai_suggested_type=r["ai_suggested_type"],
                user_confirmed=bool(r["user_confirmed"]),
                entry_count=r["entry_count"],
            )
            for r in rows
        ]
    finally:
        conn.close()
