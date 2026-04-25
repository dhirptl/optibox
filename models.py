from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


Position = Tuple[int, int, int, int, int]
# (aisle, side, x, y, z)


class ShuttleTaskType(str, Enum):
    INBOUND_CROSS_DOCK = "inbound_cross_dock"
    INBOUND_STORE_AND_PICK = "inbound_store_and_pick"
    OUTBOUND_ONLY = "outbound_only"
    RELOCATE = "relocate"


@dataclass(frozen=True)
class SimulationConfig:
    handling_seconds: int = 10
    cross_dock_handling_seconds: int = 20 # ask about if it is 10
    pallet_size: int = 12
    max_active_pallets: int = 8

    aisles: int = 4
    sides: int = 2
    x_max: int = 60
    y_levels: int = 8
    z_depth: int = 2 
    #everything is max and starts from 1

    @property
    def shuttle_count(self) -> int:
        return self.aisles * self.y_levels


@dataclass(frozen=True)
class Box:
    box_id: str
    source: str
    destination: str
    bulk_number: str

    @staticmethod
    def parse_box_id(raw_box_id: str) -> "Box":
        """
        Parse the 20-digit box identifier:
        - source:       7 digits
        - destination:  8 digits
        - bulk number:  5 digits
        """
        box_id = raw_box_id.strip()
        if len(box_id) != 20 or not box_id.isdigit():
            raise ValueError(
                f"Invalid box id '{raw_box_id}'. Expected exactly 20 digits."
            )
        return Box(
            box_id=box_id,
            source=box_id[0:7],
            destination=box_id[7:15],
            bulk_number=box_id[15:20],
        )


@dataclass
class Slot:
    aisle: int
    side: int
    x: int
    y: int
    z: int
    box: Optional[Box] = None

    @property
    def position(self) -> Position:
        return (self.aisle, self.side, self.x, self.y, self.z)

    @property
    def is_empty(self) -> bool:
        return self.box is None


@dataclass
class ShuttleTask:
    """
    One executable shuttle cycle unit.

    Decision lifecycle:
    1) At x=0, pick one inbound box from the incoming flow.
    2) Once inbound details are known, decide:
       - immediate cross-dock (drop at x=0), or
       - store while moving toward an outbound pick.
    3) Only for the store path, choose the outbound box/slot that will be
       picked and delivered in the same cycle.
    """

    task_type: ShuttleTaskType
    inbound_box: Optional[Box] = None
    # Set for store-and-pick and outbound-only tasks after selection.
    outbound_box: Optional[Box] = None
    # Where inbound will be stored if not immediately cross-docked.
    store_slot: Optional[Position] = None
    # Which already-stored box is targeted for pickup/delivery.
    pick_slot: Optional[Position] = None
    drop_to_head: bool = True
    # Duration budget captured when the task starts. Used for playback interpolation.
    total_seconds: int = 0
    remaining_seconds: int = 0


@dataclass
class Shuttle:
    shuttle_id: str
    aisle: int
    y: int
    current_x: int = 0
    carrying: Optional[Box] = None
    # Queue contains executable tasks only after inbound is identified and
    # the decision is made (cross-dock now vs store-then-pick outbound).
    queue: List[ShuttleTask] = field(default_factory=list)
    active_task: Optional[ShuttleTask] = None
    is_idle: bool = True

    def enqueue(self, task: ShuttleTask) -> None:
        self.queue.append(task)


@dataclass
class Pallet:
    destination: str
    reserved_box_ids: List[str] = field(default_factory=list)
    shipped_box_ids: List[str] = field(default_factory=list)
    is_active: bool = True

    @property
    def is_complete(self) -> bool:
        return len(self.shipped_box_ids) >= 12


@dataclass
class DispatcherState:
    active_pallets: Dict[str, Pallet] = field(default_factory=dict)
    reserved_inventory_by_destination: Dict[str, int] = field(default_factory=dict)


@dataclass
class Silo:
    slots: Dict[Position, Slot] = field(default_factory=dict)
    box_position: Dict[str, Position] = field(default_factory=dict)

    def get_slot(self, position: Position) -> Optional[Slot]:
        return self.slots.get(position)

    def place_box(self, position: Position, box: Box) -> None:
        slot = self.slots.get(position)
        if slot is None:
            raise ValueError(f"Unknown slot position: {position}")
        if not slot.is_empty:
            raise ValueError(f"Slot is occupied at {position}")
        slot.box = box
        self.box_position[box.box_id] = position

    def remove_box(self, position: Position) -> Box:
        slot = self.slots.get(position)
        if slot is None:
            raise ValueError(f"Unknown slot position: {position}")
        if slot.box is None:
            raise ValueError(f"No box in slot at {position}")
        box = slot.box
        slot.box = None
        self.box_position.pop(box.box_id, None)
        return box

    def find_box_position(self, box_id: str) -> Optional[Position]:
        return self.box_position.get(box_id)


def build_empty_silo(config: SimulationConfig) -> Silo:
    slots: Dict[Position, Slot] = {}
    for aisle in range(1, config.aisles + 1):
        for side in range(1, config.sides + 1):
            for x in range(1, config.x_max + 1):
                for y in range(1, config.y_levels + 1):
                    for z in range(1, config.z_depth + 1):
                        slot = Slot(aisle=aisle, side=side, x=x, y=y, z=z)
                        slots[slot.position] = slot
    return Silo(slots=slots)
