import os
import tempfile
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clean import clean_directory

def test_clean_pycache():
    with tempfile.TemporaryDirectory() as tmpdir:
        pycache = os.path.join(tmpdir, "__pycache__")
        os.makedirs(pycache)
        open(os.path.join(pycache, "test.pyc"), 'w').close()
        dirs, files = clean_directory(tmpdir, dry_run=False, include_venv=False)
        assert not os.path.exists(pycache)
        assert len(dirs) == 1
        assert len(files) == 0

def test_dry_run_does_not_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        pycache = os.path.join(tmpdir, "__pycache__")
        os.makedirs(pycache)
        dirs, files = clean_directory(tmpdir, dry_run=True, include_venv=False)
        assert os.path.exists(pycache)
