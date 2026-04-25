
📋 OPTIBOX — DETAILED NUMBERED CHECKLIST

🐍 BACKEND — Python (existing repo: dhirptl/optibox)
B1. Existing files (DO NOT MODIFY — only consume)
models.py — provides SimulationConfig, Box, Slot, Shuttle, Pallet, Silo, DispatcherState, ShuttleTask, Position
state_loader.py — provides preload_silo_from_csv(csv_path, silo, strict_positions)
dispatch.py — pallet management logic (algorithm team owns)
slot_heuristic.py — placement decisions (algorithm team owns)
shuttle_runner.py — step_all_shuttles returns List[ShuttleStepResult]
main.py — build_initial_state, run_tick, run_tick_batch
inbound_generator.py — generates 1000 boxes/hour stream during sim (algorithm team owns, leave alone)
B2. NEW file — initial_state_generator.py (Olivia + Claude write this)
Imports: csv, random, argparse, os
Constant SOURCE_CODE = "3055769" (7 digits)
Constant DESTINATIONS = ["01000110", "01001120", "01002130", "01003140", "01004150", "01005160", "01006170", "01007180", "01008190", "01009210", "01010220", "01011230", "01012240", "01013250", "01014260", "01015270", "01016280", "01017290", "01018310", "01019320"] (20 unique 8-digit)
Constant AISLES = 4, SIDES = 2, X_MAX = 60, Y_LEVELS = 8, Z_DEPTH = 2
Constant MAX_CAPACITY = 4 × 2 × 60 × 8 × 2 = 7680
Function generate_box_code(destination: str) -> str:
13a. Generates 5-digit random bulk number (10000–99999)
13b. Returns SOURCE_CODE + destination + bulk = 20 digits
Function format_position(aisle, side, x, y, z) -> str:
14a. Returns 11-digit string with zero-padding: f"{aisle:02d}{side:02d}{x:03d}{y:02d}{z:02d}"
14b. Example: (1,1,1,1,1) → "01010010101"
Function build_all_positions() -> List[tuple]:
15a. Builds all 7,680 positions in canonical order
15b. Loops aisle 1→4, side 1→2, x 1→60, y 1→8, z 1→2
15c. Returns list of (aisle, side, x, y, z) tuples
Function build_tunnels() -> List[tuple]:
16a. Builds list of 3,840 (aisle, side, x, y) tuples
16b. Each tunnel = one shelf cell holding 2 boxes (Z=1 + Z=2)
Function create_initial_state_csv(num_boxes: int, output_path: str) -> dict:
17a. Validates 0 <= num_boxes <= 7680, raises ValueError otherwise
17b. Calls build_tunnels(), shuffles randomly with random.shuffle()
17c. Iterates shuffled tunnels: fills Z=2 first (always), then Z=1 of same tunnel
17d. Stops after num_boxes boxes placed
17e. Stores (position_tuple, box_code) for each placed box in a dict
17f. Builds full CSV: ALL 7,680 positions in canonical order
17g. Empty slots written as "<posicion>," (blank etiqueta)
17h. Filled slots written as "<posicion>,<etiqueta>"
17i. Creates output directory if it doesn't exist
17j. Writes file with header posicion,etiqueta
17k. Returns stats dict: {"num_boxes": N, "filename": path, "fill_pct": float}
CLI entry point with argparse:
18a. --num-boxes (required int)
18b. --output (default: frontend/public/data/silo_setup.csv)
18c. Runs create_initial_state_csv() and prints stats
B3. NEW file — server.py (Flask wrapper, ~50 lines)
Imports: flask, flask_cors, initial_state_generator
Flask app with CORS enabled for http://localhost:5173
Endpoint POST /api/randomize:
21a. Body: {"num_boxes": int}
21b. Validates input
21c. Calls initial_state_generator.create_initial_state_csv(num_boxes, output_path)
21d. Returns {"success": True, "num_boxes": N, "csv_path": "...", "fill_pct": ...}
21e. Returns 400 with error message on bad input
Endpoint POST /api/reset:
22a. Calls create_initial_state_csv(0, output_path) — writes empty silo (all blank etiqueta)
22b. Returns {"success": True}
Endpoint GET /api/health:
23a. Returns {"status": "ok"}
Runs on localhost:8000 with app.run(port=8000, debug=True)
CLI: python server.py to start
B4. (Phase 2 — LATER, not now) Simulation runner
NEW endpoint POST /api/run-simulation — wraps main.py's run_tick loop
Loads silo from frontend/public/data/silo_setup.csv via build_initial_state(csv_path=...)
Records events from each tick into a simulation_log.json
Returns metrics + event log path

⚛️ FRONTEND — React + TypeScript + Tailwind (/frontend folder inside repo)
F1. Project setup (Cursor terminal commands)
mkdir frontend && cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p
Create frontend/public/data/ directory
Verify npm run dev starts at http://localhost:5173
F2. Tailwind config (tailwind.config.js)
Custom color palette in theme.extend.colors:
37a. bg-cream: #FAF7F2
37b. border-soft: #E8E0D4
37c. slot-empty: #F0EAE0
37d. box-resting: #D4C4A8
37e. box-active: #8B6F47
37f. shuttle: #5C4A38
37g. pallet-fill: #B8A082
37h. pallet-empty: #F5F0E8
37i. text-primary: #2A2520
37j. text-secondary: #888073
37k. accent: #8B6F47
37l. status-green: #5CB874
Custom font families: sans (Inter), mono (JetBrains Mono)
Content paths include all src/**/*.{ts,tsx}
F3. Fonts loaded in index.html
Inter from Google Fonts (weights 400, 500, 600, 700)
JetBrains Mono from Google Fonts (weights 400, 500)
F4. TypeScript types (src/lib/types.ts)
Position = { aisle: number; side: 1 | 2; x: number; y: number; z: 1 | 2 }
Box = { box_id: string; source: string; destination: string; bulk: string }
Slot = { position: Position; box: Box | null }
SiloState = Map<string, Slot> keyed by 11-digit posicion string
Pallet = { slot_id: number; robot_id: 1 | 2; destination: string | null; filled: number; capacity: 12 }
EventLogEntry = { t: number; type: string; message: string } (Phase 2)
F5. Utilities (src/lib/parsing.ts)
Function parsePositionString(s: string): Position:
48a. Validates length === 11
48b. Extracts aisle (0–2), side (2–4), x (4–7), y (7–9), z (9–11)
Function formatPositionString(p: Position): string — inverse of #48
Function parseBoxId(s: string): Box:
50a. Validates length === 20
50b. Extracts source (0–7), destination (7–15), bulk (15–20)
Function parseSiloCsv(csvText: string): SiloState:
51a. Splits by newline, skips header row
51b. For each line: splits on ,, parses position + (optional) box
51c. Returns Map keyed by posicion string
Function getSlotsForY(silo: SiloState, y: number): Slot[] — filters by Y level
Function getSlotsForAisleSideY(silo, aisle, side, y): Slot[] — for rendering one row
F6. API client (src/lib/api.ts)
Constant API_BASE = "http://localhost:8000"
Function randomizeSilo(numBoxes: number): Promise<RandomizeResponse> — POST /api/randomize
Function resetSilo(): Promise<{success: boolean}> — POST /api/reset
Function healthCheck(): Promise<boolean> — GET /api/health, returns true/false
Function fetchSiloState(): Promise<SiloState> — fetches /data/silo_setup.csv (Vite serves this), parses, returns
F7. Hooks (src/hooks/)
useSiloState() — manages silo state, exposes refetch()
useYLevel() — selected Y-level (default Y=4), setY()
useApi() — wraps API calls with loading/error states
useSelectedBox() — for tooltip, selectBox(box) / clearSelection()
useSelectedShuttle() — for shuttle inspector
useRightPanelTab() — tracks which right-panel tab is active: "pallets" or "events"
useBackendHealth() — checks backend on mount, polls every 5s
F8. Components — Top Bar (src/components/TopBar.tsx) ~70px tall
Logo "OPTIBOX" (bold sans, all caps) + tagline "warehouse flow simulator"
Hero metric: "FULL PALLETS" % (large 36px)
Hero metric: "PALLETS COMPLETED" count (large 36px)
Hero metric: "AVG TIME / PALLET" (large 36px)
Sim timer "00:00:00 / 10:00:00" (monospace)
Speed pills: 1× / 2× / 5× / 10× / 30× (active filled dark) — disabled in Phase 1
Play/Pause button — disabled in Phase 1
Reset button — calls api.reset() then refetches CSV
Softer styling: less rigid borders, more whitespace, friendlier feel (per Olivia's feedback)
F9. Components — Y-Level Selector (src/components/YLevelSelector.tsx) ~50px
Centered label "VIEWING LEVEL"
8 pills: Y=1, Y=2, Y=3, Y=4, Y=5, Y=6, Y=7, Y=8
Active Y filled #8B6F47, white text
Inactive: light cream bg, grey text
Default selected: Y=4
Clicking a pill triggers Y-level change
F10. Components — Main Canvas (src/components/SiloCanvas.tsx)
Centered horizontally on page (not left-anchored — per Olivia's correction)
Container max-width to keep it readable
4 aisle strips, stacked vertically:
83a. Aisle 01 (top)
83b. Aisle 02
83c. Aisle 03
83d. Aisle 04 (bottom)
Each aisle strip layout:
84a. Aisle label "AISLE 01" (or 02/03/04) — positioned to LEFT of the strip
84b. Side 01 row (60 cells horizontally) on top
84c. Corridor row in middle (light beige strip with shuttle dot)
84d. Side 02 row (60 cells horizontally) on bottom
84e. NO right-edge fill % indicator (removed per Olivia's correction)
Each cell renders 2 box squares side-by-side:
85a. Side 01 row: Z=2 (outer/wall) on far side, Z=1 (inner/aisle) closer to corridor
85b. Side 02 row: Z=1 (inner/aisle) closer to corridor, Z=2 (outer/wall) on far side
Box square uniform sizing — all boxes exactly 12×12px or 14×14px (per Olivia's "make them symmetrical" feedback)
Cells aligned in a strict grid — every X position takes the same horizontal space (no flex-wrap or organic placement)
Box rendering rules:
88a. Empty slot: faint outline #F0EAE0, no fill
88b. Resting box (any destination): solid fill #D4C4A8
88c. Active/moving box (Phase 2): solid fill #8B6F47 with subtle glow
Shuttle rendering:
89a. Small dark brown rectangle #5C4A38 (12×8px)
89b. Positioned in corridor at current X
89c. All 4 shuttles for selected Y across all 4 aisles visible simultaneously
89d. Initial state: all shuttles at X=0 (head, leftmost position)
X-axis ruler at bottom of each aisle's Side 02 row:
90a. Faint marks at X=0, X=10, X=20, X=30, X=40, X=50, X=60
90b. Marks vertically aligned with the actual X position columns (per Olivia's correction — currently misaligned)
90c. Small grey font, monospace
Click any box → tooltip popup
Click any shuttle → highlight + small task panel
Click corridor or empty area → clears selection
F11. Components — Box Tooltip (src/components/BoxTooltip.tsx)
Floating popup, white card, soft shadow
Shows full 20-digit box_id (monospace, with destination digits 7-15 visually highlighted)
Shows Destination (8-digit, monospace)
Shows Position: "Aisle 2 / Side 01 / X=5 / Y=3 / Z=1"
Shows "Loaded at: --:--:--" — note: only populated during sim Phase 2 (in Phase 1 shows placeholder)
Close button (X) or click outside to dismiss
F12. Components — Right Panel with TABS (src/components/RightPanel.tsx) ~280px wide
Tab bar at top of panel with 2 tabs: - 100a. "Pallet Slots" (default active) - 100b. "Event Log"
Active tab styled with underline + dark text; inactive grey
Click tab → switches the panel content
No more collapsible drawer chevron arrow (per Olivia's correction)
F13. Components — Pallet Slots Tab Content
Header inside tab: "8 ACTIVE SLOTS"
Sub-label "ROBOT 1" → 4 pallet cards
Sub-label "ROBOT 2" → 4 pallet cards
Each pallet card (~80px tall): - 107a. Slot number "01" (bold, left) - 107b. Destination code (monospace, right) — empty placeholder when no destination - 107c. 4×3 grid of 12 squares - 107d. Empty squares: #F5F0E8 - 107e. Filled squares: #B8A082 - 107f. Fill counter "X/12" right-aligned at bottom
Initial state: all 8 slots show "AWAITING DESTINATION", 0/12
(Phase 2) When 12/12: ship animation slides card right + fades, then resets to "AWAITING DESTINATION"
F14. Components — Event Log Tab Content
Header inside tab: "RECENT EVENTS"
Scrollable list of events, newest at top, max ~50 visible
Each event row: - 112a. Timestamp (monospace, grey, e.g. "00:04:32") - 112b. Event type as small caps tag - 112c. Message body (truncated box IDs to last 6 digits)
Auto-updates as simulation runs (Phase 2)
Initial state (Phase 1): "No events yet. Start simulation to see activity."
F15. Components — Bottom Bar (src/components/BottomBar.tsx) ~80px
Live action banner (left, ~60% width): - 115a. Monospace 20px font (per Olivia's correction — was 14px) - 115b. Single line, auto-updating with most recent action - 115c. Green pulsing dot indicator on left - 115d. Initial state: "Awaiting simulation start..."
Scrub bar (right, ~40% width): - 116a. Functional draggable horizontal track (not just decorative — per Olivia's correction) - 116b. Filled portion shows progress - 116c. Draggable thumb to seek - 116d. Click anywhere on track jumps to that point - 116e. Time display "00:00 / 10:00" (monospace) to the right - 116f. In Phase 1 (no sim yet): scrub bar disabled with "—" placeholder - 116g. In Phase 2: drag updates current sim time, replays events to that point
F16. Components — Start Modal (src/components/StartModal.tsx)
Shown on first load, dimmed backdrop, centered card
Title: "OPTIBOX" large
Subtitle: "Warehouse Flow Simulator"
Body text: "1,000 boxes per hour. 32 shuttles. 8 pallet slots."
Number input field: "How many boxes to populate the silo?" - 121a. min=0, max=7680 - 121b. Default value: 2500 - 121c. Helper text: "Try 1000–4000 for best visualization"
Button: "🎲 Randomize Silo" - 122a. Disabled while loading - 122b. Calls api.randomizeSilo(numBoxes) - 122c. On success: closes modal, refetches CSV, renders boxes - 122d. On error: shows error message inline
Re-roll: after randomize, judge can press button again to regenerate
Button: "▶ Start Simulation" — disabled in Phase 1, enabled in Phase 2
F17. Components — Backend Offline Banner
If useBackendHealth() returns false on mount, show banner at top
Message: "Backend not running. Start it with: python server.py"
Banner uses subtle warning color, dismissible
F18. Mock data (development scaffolding)
File frontend/public/data/silo_setup_mock.csv with ~1500 randomly placed boxes (committed to repo)
Toggle in dev mode: load mock CSV when backend is offline (so frontend works standalone)
F19. App composition (src/App.tsx)
Layout: TopBar + YLevelSelector + (SiloCanvas + RightPanel) + BottomBar
Mounts StartModal on first load
Health check on mount, sets banner state if backend offline
Global state hooks composition

📁 INTEGRATION CONTRACT (frontend ↔ backend)
What the frontend expects from backend:
CSV file at /data/silo_setup.csv (Vite serves from frontend/public/data/)
CSV format: header posicion,etiqueta + 7,680 rows
posicion = 11-digit zero-padded string (Aisle Side X Y Z)
etiqueta = blank for empty slot, or 20-digit box code
HTTP server at localhost:8000 exposing 3 endpoints
What the backend receives from frontend:
POST /api/randomize with {"num_boxes": <number>}
POST /api/reset (no body)
GET /api/health (no body)
File system layout:
optibox/
├── (existing Python files — unchanged)
├── initial_state_generator.py   ← #8-18 NEW
├── server.py                    ← #19-25 NEW
└── frontend/                    ← #30-133 NEW
    ├── public/data/
    │   ├── silo_setup.csv       ← Python writes, frontend reads
    │   └── silo_setup_mock.csv  ← static for offline dev
    ├── src/
    │   ├── App.tsx
    │   ├── components/
    │   ├── hooks/
    │   └── lib/
    └── (config files)


✅ BUILD ORDER
Phase 1 (today's MVP — what we ship for the demo)
Backend: write #8-25 (initial_state_generator.py + server.py)
Frontend: write #30-133 (full UI shell + CSV reading)
Test end-to-end: judge enters number → CSV generates → silo renders
Phase 2 (after teammate's algorithm is ready)
Backend: #26-29 (run-simulation endpoint)
Frontend: animation engine, live metrics, working scrub bar with replay, pallet slot fill animations

