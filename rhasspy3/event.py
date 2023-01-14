import asyncio
import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, IO

_TYPE = "type"
_DATA = "data"
_PAYLOAD_LENGTH = "payload_length"
_NEWLINE = "\n".encode()


@dataclass
class Event:
    type: str
    data: Optional[Dict[str, Any]] = None
    payload: Optional[bytes] = None


class Eventable(ABC):
    @abstractmethod
    def event(self) -> Event:
        pass

    @staticmethod
    @abstractmethod
    def is_type(event_type: str) -> bool:
        pass


async def async_read_event(reader: asyncio.StreamReader) -> Optional[Event]:
    json_line = await reader.readline()
    if not json_line:
        return None

    event_dict = json.loads(json_line)
    payload_length = event_dict.get(_PAYLOAD_LENGTH)

    payload: Optional[bytes] = None
    if payload_length is not None:
        payload = await reader.readexactly(payload_length)

    return Event(type=event_dict[_TYPE], data=event_dict.get(_DATA), payload=payload)


async def async_write_event(event: Event, writer: asyncio.StreamWriter):
    event_dict: Dict[str, Any] = {_TYPE: event.type, _DATA: event.data}
    if event.payload:
        event_dict[_PAYLOAD_LENGTH] = len(event.payload)

    json_line = json.dumps(event_dict, ensure_ascii=False)
    writer.writelines((json_line.encode(), _NEWLINE))

    if event.payload:
        writer.write(event.payload)

    await writer.drain()


def read_event(reader: Optional[IO[bytes]] = None) -> Optional[Event]:
    if reader is None:
        reader = sys.stdin.buffer

    json_line = reader.readline()

    if not json_line:
        return None

    event_dict = json.loads(json_line)
    payload_length = event_dict.get(_PAYLOAD_LENGTH)

    payload: Optional[bytes] = None
    if payload_length is not None:
        payload = reader.read(payload_length)

    return Event(type=event_dict[_TYPE], data=event_dict.get(_DATA), payload=payload)


def write_event(event: Event, writer: Optional[IO[bytes]] = None):
    if writer is None:
        writer = sys.stdout.buffer

    event_dict: Dict[str, Any] = {_TYPE: event.type, _DATA: event.data}
    if event.payload:
        event_dict[_PAYLOAD_LENGTH] = len(event.payload)

    json_line = json.dumps(event_dict, ensure_ascii=False)
    writer.writelines((json_line.encode(), _NEWLINE))

    if event.payload:
        writer.write(event.payload)

    writer.flush()