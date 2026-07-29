import json
import struct
from typing import BinaryIO, NewType

NativeCommand = NewType("NativeCommand", str)
TOGGLE_COMMAND = "toggle"
COLLAPSE_COMMAND = "collapse"
SUPPORTED_COMMANDS = frozenset((TOGGLE_COMMAND, COLLAPSE_COMMAND))


def read_command(input_stream: BinaryIO) -> NativeCommand:
    message_size = struct.unpack("<I", read_exactly(input_stream, 4))[0]
    request = json.loads(read_exactly(input_stream, message_size))
    command = request["command"]
    if command not in SUPPORTED_COMMANDS:
        raise ValueError("unsupported command")
    return NativeCommand(command)


def read_exactly(input_stream: BinaryIO, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        chunk = input_stream.read(length - len(data))
        if not chunk:
            raise EOFError("invalid Native Messaging request")
        data.extend(chunk)
    return bytes(data)


def write_response(output_stream: BinaryIO, response: dict[str, str]) -> None:
    payload = json.dumps(response).encode()
    output_stream.write(struct.pack("<I", len(payload)))
    output_stream.write(payload)
    output_stream.flush()
