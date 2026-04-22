import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import patch


class ConfigTests(unittest.TestCase):
    def test_vercel_uses_tmp_data_dir_by_default(self):
        with patch.dict(os.environ, {"VERCEL": "1"}, clear=True):
            import config

            reloaded = importlib.reload(config)

        self.assertEqual(reloaded.OUTPUT_DIR, Path("/tmp/avori-discovery"))
        importlib.reload(config)

    def test_avori_data_dir_overrides_default(self):
        with patch.dict(os.environ, {"AVORI_DATA_DIR": "/tmp/custom-avori"}, clear=True):
            import config

            reloaded = importlib.reload(config)

        self.assertEqual(reloaded.OUTPUT_DIR, Path("/tmp/custom-avori"))
        importlib.reload(config)


if __name__ == "__main__":
    unittest.main()
