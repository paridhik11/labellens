"""API entry points remain importable when native CV packages are absent."""
from __future__ import annotations

import subprocess
import sys

from src.cv._optional import LazyModule, deferred


def test_deferred_helpers() -> None:
    """A module proxy and function wrapper preserve normal Python call behavior."""
    assert LazyModule('math').sqrt(9) == 3
    assert deferred('math', 'pow')(2, 3) == 8


def test_extractor_without_cv_packages() -> None:
    """Simulate minimal CI in a fresh process, including NumPy being unavailable."""
    program = '''
import sys, importlib.abc
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'cv2','numpy','PIL','zxingcpp','rapidocr_onnxruntime','reportlab'}:
            raise ModuleNotFoundError('blocked optional dependency: '+fullname)
sys.meta_path.insert(0, Block())
from src.cv.extract import extract_label
from src.gen.medicine import load_medicine_corpus
assert callable(extract_label) and callable(load_medicine_corpus)
assert 'cv2' not in sys.modules
'''
    result = subprocess.run([sys.executable, '-c', program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
