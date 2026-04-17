import os
import tempfile
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scaffold import parse_structure, create_structure

def test_parse_simple_structure():
    text = """my_project
├── src/
│   ├── main.py
│   └── utils/
└── README.md"""
    root_dir, structure = parse_structure(text)
    assert root_dir == "my_project"
    assert (0, "src/") in structure
    assert (1, "main.py") in structure
    assert (1, "utils/") in structure
    assert (0, "README.md") in structure

def test_create_structure():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = os.path.join(tmpdir, "test_proj")
        structure = [
            (0, "src/"),
            (1, "main.py"),
            (0, "README.md")
        ]
        create_structure(root, structure)
        assert os.path.isdir(root)
        assert os.path.isdir(os.path.join(root, "src"))
        assert os.path.isfile(os.path.join(root, "src", "main.py"))
        assert os.path.isfile(os.path.join(root, "README.md"))