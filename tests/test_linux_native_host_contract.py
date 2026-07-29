import unittest
from pathlib import Path

from native_messaging_harness import exchange_native_message


class LinuxNativeHostContractTest(unittest.TestCase):
    def test_responds_without_waiting_for_stdin_to_close(self) -> None:
        host_path = Path(__file__).parents[1] / "native-host/linux/main.py"

        response = exchange_native_message(
            host_path,
            {"command": "unsupported"},
        )

        self.assertEqual(response, {"error": "unsupported command"})


if __name__ == "__main__":
    unittest.main()
