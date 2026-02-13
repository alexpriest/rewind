# Rewind — Implementation Plan

## What Exists (Phases 1-3 Complete)

The full project is at `~/Code/projects/rewind/`. Backend is Python/FastAPI, frontend is SvelteKit. Both run via `./scripts/dev.sh`.

### Backend (`backend/src/rewind/`)
- `main.py` — FastAPI app with CORS (localhost:5173), lifespan init, routers: entries, tags, photos, import, graph
- `config.py` — Settings class with DATA_DIR, DB_PATH, PHOTOS_DIR, THUMBNAILS_DIR, ANTHROPIC_API_KEY
- `db.py` — SQLite schema with 7 tables + FTS5 + triggers. `get_db()` returns connection with WAL mode + row_factory. `init_db()` creates tables.
- `models.py` — Pydantic: EntryResponse, PhotoResponse, TagResponse, EntryListResponse, TimelineGroup, TimelineResponse, PlaceCount, ImportStatus, TagUpdateRequest, BulkConfirmRequest, GraphNodeResponse, GraphEdgeResponse, GraphResponse
- `importer/parser.py` — `parse_all_journals(paths)` combines multiple Journal.json files, dedupes by UUID. `_parse_entry()` handles all Day One fields.
- `importer/pipeline.py` — `ImportPipeline.run()`: extract zip → find all Journal.json → parse → process photos → clear DB (preserve confirmed tags) → insert entries/tags/photos → classify tags (Claude) → compute graph → record metadata. Status stored in module-level `_import_statuses` dict.
- `importer/thumbnails.py` — `process_photos()`: find photo files by identifier/md5, copy to photos dir, generate 400px thumbnails via Pillow.
- `importer/classifier.py` — `classify_tags(tag_names)`: sends tags to Claude Sonnet in batches of 50, returns dict mapping tag names to 'person'|'topic'. Skips gracefully if no API key.
- `importer/graph.py` — `compute_graph(db_path)`: reads all entries+tags+places, computes co-occurrence nodes and edges for every pair of nodes in the same entry, bulk inserts into graph tables. Returns (node_count, edge_count).
- `routers/entries.py` — `GET /api/entries` with pagination + filters (q searches FTS AND tags, tag, place, date_from, date_to). `GET /api/entries/timeline` (grouped by month, same filters + limit). `GET /api/entries/places` (distinct places with counts). `GET /api/entries/{uuid}`.
- `routers/tags.py` — `GET /api/tags` (with counts). `PATCH /api/tags/{id}` (update type). `POST /api/tags/classify` (trigger Claude classification). `POST /api/tags/bulk-confirm` (bulk set user_confirmed=1).
- `routers/photos.py` — `GET /api/photos/{id}/thumbnail` and `/full`.
- `routers/import_router.py` — `POST /api/import/upload`, `GET /api/import/status/{id}`.
- `routers/graph.py` — `GET /api/graph` (nodes+edges, filterable by types/dates/min_weight). `GET /api/graph/node/{type}/{id}/entries` (entries for a node).

### Frontend (`frontend/src/`)
- SvelteKit with adapter-static (SPA mode), Vite proxy `/api` → localhost:8000
- Svelte 5 runes throughout ($state, $derived, $props, $effect)
- `lib/api.ts` — typed fetch wrapper: getEntries, getEntry, getTimeline, getPlaces, getTags, updateTag, classifyTags, bulkConfirmTags, uploadJournal, getImportStatus, getGraph, getNodeEntries, healthCheck
- `lib/types.ts` — Entry, Photo, Tag, EntryListResponse, TimelineGroup, TimelineResponse, PlaceCount, ImportStatus, GraphNode, GraphEdge, GraphData
- `lib/stores/filters.ts` — writable store for Filters
- `lib/components/EntryCard.svelte` — card with date (serif), star, snippet, photo grid (2-col, 120px, clickable), lightbox trigger, location, weather, word count, tag chips
- `lib/components/SearchBar.svelte` — text input (debounced 300ms) + expandable filter panel with date range, place input, tag chips (colored by type)
- `lib/components/FilterChips.svelte` — active filter display with removable chips and "Clear all"
- `lib/components/Lightbox.svelte` — full-screen photo viewer with keyboard nav, prev/next, counter, loading state
- `lib/components/ForceGraph.svelte` — D3 force simulation with SVG rendering, zoom/pan, drag, hover highlighting, click-to-select
- `lib/components/GraphControls.svelte` — type toggles (colored dots), date range, min connections slider, reset
- `lib/components/NodePanel.svelte` — slide-in side panel with node info + scrollable entry list
- `routes/+layout.svelte` — fixed sidebar (200px) with nav links, `{@render children()}`
- `routes/+page.svelte` — dashboard (stats if data exists, welcome CTA if not)
- `routes/import/+page.svelte` — drag-and-drop, polls status, shows progress bar + done summary
- `routes/search/+page.svelte` — "Entries" page: SearchBar + FilterChips + Timeline/List tab toggle. Timeline shows month groups with serif headers + "Load more". List has pagination.
- `routes/explore/+page.svelte` — graph explorer: fetches graph data, client-side filtering via GraphControls, ForceGraph + NodePanel layout
- `routes/reports/+page.svelte` — placeholder (Phase 4)

### Database Tables
- entries (uuid PK, creation_date, modified_date, timezone, text, snippet, starred, lat/lon, place_name, locality, admin_area, country, weather_description, weather_temp_c, duration, word_count)
- entries_fts (FTS5, content-sync with entries, porter tokenizer)
- tags (id, name UNIQUE, tag_type, ai_suggested_type, user_confirmed)
- entry_tags (entry_uuid, tag_id)
- photos (id, entry_uuid, identifier, md5, file_type, width, height, has_thumbnail)
- graph_edges (source_type, source_id, target_type, target_id, weight, first_date, last_date)
- graph_nodes (node_type, node_id, label, entry_count, first_date, last_date)
- import_meta (imported_at, entry_count, tag_count, photo_count, filename, duration_seconds)

### Color Palette (CSS variables in app.css)
- --color-bg: #faf8f5, --color-surface: #ffffff, --color-text: #2d2a26
- --color-accent: #c06a45 (terracotta), --color-accent-light: #f0ddd3, --color-accent-dark: #9b4f30
- --color-person: #7c6bc4 (purple), --color-place: #4a9e7a (green), --color-topic: #c49a3c (gold)
- --color-starred: #d4a843, --color-danger: #c44b4b, --color-success: #4a9e6a

---

## Phase 4: Map + Reports

### 4A. Map View

**Backend — `GET /api/entries/map-points`:**
- Returns entries that have lat/lon: `[{ uuid, latitude, longitude, creation_date, snippet, place_name, photo_id }]`
- Supports same filters as entries endpoint
- Lightweight response (no full text, just what's needed for map markers)

**Frontend — update `routes/search/+page.svelte`:**
- Add third tab: "Timeline" | "List" | "Map"
- Map tab renders MapView component

**Frontend — new `lib/components/MapView.svelte`:**
- Leaflet.js with OpenStreetMap tiles
- Marker for each entry with GPS coordinates
- Marker clustering for dense areas (use leaflet.markercluster)
- Click marker → popup with entry snippet, date, photo thumbnail, link to full entry
- Map bounds update when filters change
- Bidirectional: selecting a marker filters the entry list, changing filters updates map markers

Install: `npm install leaflet.markercluster @types/leaflet.markercluster`

### 4B. Claude Report Generation

**Backend — new `services/report.py`:**
- `generate_report(person_tag_id: int, date_from: str | None, date_to: str | None) -> str`
- Fetch all entries for the person (via entry_tags)
- Build prompt with entry excerpts, dates, places, co-occurring tags
- Claude generates narrative sections: themes, timeline highlights, favorite places, relationship evolution
- Return structured data (JSON with sections)

**Backend — new report HTML template:**
- Standalone HTML page (inline CSS, no external dependencies)
- Sections: header (person name, date range), summary stats, narrative themes, timeline highlights with excerpts, places, photo gallery
- Beautiful typography, warm color palette matching the app
- Self-contained — can be saved and shared as a single file

**Backend — `routers/reports.py`:**
- `POST /api/reports/generate` — body: `{ person_tag_id, date_from?, date_to? }`. Starts generation in background, returns report ID.
- `GET /api/reports/{id}/status` — polling endpoint (status + progress)
- `GET /api/reports/{id}/html` — serve the generated HTML file

### 4C. Report Builder UI

**Frontend — update `routes/reports/+page.svelte`:**
Replace placeholder with ReportBuilder:
- Person selector: dropdown/search of person-typed tags
- Optional date range
- "Generate Report" button
- Progress indicator while generating
- Preview: rendered HTML in iframe
- Privacy review: show all excerpts included, toggle individual ones on/off
- Download button (saves HTML file)

**Frontend — new `lib/components/ReportBuilder.svelte`:**
- Person picker (searchable dropdown of person tags, sorted by entry count)
- Date range inputs
- Generate button with loading state
- Report preview in iframe when done

### Phase 4 Verification
- Map shows markers for entries with GPS data
- Marker clusters at zoom-out, individual pins at zoom-in
- Click marker shows popup with entry info
- Report generates for a person with relevant entries
- Report HTML is self-contained, looks good when opened standalone
- Privacy review shows all included excerpts
- Download produces a working HTML file

---

## Execution Notes

- Backend runs on port 8000 with `--reload` (auto-restarts on file changes)
- Frontend runs on port 5173 with Vite HMR
- Data lives in `~/Code/projects/rewind/data/` (.gitignored)
- `ANTHROPIC_API_KEY` env var needed for tag classification and report generation
- Use `python3.11` (not `python`) on this machine
- All Svelte components use Svelte 5 runes ($state, $derived, $props, $effect)
- Layout uses `{@render children()}` not `<slot />`
- Import `{ page } from '$app/state'` for route info
- Callback props instead of createEventDispatcher (Svelte 5)
- Event handlers: `onclick={fn}` not `on:click={fn}`
