# OptiBox

OptiBox solves the **storage + delivery flow problem** in a multi-shuttle warehouse.
We built a greedy routing and dispatch system that receives boxes, stores them intelligently, and ships them through active pallet destinations, with a full visual playback UI.

## Inspiration

We were inspired by the practical impact of warehouse optimization and by the challenge itself.  
The constraints are realistic (limited shuttles, lane geometry, pallet limits), so this was both an algorithmic and product design challenge.

## What It Does

- Simulates **32 shuttles** operating in a silo layout.
- Routes inbound boxes to either:
  - immediate cross-dock delivery, or
  - storage + pickup flow on the same route.
- Tracks pallet progression and completion over time.
- Produces a timeline that can be replayed in a React frontend.
- Lets users randomize initial load, run simulation, scrub through time, and inspect events/metrics.

## How We Built It

- **Backend (Python + Flask)**
  - Core simulation state machine
  - Shuttle task execution logic
  - Dispatch and pallet lifecycle rules
  - CSV-based initial state generation/loading
  - Timeline/log export for frontend playback
- **Frontend (React + TypeScript + Vite + Tailwind)**
  - Playback controls (play/pause, speeds, scrubber)
  - Silo grid visualization
  - Event log + pallet panel
  - Health/error handling + deterministic replay UX

## Challenges We Ran Into

- Balancing multiple constraints at once:
  - route efficiency,
  - storage placement,
  - pallet activation/completion logic.
- Keeping simulation deterministic while still being interactive.
- Translating backend state transitions into smooth visual playback.
- Handling sparse box updates and debugging visual “no movement” cases.
- Keeping frontend and backend payload contracts aligned as features evolved.

## Accomplishments

- Built a working greedy algorithm that returns actionable simulation output.
- Delivered a complete end-to-end product (backend + visualization).
- Added scrubbing and explainability features so behavior is understandable, not a black box.

## What We Learned

- How to manage complex warehouse constraints with clear state transitions.
- How important data contracts are when frontend playback depends on backend tick data.
- How to collaborate quickly under hackathon time pressure.

## What's Next

- Improve routing heuristics and benchmark throughput.
- Add richer visual analytics overlays.
- Expand export/reporting for post-run analysis.

---

## Tech Stack

### Core
- Python
- Flask / Flask-CORS
- React
- TypeScript
- Vite
- Tailwind CSS

### Data + Protocol
- CSV (initial state + mock data)
- JSON (simulation timeline/log output)
- REST API

### Tooling
- Node.js + npm
- ESLint
- Git + GitHub
- Cursor / AI-assisted coding workflows

---

## Repository Setup

### 1) Clone the repository

```bash
git clone <your-repo-url>
cd optibox
```

### 2) Install backend dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Run the Project

### Start backend (Terminal 1)

```bash
source .venv/bin/activate
python server.py
```

Backend default: `http://127.0.0.1:8000`

### Start frontend (Terminal 2)

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend default: `http://127.0.0.1:5173`

---

## Frontend Scripts

Run from `frontend/`:

```bash
npm run dev
npm run build
npm run lint
npm run preview
```

---

## Backend API (High Level)

- `GET /api/health`  
  Backend status.

- `POST /api/randomize`  
  Generate randomized silo CSV from `num_boxes`.

- `POST /api/reset`  
  Reset silo state.

- `POST /api/run-simulation`  
  Run simulation and return timeline + metrics + events.

---

## Demo Guide

See [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for a structured 3-minute walkthrough.

---

## Project Notes

- Architecture/design notes: [`docs/PLAN.md`](docs/PLAN.md)
