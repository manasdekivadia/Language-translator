# tests/test_samples.py
import cpp2py.parser as cppparser
from cpp2py.translator import translate_file
import os
import tempfile

def test_sample_translation():
    path = os.path.join(os.path.dirname(__file__), '..', 'input_examples', 'sample.cpp')
    tmp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
    tmp.close()
    translate_file(path, tmp.name)
    with open(tmp.name, 'r') as f:
        data = f.read()
    assert "for i in range(0, 3):" in data
    assert 'print("a is less")' in data or "print('a is less')" in data
