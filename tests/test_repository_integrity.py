from check_conflict_markers import find_conflict_markers


def test_tracked_text_files_have_no_merge_conflict_markers():
    assert find_conflict_markers() == []
