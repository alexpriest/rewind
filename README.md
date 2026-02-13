# Rewind

A Day One journal visualizer for exploring years of journal entries through interactive graphs, smart search, maps, and personalized reports. Built as a surprise gift.

## Features

- **Graph Explorer** — Interactive force-directed graph showing connections between people, places, and tags
- **Smart Search + Timeline + Map** — Full-text search with filters, timeline view, and GPS-plotted map
- **Personalized Reports** — AI-generated narrative summaries as beautiful standalone HTML pages
- **Tag Classification** — AI-powered classification of tags as people vs. topics

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLite + FTS5, Claude API (anthropic SDK), Pillow
- **Frontend:** SvelteKit (SPA mode, adapter-static), D3.js, Leaflet.js
- **Dev:** Both servers via `./scripts/dev.sh`

## Setup

```bash
# Backend
cd backend
pip install -e .

# Frontend
cd frontend
npm install

# Start both servers
./scripts/dev.sh
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Data

1. Open Day One → select "All Entries" in sidebar → File → Export → JSON
2. Make sure "Include media/photos" is checked
3. Upload the .zip through the Import page at `/import`

Multi-journal exports are supported — the importer finds all `Journal.json` files in the zip and combines entries.

## Architecture

### Backend (`backend/src/rewind/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, CORS, lifespan, all routers registered |
| `config.py` | Paths (data dir, DB, photos, thumbnails), ANTHROPIC_API_KEY |
| `db.py` | SQLite schema (7 tables + FTS5 + triggers + indexes), WAL mode |
| `models.py` | Pydantic models for all API responses |
| `importer/parser.py` | Day One JSON parsing, multi-journal support, markdown stripping |
| `importer/pipeline.py` | Import orchestrator: extract → parse → photos → DB → classify → graph |
| `importer/thumbnails.py` | Pillow thumbnail generation (400px JPEG) |
| `importer/classifier.py` | Claude tag classification (person vs. topic) in batches of 50 |
| `importer/graph.py` | Graph pre-computation (co-occurrence nodes + edges from entries) |
| `routers/import_router.py` | Upload + status polling endpoints |
| `routers/entries.py` | Entry list, timeline (grouped by month), places list, single entry |
| `routers/tags.py` | Tag list, update, classify, bulk-confirm |
| `routers/photos.py` | Thumbnail and full-size photo serving |
| `routers/graph.py` | Graph data (filtered), node entries |

### Frontend (`frontend/src/`)

| File | Purpose |
|------|---------|
| `app.css` | Global styles — warm journal theme with terracotta accent |
| `lib/api.ts` | Typed fetch wrapper for all API calls |
| `lib/types.ts` | TypeScript interfaces matching backend models |
| `lib/stores/filters.ts` | Shared filter state (query, people, places, tags, dates) |
| `lib/components/EntryCard.svelte` | Entry card: date, text, photo grid, lightbox, location, tags |
| `lib/components/SearchBar.svelte` | Text search + expandable filter panel (dates, tags, places) |
| `lib/components/FilterChips.svelte` | Active filter display with removable chips |
| `lib/components/Lightbox.svelte` | Full-screen photo viewer with keyboard nav |
| `lib/components/ForceGraph.svelte` | D3 force-directed graph (SVG, zoom, drag, hover) |
| `lib/components/GraphControls.svelte` | Graph filters: type toggles, date range, min connections |
| `lib/components/NodePanel.svelte` | Side panel showing entries for selected graph node |
| `routes/+layout.svelte` | Fixed sidebar nav (Home, Import, Entries, Explore, Reports) |
| `routes/+page.svelte` | Dashboard — stats or getting-started prompt |
| `routes/import/+page.svelte` | Drag-and-drop upload with progress bar |
| `routes/search/+page.svelte` | Entries page: SearchBar + Timeline/List tabs + FilterChips |
| `routes/explore/+page.svelte` | Graph explorer: ForceGraph + GraphControls + NodePanel |
| `routes/reports/+page.svelte` | Placeholder (Phase 4) |

### Database Schema

- **entries** — Core journal data with denormalized location + weather
- **entries_fts** — FTS5 virtual table (porter tokenizer, content-sync with entries)
- **tags** — Unique tags with `tag_type` (person/topic), AI suggestion, user confirmation
- **entry_tags** — Junction table
- **photos** — Photo metadata with `has_thumbnail` flag
- **graph_edges** — Pre-computed co-occurrence edges (weight, date range)
- **graph_nodes** — Pre-computed node stats (entry count, date range)
- **import_meta** — Import history

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/import/upload` | Upload Day One zip |
| GET | `/api/import/status/{id}` | Import progress |
| GET | `/api/entries` | List entries (page, page_size, q, tag, place, date_from, date_to) |
| GET | `/api/entries/timeline` | Entries grouped by month (same filters + limit) |
| GET | `/api/entries/places` | Distinct places with entry counts |
| GET | `/api/entries/{uuid}` | Single entry detail |
| GET | `/api/tags` | All tags with entry counts |
| PATCH | `/api/tags/{id}` | Update tag type (person/topic), sets user_confirmed |
| POST | `/api/tags/classify` | Trigger Claude classification for unconfirmed tags |
| POST | `/api/tags/bulk-confirm` | Bulk confirm tag classifications |
| GET | `/api/photos/{id}/thumbnail` | Serve 400px thumbnail |
| GET | `/api/photos/{id}/full` | Serve original photo |
| GET | `/api/graph` | Graph nodes + edges (types, date_from, date_to, min_weight) |
| GET | `/api/graph/node/{type}/{id}/entries` | Entries connected to a graph node |

### Key Design Decisions

- **Search matches both text AND tags** — `q` parameter does FTS5 on entry text AND LIKE match on tag names
- **Re-import preserves tag classifications** — user-confirmed tag types survive re-import
- **Photos stored by identifier** — `data/photos/{identifier}.{ext}` and `data/thumbnails/{identifier}.{ext}`
- **FTS5 triggers** — insert/update/delete triggers keep search index in sync automatically
- **SPA mode** — SvelteKit with adapter-static, all routing client-side
- **Graph pre-computation** — co-occurrence edges computed at import time, stored in DB, served via API
- **Tag classification** — Claude classifies tags as person/topic during import, user can review/override
- **Timeline grouping** — entries grouped by month (YYYY-MM prefix), server-side with "load more" pagination

## Status

### Phase 1: Foundation (complete)
- [x] Project scaffolding + git repo
- [x] Database schema (SQLite + FTS5 + triggers + indexes)
- [x] Day One JSON parser (multi-journal support)
- [x] Import pipeline with photo processing + thumbnails
- [x] Entry list API with search (FTS + tag matching)
- [x] Photo serving endpoints (thumbnail + full)
- [x] SvelteKit shell with sidebar nav
- [x] Import page with drag-and-drop + progress
- [x] Search page with entry cards + pagination
- [x] EntryCard component (date, text, photos, location, weather, tags)

### Phase 2: Search + Filters + Timeline (complete)
- [x] SearchBar with debounced text search + expandable filter panel
- [x] FilterChips showing active filters with remove buttons
- [x] Tag chips in filter panel (colored by type, with entry counts)
- [x] Date range and place filters
- [x] Timeline view grouped by month with "Load more" pagination
- [x] List view with traditional pagination
- [x] Tab toggle between Timeline and List views
- [x] Photo lightbox (full-screen, keyboard nav, prev/next)
- [x] Photo grid in entry cards (2-col, 120px, clickable)
- [x] Timeline API endpoint + places API endpoint
- [ ] Virtual scrolling (deferred — optimize when testing with real data)

### Phase 3: Tag Classification + Graph (complete)
- [x] Claude tag classifier (batches of 50, Sonnet, graceful skip if no API key)
- [x] Graph pre-computation (co-occurrence nodes + edges from entries/tags/places)
- [x] Import pipeline: classify → compute graph steps added
- [x] Tag classify + bulk-confirm API endpoints
- [x] Graph API (filterable by types, dates, min_weight)
- [x] Node entries API (entries connected to a specific node)
- [x] ForceGraph.svelte (D3 force simulation, SVG, zoom/pan, drag, hover highlight)
- [x] GraphControls.svelte (type toggles, date range, min connections, reset)
- [x] NodePanel.svelte (side panel with entry list for selected node)
- [x] Graph explorer page (fetch → filter → render → interact)
- [ ] Tag review/confirmation UI (deferred — can use existing PATCH endpoint)

### Phase 4: Map + Reports (next)
- [ ] Leaflet map view with marker clustering
- [ ] Map/list bidirectional filtering
- [ ] Claude report generation (narrative summary)
- [ ] Report HTML template (timeline, map, stats, excerpts, photos)
- [ ] ReportBuilder UI (person selector, progress, preview, download)
- [ ] Privacy review before sharing

### Phase 5: Polish
- [ ] Dashboard with real stats
- [ ] SSE progress for import
- [ ] Entry detail modal
- [ ] Responsive layout
- [ ] Error handling + loading states everywhere
- [ ] Performance tuning for large datasets
