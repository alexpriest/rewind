# Rewind — Implementation Plan (Phases 2-4)

## What Exists (Phase 1 Complete)

The full project is at `~/Code/projects/rewind/`. Backend is Python/FastAPI, frontend is SvelteKit. Both run via `./scripts/dev.sh`.

### Backend (`backend/src/rewind/`)
- `main.py` — FastAPI app with CORS (localhost:5173), lifespan init, routers for entries, tags, photos, import
- `config.py` — Settings class with DATA_DIR, DB_PATH, PHOTOS_DIR, THUMBNAILS_DIR, ANTHROPIC_API_KEY
- `db.py` — SQLite schema with 7 tables + FTS5 + triggers. `get_db()` returns connection with WAL mode + row_factory. `init_db()` creates tables.
- `models.py` — Pydantic: EntryResponse, PhotoResponse, TagResponse, EntryListResponse, ImportStatus, TagUpdateRequest, etc.
- `importer/parser.py` — `parse_all_journals(paths)` combines multiple Journal.json files, dedupes by UUID. `_parse_entry()` handles all Day One fields.
- `importer/pipeline.py` — `ImportPipeline.run()`: extract zip → find all Journal.json → parse → process photos → clear DB (preserve confirmed tags) → insert entries/tags/photos → record metadata. Status stored in module-level `_import_statuses` dict.
- `importer/thumbnails.py` — `process_photos()`: find photo files by identifier/md5, copy to photos dir, generate 400px thumbnails via Pillow. Sets `has_thumbnail` on photo dicts.
- `routers/entries.py` — `GET /api/entries` with pagination + filters (q searches FTS AND tags, tag, place, date_from, date_to). `GET /api/entries/{uuid}`. Both join tags + photos per entry.
- `routers/tags.py` — `GET /api/tags` (with entry counts, sorted desc). `PATCH /api/tags/{id}` (update tag_type, set user_confirmed=1).
- `routers/photos.py` — `GET /api/photos/{id}/thumbnail` and `/full`, find file by identifier, serve via FileResponse.
- `routers/import_router.py` — `POST /api/import/upload` (saves file, runs pipeline in background thread), `GET /api/import/status/{id}`.

### Frontend (`frontend/src/`)
- SvelteKit with adapter-static (SPA mode), Vite proxy `/api` → localhost:8000
- Svelte 5 runes throughout ($state, $derived, $props, $effect)
- `lib/api.ts` — typed fetch wrapper: getEntries, getEntry, getTags, updateTag, uploadJournal, getImportStatus, healthCheck
- `lib/types.ts` — Entry, Photo, Tag, EntryListResponse, ImportStatus, GraphNode, GraphEdge, GraphData
- `lib/stores/filters.ts` — writable store for Filters (query, people, places, tags, dateFrom, dateTo)
- `lib/components/EntryCard.svelte` — card with date (serif), star, snippet, photo thumbnails (up to 4), location, weather, word count, tag chips
- `routes/+layout.svelte` — fixed sidebar (200px) with nav links, `{@render children()}`
- `routes/+page.svelte` — dashboard (stats if data exists, welcome CTA if not)
- `routes/import/+page.svelte` — drag-and-drop, polls status, shows progress bar + done summary
- `routes/search/+page.svelte` — text search input, paginated entry list, reads ?tag= from URL

### Database Tables
- entries (uuid PK, creation_date, text, snippet, starred, lat/lon, place_name, locality, admin_area, country, weather, word_count)
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

## Phase 2: Search + Filters + Timeline

### 2A. Combined Filter UI

**Backend changes:** None — the entries endpoint already supports all filter params.

**Frontend — `routes/search/+page.svelte`:**
Replace the simple search input with a full filter bar:
- Text search input (debounced, fires on Enter or after 300ms idle)
- Date range picker (two date inputs: from/to)
- Tag filter chips — load tags from `GET /api/tags`, show as clickable chips below search bar. Selected chips apply as tag filters. Color chips by tag_type (person=purple, topic=gold).
- Place filter — text input or dropdown of known places from entries
- Active filters shown as removable chips below the filter bar
- All filters stored in the shared `filters` store and sent to getEntries()

**Frontend — new `lib/components/SearchBar.svelte`:**
- Text input + filter toggle button
- Expandable filter panel (date range, tag chips, place input)
- "Clear all" button when any filters active

**Frontend — new `lib/components/FilterChips.svelte`:**
- Row of active filter chips with × remove buttons
- Shows: search query, selected tags, place, date range

### 2B. Timeline View

**Backend — new endpoint `GET /api/entries/timeline`:**
- Same filters as `/api/entries`, but returns entries grouped by month
- Response: `{ groups: [{ month: "2024-01", label: "January 2024", entries: [...], count: int }], total: int }`
- Limit to most recent 500 entries by default, load more on scroll

**Frontend — update `routes/search/+page.svelte`:**
- Tab toggle: "List" | "Timeline" (default to Timeline)
- Timeline view groups entries by month with month headers
- Each month header shows: "January 2024 — 23 entries"
- EntryCards rendered within each group
- Infinite scroll or "Load more" button

### 2C. Virtual Scrolling

**Frontend — update timeline/list view:**
- Use `@tanstack/svelte-virtual` for virtualizing the entry list
- Only render visible entries + buffer
- Each EntryCard needs a consistent estimated height (~200px, with dynamic measurement)
- Important for 10+ years of entries

### 2D. Photo Gallery

**Frontend — update `EntryCard.svelte`:**
- Show photo thumbnails in a grid (not just a row)
- Click thumbnail to open lightbox
- Lightbox: full-size image, left/right navigation, close button

**Frontend — new `lib/components/Lightbox.svelte`:**
- Modal overlay with full-size photo
- Arrow keys / click for prev/next
- Close on Escape or click outside
- Uses `/api/photos/{id}/full`

### Phase 2 Verification
- Search for a person name → returns entries with that tag
- Filter by date range → only shows entries in range
- Combine text search + tag + date → intersection of results
- Timeline groups correctly by month
- Photos display as grid, click opens lightbox
- Performance acceptable with thousands of entries

---

## Phase 3: Tag Classification + Graph

### 3A. Claude Tag Classification

**Backend — new `importer/classifier.py`:**
- `classify_tags(tags: list[str]) -> dict[str, str]` — sends tags to Claude in batches of ~50
- Prompt: "Classify each tag as 'person' (a human name) or 'topic' (an activity, place, thing, or concept). Return JSON: {tag: type}"
- Uses anthropic SDK with ANTHROPIC_API_KEY from config
- Handles rate limits, retries

**Backend — update `importer/pipeline.py`:**
- After inserting tags, call classifier for tags where `user_confirmed=0 AND ai_suggested_type IS NULL`
- Write `ai_suggested_type` and `tag_type` to DB for each classified tag
- Add progress step: "Classifying tags..."

**Backend — update `routers/tags.py`:**
- `POST /api/tags/classify` — trigger classification for unclassified tags (for manual re-run)
- `POST /api/tags/bulk-confirm` — accept list of tag IDs, set user_confirmed=1 on all

### 3B. Tag Review UI

**Frontend — new `routes/import/tags/+page.svelte` or section in import page:**
- After import completes, show tag classification review
- Two columns: "People" and "Topics"
- Each tag shown as a draggable/clickable chip
- AI-suggested type shown, user can flip person↔topic by clicking
- "Confirm All" button to bulk-confirm
- Tags colored by type (purple=person, gold=topic)

### 3C. Graph Pre-computation

**Backend — new `importer/graph.py`:**
- `compute_graph(db_path: Path)` — called at end of import pipeline
- For each entry, collect node set: people (from person-typed tags), places (from place_name), topics (from topic-typed tags)
- For every pair of nodes in the same entry, upsert edge weight (+1)
- Bulk insert/update graph_nodes (entry_count, first_date, last_date) and graph_edges (weight, date range)
- This is the most computationally intensive step — batch and commit periodically

**Backend — update `importer/pipeline.py`:**
- Add graph computation step after tag classification
- Progress: "Computing graph..."

### 3D. Graph API

**Backend — new `routers/graph.py`:**
- `GET /api/graph` — returns all nodes + edges
  - Query params: `types` (comma-separated: person,place,topic), `date_from`, `date_to`, `min_weight` (edge filter)
  - Response: `{ nodes: [...], edges: [...] }`
- `GET /api/graph/node/{type}/{id}/entries` — returns entries connected to a specific node
  - For person/topic: entries with that tag
  - For place: entries at that place_name

### 3E. Force-Directed Graph

**Frontend — `routes/explore/+page.svelte`:**
Replace placeholder with full graph explorer layout:
- Main area: SVG graph
- Right side panel: entry list for selected node (collapsed by default)
- Top controls bar: type toggles, time slider, search within graph

**Frontend — new `lib/components/ForceGraph.svelte`:**
- Uses d3-force simulation: forceLink, forceManyBody, forceCenter, forceCollide
- SVG rendering (not canvas) for Svelte reactivity
- Nodes: circles sized by entry_count (sqrt scale), colored by type
- Edges: lines with opacity by weight
- Node labels: text elements, show on hover or for high-count nodes
- Zoom + pan via d3-zoom
- Click node → dispatch event to parent with node info
- Drag nodes to reposition

**Frontend — new `lib/components/GraphControls.svelte`:**
- Type toggles: checkboxes for Person / Place / Topic (each with colored indicator)
- Time range slider: dual-handle slider for date range, updates graph to only show nodes/edges in range
- Minimum connections slider: filter out low-weight edges
- Layout reset button

### Phase 3 Verification
- After import, tags are auto-classified (most person names detected)
- Tag review UI allows flipping types, bulk confirming
- Graph shows nodes for people, places, topics with correct counts
- Clicking a node shows related entries
- Time slider filters graph to date range
- Type toggles hide/show node categories
- Graph handles 100+ nodes without performance issues

---

## Phase 4: Map + Reports

### 4A. Map View

**Backend — `GET /api/entries/map-points`:**
- Returns entries that have lat/lon: `[{ uuid, latitude, longitude, creation_date, snippet, place_name, photo_id }]`
- Supports same filters as entries endpoint
- Lightweight response (no full text, just what's needed for map markers)

**Frontend — update `routes/search/+page.svelte`:**
- Add third tab: "List" | "Timeline" | "Map"
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
- Sections: header (person name, date range), summary stats, narrative themes, timeline highlights with excerpts, places map (static image or inline Leaflet), photo gallery
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
