import logging
import sqlite3
from collections import defaultdict

logger = logging.getLogger(__name__)


def compute_graph(db_path) -> tuple[int, int]:
    """Compute graph nodes and edges from entries+tags+places.

    Returns (node_count, edge_count).
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=wal")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        conn.execute("DELETE FROM graph_edges")
        conn.execute("DELETE FROM graph_nodes")
        conn.commit()

        # Build tag type lookup
        tag_rows = conn.execute("SELECT name, tag_type FROM tags").fetchall()
        tag_types: dict[str, str] = {r["name"]: r["tag_type"] for r in tag_rows}

        # Node stats: (node_type, node_id) -> {entry_count, first_date, last_date, label}
        node_stats: dict[tuple[str, str], dict] = defaultdict(
            lambda: {"entry_count": 0, "first_date": None, "last_date": None, "label": ""}
        )

        # Edge stats: (src_type, src_id, tgt_type, tgt_id) -> {weight, first_date, last_date}
        edge_stats: dict[tuple[str, str, str, str], dict] = defaultdict(
            lambda: {"weight": 0, "first_date": None, "last_date": None}
        )

        entry_rows = conn.execute(
            "SELECT uuid, creation_date, place_name FROM entries"
        ).fetchall()

        # Batch-fetch all entry_tags
        entry_tag_rows = conn.execute(
            """SELECT et.entry_uuid, t.name
               FROM entry_tags et JOIN tags t ON t.id = et.tag_id"""
        ).fetchall()
        tags_by_entry: dict[str, list[str]] = defaultdict(list)
        for r in entry_tag_rows:
            tags_by_entry[r["entry_uuid"]].append(r["name"])

        for entry in entry_rows:
            entry_uuid = entry["uuid"]
            date = entry["creation_date"]
            place_name = entry["place_name"]

            # Collect nodes for this entry
            entry_nodes: list[tuple[str, str]] = []

            for tag_name in tags_by_entry.get(entry_uuid, []):
                node_type = tag_types.get(tag_name, "topic")
                entry_nodes.append((node_type, tag_name))

            if place_name:
                entry_nodes.append(("place", place_name))

            # Update node stats
            for node_type, node_id in entry_nodes:
                stats = node_stats[(node_type, node_id)]
                stats["entry_count"] += 1
                stats["label"] = node_id
                if stats["first_date"] is None or date < stats["first_date"]:
                    stats["first_date"] = date
                if stats["last_date"] is None or date > stats["last_date"]:
                    stats["last_date"] = date

            # Update edge stats for every pair
            for i in range(len(entry_nodes)):
                for j in range(i + 1, len(entry_nodes)):
                    a = entry_nodes[i]
                    b = entry_nodes[j]
                    # Normalize direction: sort by (type, id)
                    if (a[0], a[1]) > (b[0], b[1]):
                        a, b = b, a
                    edge_key = (a[0], a[1], b[0], b[1])
                    edge = edge_stats[edge_key]
                    edge["weight"] += 1
                    if edge["first_date"] is None or date < edge["first_date"]:
                        edge["first_date"] = date
                    if edge["last_date"] is None or date > edge["last_date"]:
                        edge["last_date"] = date

        # Bulk insert nodes
        node_rows = [
            (ntype, nid, stats["label"], stats["entry_count"], stats["first_date"], stats["last_date"])
            for (ntype, nid), stats in node_stats.items()
        ]
        conn.executemany(
            """INSERT INTO graph_nodes (node_type, node_id, label, entry_count, first_date, last_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            node_rows,
        )

        # Bulk insert edges
        edge_rows = [
            (st, si, tt, ti, stats["weight"], stats["first_date"], stats["last_date"])
            for (st, si, tt, ti), stats in edge_stats.items()
        ]
        conn.executemany(
            """INSERT INTO graph_edges (source_type, source_id, target_type, target_id, weight, first_date, last_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            edge_rows,
        )

        conn.commit()

        logger.info(f"Graph computed: {len(node_rows)} nodes, {len(edge_rows)} edges")
        return len(node_rows), len(edge_rows)

    finally:
        conn.close()
