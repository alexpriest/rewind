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
| `main.py` | FastAPI app, CORS, lifespan |
| `config.py` | Paths (data dir, DB, photos, thumbnails), settings |
| `db.py` | SQLite schema (7 tables + FTS5 + triggers + indexes), WAL mode |
| `models.py` | Pydantic models for all API responses |
| `importer/parser.py` | Day One JSON parsing, multi-journal support, markdown stripping |
| `importer/pipeline.py` | Import orchestrator: extract → parse → photos → DB insert |
| `importer/thumbnails.py` | Pillow thumbnail generation (400px JPEG) |
| `routers/import_router.py` | Upload + status polling endpoints |
| `routers/entries.py` | Entry list (paginated, filterable by text+tags+place+date), single entry |
| `routers/tags.py` | Tag list with counts, tag type update |
| `routers/photos.py` | Thumbnail and full-size photo serving |

### Frontend (`frontend/src/`)

| File | Purpose |
|------|---------|
| `app.css` | Global styles — warm journal theme with terracotta accent |
| `lib/api.ts` | Typed fetch wrapper for all API calls |
| `lib/types.ts` | TypeScript interfaces matching backend models |
| `lib/stores/filters.ts` | Shared filter state (query, people, places, tags, dates) |
| `lib/components/EntryCard.svelte` | Journal entry card with date, text, photos, location, tags |
| `routes/+layout.svelte` | Fixed sidebar nav (Home, Import, Search, Explore, Reports) |
| `routes/+page.svelte` | Dashboard — stats or getting-started prompt |
| `routes/import/+page.svelte` | Drag-and-drop upload with progress bar |
| `routes/search/+page.svelte` | Text search + paginated entry list |
| `routes/explore/+page.svelte` | Placeholder (Phase 3) |
| `routes/reports/+page.svelte` | Placeholder (Phase 4) |

### Database Schema

- **entries** — Core journal data with denormalized location + weather
- **entries_fts** — FTS5 virtual table (porter tokenizer, content-sync with entries)
- **tags** — Unique tags with `tag_type` (person/topic), AI suggestion, user confirmation
- **entry_tags** — Junction table
- **photos** — Photo metadata with `has_thumbnail` flag
- **graph_edges** — Pre-computed co-occurrence edges (Phase 3)
- **graph_nodes** — Pre-computed node stats (Phase 3)
- **import_meta** — Import history

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/import/upload` | Upload Day One zip |
| GET | `/api/import/status/{id}` | Import progress |
| GET | `/api/entries` | List entries (params: page, page_size, q, tag, place, date_from, date_to) |
| GET | `/api/entries/{uuid}` | Single entry detail |
| GET | `/api/tags` | All tags with entry counts |
| PATCH | `/api/tags/{id}` | Update tag type (person/topic) |
| GET | `/api/photos/{id}/thumbnail` | Serve 400px thumbnail |
| GET | `/api/photos/{id}/full` | Serve original photo |

### Key Design Decisions

- **Search matches both text AND tags** — `q` parameter does FTS5 on entry text AND LIKE match on tag names
- **Re-import preserves tag classifications** — user-confirmed tag types survive re-import
- **Photos stored by identifier** — `data/photos/{identifier}.{ext}` and `data/thumbnails/{identifier}.{ext}`
- **FTS5 triggers** — insert/update/delete triggers keep search index in sync automatically
- **SPA mode** — SvelteKit with adapter-static, all routing client-side

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

### Phase 2: Search + Filters (next)
- [ ] Combined filter UI (SearchBar + FilterChips)
- [ ] Timeline view grouped by month
- [ ] Virtual scrolling (@tanstack/svelte-virtual)
- [ ] Photo lightbox/gallery in entry cards

### Phase 3: Tag Classification + Graph
- [ ] Claude tag classification (person vs. topic)
- [ ] Tag review/confirmation UI
- [ ] Graph pre-computation (co-occurrence edges)
- [ ] Force-directed graph (D3.js)
- [ ] Graph controls (type toggles, time slider)
- [ ] Node click → entry list

### Phase 4: Map + Reports
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
