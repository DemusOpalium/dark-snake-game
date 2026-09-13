from check_conflict_markers import find_artifacts


def test_finds_merge_markers_and_standalone_branch_names(tmp_path):
    source = tmp_path / "broken.py"
    source.write_text(
        "<<<<<<< HEAD\n"
        "codex/reparaturzweig\n"
        "main\n"
        "=======\n"
        ">>>>>>> topic\n",
        encoding="utf-8",
    )

    artifacts = list(find_artifacts(tmp_path))

    assert [line for _path, _number, line in artifacts] == [
        "<<<<<<< HEAD",
        "codex/reparaturzweig",
        "main",
        "=======",
        ">>>>>>> topic",
    ]


def test_ignores_python_comments_with_decorative_separator(tmp_path):
    source = tmp_path / "valid.py"
    source.write_text("# ======= Abschnitt =======\n", encoding="utf-8")

    assert list(find_artifacts(tmp_path)) == []
