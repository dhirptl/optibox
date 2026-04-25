export type Position = {
  aisle: number;
  side: 1 | 2;
  x: number;
  y: number;
  z: 1 | 2;
};

export type Box = {
  box_id: string;
  source: string;
  destination: string;
  bulk: string;
};

export type Slot = {
  position: Position;
  box: Box | null;
};

export type SiloState = Map<string, Slot>;

export type Pallet = {
  slot_id: number;
  robot_id: 1 | 2;
  destination: string | null;
  filled: number;
  capacity: number;
};

export type EventLogEntry = {
  t: number;
  type: string;
  message: string;
};

export type RandomizeResponse = {
  success: boolean;
  num_boxes: number;
  csv_path: string;
  fill_pct: number;
};

export type SimulationMetrics = {
  full_pallets_out_of_8: number;
  full_pallet_pct?: number;
  pallets_completed: number;
  avg_time_per_pallet: number;
};

export type ShuttleSnapshot = {
  shuttle_id: string;
  aisle: number;
  y: number;
  x: number;
  task_type: string | null;
};

export type SimulationTimelineFrame = {
  t: number;
  metrics: SimulationMetrics;
  pallet_slots: Pallet[];
  shuttles: ShuttleSnapshot[];
  grid_changes?: GridChange[];
  action_message: string;
  event_count: number;
  final_metrics?: SimulationMetrics;
};

export type GridChange = {
  position: string;
  before: Box | null;
  after: Box | null;
};

export type SimulationEvent = EventLogEntry & {
  destination?: string;
  shuttle_id?: string;
  task_type?: string;
  box_id?: string;
};

export type RunSimulationResponse = {
  success: boolean;
  duration_seconds: number;
  metrics: SimulationMetrics;
  final_metrics: SimulationMetrics;
  events: SimulationEvent[];
  timeline: SimulationTimelineFrame[];
  log_path: string;
};
