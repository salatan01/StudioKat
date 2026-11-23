"""Both local-runtime adapters must handle child processes the same way.

`editor_render` and `faceless_render` each own a copy of the job/preview process
handling (design S2: the copy drifted). These tests pin the two behaviours that
diverged — zombie-aware liveness and reaping on terminate — so a change to one
adapter that is not mirrored in the other fails here.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from tools.video.editor_render import EditorRender
from tools.video.editor_render import _pid_alive as editor_pid_alive
from tools.video.faceless_render import FacelessRender
from tools.video.faceless_render import _pid_alive as faceless_pid_alive

ADAPTERS = pytest.mark.parametrize(
    ("cls", "pid_alive"),
    [
        pytest.param(EditorRender, editor_pid_alive, id="editor"),
        pytest.param(FacelessRender, faceless_pid_alive, id="faceless"),
    ],
)


def _proc_state(pid: int) -> str | None:
    """Linux process state from /proc, or None once the pid is gone."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    return stat.rsplit(")", 1)[1].split(None, 1)[0]


def test_proc_state_reports_a_zombie():
    """Guard the test helper itself: a fresh fork becomes a zombie, then clears."""
    pid = os.fork()
    if pid == 0:  # child
        os._exit(0)
    deadline = time.time() + 5
    while time.time() < deadline and _proc_state(pid) != "Z":
        time.sleep(0.02)
    try:
        assert _proc_state(pid) == "Z"
    finally:
        os.waitpid(pid, 0)
    assert _proc_state(pid) is None


@ADAPTERS
def test_pid_alive_treats_a_zombie_as_dead(cls, pid_alive):
    """A zombie still answers kill(pid, 0); liveness must not report it running."""
    pid = os.fork()
    if pid == 0:  # child
        os._exit(0)
    deadline = time.time() + 5
    while time.time() < deadline and _proc_state(pid) != "Z":
        time.sleep(0.02)
    try:
        assert _proc_state(pid) == "Z"
        os.kill(pid, 0)  # succeeds for a zombie — the trap this fix closes
        assert pid_alive(pid) is False
    finally:
        os.waitpid(pid, 0)


@ADAPTERS
def test_terminate_reaps_the_child(cls, pid_alive):
    """`_terminate` must collect the child, leaving no zombie behind."""
    pid = os.fork()
    if pid == 0:  # child: own session so killpg targets only it
        os.setsid()
        time.sleep(60)
        os._exit(0)
    try:
        time.sleep(0.2)
        cls()._terminate(pid)
        assert _proc_state(pid) is None
    finally:
        try:
            os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            pass
