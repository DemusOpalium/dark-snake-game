"""No intrusive question is required for normal Classic gameplay."""
from modules.dev_feedback_ui import DeveloperFeedbackUI


class RecorderSpy:
    active = True
    def __init__(self):
        self.feedback, self.skips = [], []
    def add_feedback(self, **kwargs):
        self.feedback.append(kwargs)
        return True
    def event(self, name, **kwargs):
        self.skips.append(name)


def test_boss_rating_save_and_skip():
    ui, spy = DeveloperFeedbackUI(), RecorderSpy()
    assert ui.enqueue("boss:guardian:1", "Boss fair?")
    ui.choose_rating(4)
    ui.note = "Passt"
    assert ui.submit(spy)
    assert spy.feedback[0]["rating"] == 4
    assert not ui.active
    assert ui.enqueue("portal", "Portal ok?")
    assert ui.submit(spy, save=False)
    assert len(spy.feedback) == 1
    assert spy.skips == ["feedback_skipped"]


def test_item_verdict_and_reset():
    ui, spy = DeveloperFeedbackUI(), RecorderSpy()
    ui.enqueue("item", "Item sinnvoll?", items=["PROJECTILE_SHOOT", "SPEED_BOOST"])
    ui.item_index = 1
    ui.choose_rating(2)
    ui.toggle_verdict("Zu schwach")
    ui.toggle_verdict("Hilft nicht")
    assert ui.submit(spy)
    assert spy.feedback[0]["subject"] == "item:SPEED_BOOST"
    assert spy.feedback[0]["item_verdict"] == ["Hilft nicht", "Zu schwach"]
    ui.enqueue("zone", "Zone?")
    ui.clear()
    assert not ui.active


def test_zero_rating_is_explicit_feedback_not_a_skip():
    ui, spy = DeveloperFeedbackUI(), RecorderSpy()
    ui.enqueue("zone", "Was kaputt?")
    ui.choose_rating(0)
    assert ui.submit(spy)
    assert spy.feedback[0]["rating"] == 0
    assert spy.skips == []
