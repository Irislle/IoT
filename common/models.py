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

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TemperatureTelemetry":
        try:
            return cls(
                bn=str(payload["bn"]),
                ts=int(payload["ts"]),
                room_id=str(payload["room_id"]),
                temp_c=float(payload["temp_c"]),
                unit=str(payload.get("unit", "C")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid TemperatureTelemetry payload: {payload}") from exc


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

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AlertEvent":
        try:
            return cls(
                ts=int(payload["ts"]),
                room_id=str(payload["room_id"]),
                type=str(payload["type"]),
                level=str(payload["level"]),
                temp_c=float(payload["temp_c"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid AlertEvent payload: {payload}") from exc


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

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ActuatorState":
        try:
            return cls(
                ts=int(payload["ts"]),
                device=str(payload["device"]),
                room_id=str(payload["room_id"]),
                state=str(payload["state"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid ActuatorState payload: {payload}") from exc
