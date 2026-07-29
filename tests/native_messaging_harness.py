import json
import struct
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import BinaryIO


def exchange_native_message(
    host_path: Path,
    request: dict[str, str],
) -> dict[str, str]:
    process = subprocess.Popen(
        [host_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("native host pipes were not created")

    payload = json.dumps(request).encode()
    process.stdin.write(struct.pack("<I", len(payload)) + payload)
    process.stdin.flush()

    executor = ThreadPoolExecutor(max_workers=1)
    response = executor.submit(read_native_message, process.stdout)
    try:
        return response.result(timeout=2)
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait()
        executor.shutdown()
        process.stdin.close()
        process.stdout.close()


def read_native_message(output: BinaryIO) -> dict[str, str]:
    message_size = struct.unpack("<I", read_exactly(output, 4))[0]
    return json.loads(read_exactly(output, message_size))


def read_exactly(stream: BinaryIO, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        chunk = stream.read(length - len(data))
        if not chunk:
            raise EOFError("native host closed the pipe")
        data.extend(chunk)
    return bytes(data)
