import pytest

from shiftlab.dive.delayed_feedback import EventOrderBuffer


def test_out_of_order_feedback_releases_evidence_in_event_order():
    buffer = EventOrderBuffer()
    first = buffer.register(0, 10.0, value=0.1)
    assert [(row.event_index, row.value) for row in first] == [(0, 0.1)]
    assert buffer.register(1, 11.0) == []
    assert buffer.register(2, 12.0) == []

    assert buffer.resolve(2, available_time=14.0, value=0.3) == []
    released = buffer.resolve(1, available_time=15.0, value=0.2)

    assert [(row.event_index, row.value) for row in released] == [(1, 0.2), (2, 0.3)]
    assert [row.feedback_delay for row in released] == [4.0, 2.0]
    assert buffer.pending_count == buffer.buffered_count == 0


def test_immediate_proxy_evidence_can_release_before_a_pending_label():
    buffer = EventOrderBuffer()
    first = buffer.register(0, 1.0, value=0.4)
    assert [(row.event_index, row.available_time) for row in first] == [(0, 1.0)]
    assert buffer.register(1, 2.0) == []
    immediate = buffer.register(2, 3.0, value=-0.1)
    assert immediate == []

    released = buffer.resolve(1, available_time=8.0, value=0.2)
    assert [row.event_index for row in released] == [1, 2]
    assert [row.feedback_delay for row in released] == [6.0, 0.0]


@pytest.mark.parametrize(
    ("register_args", "message"),
    [
        ((1, 1.0), "in index order"),
        ((0, float("nan")), "event times"),
        ((0, 1.0, float("inf")), "finite"),
    ],
)
def test_registration_rejects_invalid_order_or_values(register_args, message):
    with pytest.raises(ValueError, match=message):
        EventOrderBuffer().register(*register_args)


def test_resolve_rejects_duplicate_early_or_nonfinite_feedback():
    buffer = EventOrderBuffer()
    buffer.register(0, 3.0)
    with pytest.raises(ValueError, match="no earlier"):
        buffer.resolve(0, available_time=2.0, value=0.1)
    with pytest.raises(ValueError, match="finite"):
        buffer.resolve(0, available_time=4.0, value=float("nan"))

    buffer.resolve(0, available_time=4.0, value=0.1)
    with pytest.raises(ValueError, match="released"):
        buffer.resolve(0, available_time=5.0, value=0.2)


def test_pending_feedback_is_counted_without_revealing_its_value():
    buffer = EventOrderBuffer()
    buffer.register(0, 0.0)
    buffer.register(1, 1.0, value=0.5)
    assert buffer.pending_count == 1
    assert buffer.buffered_count == 2
