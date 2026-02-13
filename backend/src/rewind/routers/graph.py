from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query

from rewind.db import get_db
from rewind.models import (
    EntryResponse,
    GraphEdgeResponse,
    GraphNodeResponse,
    GraphResponse,
    PhotoResponse,
)

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
def get_graph(
    types: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_weight: int = Query(1, ge=1),
) -> GraphResponse:
    conn = get_db()
    try:
        type_filter = set()
        if types:
            type_filter = {t.strip() for t in types.split(",")}

        # Fetch nodes
        node_rows = conn.execute("SELECT * FROM graph_nodes").fetchall()
        nodes: list[GraphNodeResponse] = []
        node_set: set[tuple[str, str]] = set()

        for r in node_rows:
            if type_filter and r["node_type"] not in type_filter:
                continue
            if date_from and r["last_date"] and r["last_date"] < date_from:
                continue
            if date_to and r["first_date"] and r["first_date"] > date_to:
                continue

            nodes.append(
                GraphNodeResponse(
                    node_type=r["node_type"],
                    node_id=r["node_id"],
                    label=r["label"],
                    entry_count=r["entry_count"],
                    first_date=r["first_date"],
                    last_date=r["last_date"],
                )
            )
            node_set.add((r["node_type"], r["node_id"]))

        # Fetch edges
        edge_rows = conn.execute(
            "SELECT * FROM graph_edges WHERE weight >= ?", (min_weight,)
        ).fetchall()
        edges: list[GraphEdgeResponse] = []

        for r in edge_rows:
            if (r["source_type"], r["source_id"]) not in node_set:
                continue
            if (r["target_type"], r["target_id"]) not in node_set:
                continue
            if date_from and r["last_date"] and r["last_date"] < date_from:
                continue
            if date_to and r["first_date"] and r["first_date"] > date_to:
                continue

            edges.append(
                GraphEdgeResponse(
                    source_type=r["source_type"],
                    source_id=r["source_id"],
                    target_type=r["target_type"],
                    target_id=r["target_id"],
                    weight=r["weight"],
                    first_date=r["first_date"],
                    last_date=r["last_date"],
                )
            )

        return GraphResponse(nodes=nodes, edges=edges)
    finally:
        conn.close()


@router.get("/node/{node_type}/{node_id}/entries", response_model=list[EntryResponse])
def get_node_entries(node_type: str, node_id: str) -> list[EntryResponse]:
    if node_type not in ("person", "topic", "place"):
        raise HTTPException(status_code=400, detail="node_type must be 'person', 'topic', or 'place'")

    conn = get_db()
    try:
        if node_type in ("person", "topic"):
            entry_rows = conn.execute(
                """SELECT e.* FROM entries e
                   JOIN entry_tags et ON et.entry_uuid = e.uuid
                   JOIN tags t ON t.id = et.tag_id
                   WHERE t.name = ?
                   ORDER BY e.creation_date DESC""",
                (node_id,),
            ).fetchall()
        else:
            entry_rows = conn.execute(
                """SELECT * FROM entries
                   WHERE place_name = ?
                   ORDER BY creation_date DESC""",
                (node_id,),
            ).fetchall()

        if not entry_rows:
            return []

        uuids = [r["uuid"] for r in entry_rows]
        placeholders = ",".join("?" * len(uuids))

        tag_rows = conn.execute(
            f"""SELECT et.entry_uuid, t.name
                FROM entry_tags et JOIN tags t ON t.id = et.tag_id
                WHERE et.entry_uuid IN ({placeholders})""",
            uuids,
        ).fetchall()
        tags_by_uuid: dict[str, list[str]] = defaultdict(list)
        for r in tag_rows:
            tags_by_uuid[r["entry_uuid"]].append(r["name"])

        photo_rows = conn.execute(
            f"SELECT * FROM photos WHERE entry_uuid IN ({placeholders})",
            uuids,
        ).fetchall()
        photos_by_uuid: dict[str, list[PhotoResponse]] = defaultdict(list)
        for r in photo_rows:
            photos_by_uuid[r["entry_uuid"]].append(
                PhotoResponse(
                    id=r["id"],
                    identifier=r["identifier"],
                    file_type=r["file_type"],
                    has_thumbnail=bool(r["has_thumbnail"]),
                )
            )

        return [
            EntryResponse(
                uuid=r["uuid"],
                creation_date=r["creation_date"],
                text=r["text"],
                snippet=r["snippet"],
                starred=bool(r["starred"]),
                latitude=r["latitude"],
                longitude=r["longitude"],
                place_name=r["place_name"],
                locality=r["locality"],
                admin_area=r["admin_area"],
                country=r["country"],
                weather_description=r["weather_description"],
                weather_temp_c=r["weather_temp_c"],
                word_count=r["word_count"],
                tags=tags_by_uuid.get(r["uuid"], []),
                photos=photos_by_uuid.get(r["uuid"], []),
            )
            for r in entry_rows
        ]
    finally:
        conn.close()
