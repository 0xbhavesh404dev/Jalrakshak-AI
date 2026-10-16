import pytest
@pytest.fixture(autouse=True)
def isolated_db(tmp_path,monkeypatch):
    from core import config,db
    monkeypatch.setattr(config,"DB_PATH",tmp_path/"test.sqlite3")
    monkeypatch.setattr(db,"DB_PATH",tmp_path/"test.sqlite3")
