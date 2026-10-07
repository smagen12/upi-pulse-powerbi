"""Regression checks for failures that previously escaped the pipeline."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import build_project
import fetch_data


class PipelineTests(unittest.TestCase):
    def test_nonfinite_numbers(self):
        for value in ('NaN', 'inf', '-inf'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_project.num(value)

    def test_bad_inputs_do_not_write_outputs(self):
        cases = ('missing_month', 'zero_volume', 'invalid_rate', 'unknown_bank', 'wrong_month')
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copytree(build_project.R / 'data/raw', root / 'data/raw')
                path = root / 'data/raw/remitter-2026-03.json'
                payload = json.loads(path.read_text(encoding='utf-8'))
                row = payload['data']['results'][0]
                if case == 'missing_month':
                    path.unlink()
                else:
                    key, value = {
                        'zero_volume': ('total_volume_in_mn', '0'),
                        'invalid_rate': ('td_percent', '101'),
                        'unknown_bank': ('upi_remitter_banks', 'Unknown bank'),
                        'wrong_month': ('year', '2025'),
                    }[case]
                    row[key] = value
                    path.write_text(json.dumps(payload), encoding='utf-8')
                with patch.object(build_project, 'R', root), patch.object(build_project, 'write') as write, patch.object(build_project, 'csvout') as csvout:
                    with self.assertRaises(ValueError):
                        build_project.main()
                    write.assert_not_called()
                    csvout.assert_not_called()

    def test_download_failure_preserves_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / 'data/raw'
            raw.mkdir(parents=True)
            snapshot = raw / 'remitter-2024-04.json'
            snapshot.write_bytes(b'existing snapshot')
            with patch.object(fetch_data, 'root', root), patch.object(fetch_data, 'f', side_effect=RuntimeError('offline')):
                with self.assertRaises(RuntimeError):
                    fetch_data.main()
            self.assertEqual(snapshot.read_bytes(), b'existing snapshot')
            self.assertEqual(list(raw.iterdir()), [snapshot])


if __name__ == '__main__':
    unittest.main()
