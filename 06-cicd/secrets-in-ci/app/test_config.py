import importlib

import pytest


def load_config():
    import config
    return importlib.reload(config)


def test_config_reads_env(monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PASSWORD", "fake-test-value")
    monkeypatch.setenv("API_KEY", "fake-api-key")
    cfg = load_config()
    assert cfg.DB_HOST == "localhost"


def test_missing_secret_raises(monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.setenv("API_KEY", "fake-api-key")
    with pytest.raises(EnvironmentError):
        load_config()
