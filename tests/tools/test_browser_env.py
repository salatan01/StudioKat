"""Tests for the shared Chrome/Chromium path resolver."""

from __future__ import annotations

from tools.video.browser_env import resolve_chrome

_ENV_VARS = ("CHROME", "HYPERFRAMES_BROWSER_PATH", "REMOTION_BROWSER_EXECUTABLE")


def test_resolve_chrome_prefers_env(monkeypatch, tmp_path):
    fake = tmp_path / "my chrome"
    fake.write_text("#!/bin/sh\n")
    link = tmp_path / "link"
    link.symlink_to(fake)
    monkeypatch.setenv("CHROME", str(link))
    assert resolve_chrome() == str(link)


def test_resolve_chrome_env_fallback_order(monkeypatch, tmp_path):
    fake = tmp_path / "browser"
    fake.write_text("#!/bin/sh\n")
    monkeypatch.delenv("CHROME", raising=False)
    monkeypatch.setenv("HYPERFRAMES_BROWSER_PATH", str(fake))
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/chromium")
    assert resolve_chrome() == str(fake)


def test_resolve_chrome_ignores_missing_env_path(monkeypatch, tmp_path):
    for name in ("HYPERFRAMES_BROWSER_PATH", "REMOTION_BROWSER_EXECUTABLE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CHROME", str(tmp_path / "does-not-exist"))
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/chromium")
    assert resolve_chrome() == "/usr/bin/chromium"


def test_resolve_chrome_falls_back_to_path(monkeypatch):
    for name in _ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/chromium-browser")
    assert resolve_chrome() == "/usr/bin/chromium-browser"


def test_resolve_chrome_empty_when_none(monkeypatch):
    for name in _ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("shutil.which", lambda _: None)
    assert resolve_chrome() == ""
