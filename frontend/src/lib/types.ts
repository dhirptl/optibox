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
  capacity: 12;
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
