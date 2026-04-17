import os
import tempfile
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import password_manager as pm

def test_generate_password():
    pwd = pm.generate_password(12, True, True, True)
    assert len(pwd) == 12

def test_derive_key():
    salt = b'salt123456789012'
    key1 = pm.derive_key_from_password("master", salt)
    key2 = pm.derive_key_from_password("master", salt)
    assert key1 == key2
    key3 = pm.derive_key_from_password("other", salt)
    assert key1 != key3

def test_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        original_data = pm.DATA_FILE
        original_salt = pm.SALT_FILE
        pm.DATA_FILE = pm.Path(tmpdir) / "passwords.enc"
        pm.SALT_FILE = pm.Path(tmpdir) / "salt"
        try:
            data = {"test": "secret"}
            pm.save_data(data, "mypassword")
            loaded = pm.load_data("mypassword")
            assert loaded == data
            assert pm.load_data("wrong") is None
        finally:
            pm.DATA_FILE = original_data
            pm.SALT_FILE = original_salt