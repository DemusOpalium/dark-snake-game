import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

from modules.border_builder import BorderCell, BorderPlan, CORNERS, SIDES


@pytest.mark.parametrize(("side", "positions"), (
    ("left", {(0, y) for y in range(3)}),
    ("right", {(4, y) for y in range(3)}),
    ("top", {(x, 0) for x in range(5)}),
    ("bottom", {(x, 2) for x in range(5)}),
))
def test_only_selected_side_and_its_corners_are_targeted(side, positions):
    board = [[None] * 5 for _ in range(3)]
    plan = BorderPlan({side: "FrostAge_Side"})

    preview = plan.preview(board)

    assert {(cell.x, cell.y) for cell in preview} == positions
    assert {(cell.tile, cell.source) for cell in preview} == {("FrostAge_Side", side)}
    assert board == [[None] * 5 for _ in range(3)]


def test_entire_border_resolves_every_corner_once():
    board = [[None] * 45 for _ in range(31)]
    plan = BorderPlan(dict(zip(SIDES, ("L", "R", "T", "B"))), {"top_left": "TL"})

    preview = plan.preview(board)
    tiles = {(cell.x, cell.y): (cell.tile, cell.source) for cell in preview}

    assert len(tiles) == len(preview) == 148
    assert [tiles[position] for position in ((0, 0), (44, 0), (0, 30), (44, 30))] == [
        ("TL", "top_left"), ("T", "top"), ("B", "bottom"), ("B", "bottom"),
    ]
    assert [tiles[position][0] for position in ((0, 1), (44, 1), (1, 0), (1, 30))] == ["L", "R", "T", "B"]
    assert all(x in (0, 44) or y in (0, 30) for x, y in tiles)


def test_corner_override_waits_for_an_adjacent_active_side():
    board = [[None] * 4 for _ in range(3)]
    plan = BorderPlan({"left": "L", "top": None}, {"top_right": "TR"})

    assert plan.corner_choice("top_right") is None
    assert all(cell.x == 0 for cell in plan.preview(board))

    plan.sides["top"] = "T"
    assert plan.corner_choice("top_right") == ("TR", "top_right")
    assert plan.preview(board)[3] == BorderCell(3, 0, None, "TR", "top_right")


def test_preview_distinguishes_addition_overwrite_and_identical_tiles():
    board = [[None, "old", "same"], [None, "interior", None], [None, None, None]]
    plan = BorderPlan({"top": "same"})

    preview = plan.preview(board)

    assert [cell.previous for cell in preview] == [None, "old", "same"]
    assert [cell.changed for cell in preview] == [True, True, False]
    assert [cell.overwrites for cell in preview] == [False, True, False]
    assert board[0] == [None, "old", "same"]
    assert board[1][1] == "interior"


def test_empty_plan_has_no_target_cells():
    plan = BorderPlan(corners=dict.fromkeys(CORNERS, "override"))
    assert plan.preview([[None] * 2 for _ in range(2)]) == ()
