import json
import struct
import unittest
from io import BytesIO

from chrome_vertical_tabs_toggle_linux.native_messaging import (
    read_command,
    write_response,
)


class NativeMessagingTest(unittest.TestCase):
    def test_reads_toggle_command(self) -> None:
        input_stream = encoded_message({"command": "toggle"})

        self.assertEqual(read_command(input_stream), "toggle")

    def test_reads_collapse_command(self) -> None:
        input_stream = encoded_message({"command": "collapse"})

        self.assertEqual(read_command(input_stream), "collapse")

    def test_rejects_unknown_command(self) -> None:
        input_stream = encoded_message({"command": "expand"})

        with self.assertRaisesRegex(ValueError, "unsupported command"):
            read_command(input_stream)

    def test_reads_a_fragmented_message(self) -> None:
        input_stream = FragmentedStream(encoded_message({"command": "toggle"}).read())

        self.assertEqual(read_command(input_stream), "toggle")

    def test_writes_framed_response(self) -> None:
        output_stream = BytesIO()

        write_response(output_stream, {"state": "collapsed"})

        output_stream.seek(0)
        message_size = struct.unpack("<I", output_stream.read(4))[0]
        self.assertEqual(
            json.loads(output_stream.read(message_size)), {"state": "collapsed"}
        )


def encoded_message(message: dict[str, str]) -> BytesIO:
    payload = json.dumps(message).encode()
    return BytesIO(struct.pack("<I", len(payload)) + payload)


class FragmentedStream(BytesIO):
    def read(self, size: int = -1) -> bytes:
        return super().read(min(size, 1))


if __name__ == "__main__":
    unittest.main()
