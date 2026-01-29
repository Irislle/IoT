from __future__ import annotations

"""Shared data models for JSON payloads exchanged across services."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class TemperatureTelemetry:
    bn: str
    ts: int
    room_id: str
    temp_c: float
    unit: str = "C"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bn": self.bn,
            "ts": self.ts,
            "room_id": self.room_id,
            "temp_c": self.temp_c,
            "unit": self.unit,
        }


@dataclass
class AlertEvent:
    ts: int
    room_id: str
    type: str
    level: str
    temp_c: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts": self.ts,
            "room_id": self.room_id,
            "type": self.type,
            "level": self.level,
            "temp_c": self.temp_c,
        }


@dataclass
class ActuatorState:
    ts: int
    device: str
    room_id: str
    state: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts": self.ts,
            "device": self.device,
            "room_id": self.room_id,
            "state": self.state,
        }
