from schemas.artifacts import validate_artifact
from tools.video.lemo.host_fixture import build_host_artifacts


def test_host_fixture_artifacts_validate_and_place_the_clip():
    artifacts = build_host_artifacts(
        "beat_1",
        "swiss-motion",
        "A tide timetable",
        6,
        "assets/video/beat_1.mp4",
        host_runtime="editor",
    )
    for name, document in artifacts.items():
        validate_artifact(name, document)

    edit = artifacts["edit_decisions"]
    assert edit["render_runtime"] == "editor"
    placed = [cut for cut in edit["cuts"] if cut.get("source") == "beat_1_broll"]
    assert placed
    assert placed[0]["in_seconds"] == 0
    assert placed[0]["out_seconds"] == 6
