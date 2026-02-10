# Rewind

A Day One journal visualizer for exploring years of journal entries through interactive graphs, smart search, maps, and personalized reports.

## Features

- **Graph Explorer** — Interactive force-directed graph showing connections between people, places, and tags
- **Smart Search + Timeline + Map** — Full-text search with filters, timeline view, and GPS-plotted map
- **Personalized Reports** — AI-generated narrative summaries as beautiful standalone HTML pages
- **Tag Classification** — AI-powered classification of tags as people vs. topics

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLite + FTS5, Claude API
- **Frontend:** SvelteKit, D3.js, Leaflet.js

## Setup

```bash
# Backend
cd backend
pip install -e .
uvicorn rewind.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev -- --port 5173

# Or use the dev script to start both
./scripts/dev.sh
```

## Data

Export your Day One journal as JSON (zip format), then upload it through the Import page.

## Status

### Phase 1: Foundation ← current
- [x] Project scaffolding
- [x] Database schema (SQLite + FTS5)
- [x] Day One JSON parser
- [x] Basic import pipeline
- [x] Entry list API
- [x] SvelteKit shell with import + entry list

### Phase 2: Photos + Search
- [ ] Thumbnail generation
- [ ] FTS5 search with combined filters
- [ ] Timeline grouping
- [ ] Photo display in cards
- [ ] Virtual scrolling

### Phase 3: Tag Classification + Graph
- [ ] Claude tag classification
- [ ] Tag review UI
- [ ] Graph pre-computation
- [ ] Force-directed graph explorer

### Phase 4: Map + Reports
- [ ] Leaflet map view
- [ ] Claude report generation
- [ ] Report HTML template + preview

### Phase 5: Polish
- [ ] Dashboard stats
- [ ] SSE progress
- [ ] Entry detail modal
- [ ] Responsive layout
- [ ] Performance tuning
