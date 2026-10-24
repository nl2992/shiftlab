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


def test_arbitrary_value_dependent_arrivals_only_expose_event_time_prefixes():
    # Delays deliberately depend on the evidence value and resolve out of order.
    values = [0.9, -0.7, 0.8, -0.6, 0.5, -0.4]
    delays = [8 if value > 0 else 1 for value in values]
    buffer = EventOrderBuffer()
    for index in range(len(values)):
        assert buffer.register(index, float(index)) == []

    arrivals = sorted((index + delays[index], index) for index in range(len(values)))
    arrival_wealth = 1.0
    released_sequence = []
    event_wealth = 1.0
    event_prefix_wealth = [event_wealth]
    alarm_threshold = 1.4
    arrival_alarm = False
    event_time_crossing = False

    for index, value in enumerate(values):
        event_wealth *= 1.0 + 0.5 * value
        event_prefix_wealth.append(event_wealth)
        event_time_crossing |= event_wealth >= alarm_threshold

    for available_time, index in arrivals:
        released = buffer.resolve(index, available_time=float(available_time), value=values[index])
        for row in released:
            released_sequence.append(row.event_index)
            arrival_wealth *= 1.0 + 0.5 * row.value
            arrival_alarm |= arrival_wealth >= alarm_threshold
            # Every released prefix state is exactly a state on the event path.
            assert arrival_wealth == pytest.approx(event_prefix_wealth[len(released_sequence)])

    assert released_sequence == list(range(len(values)))
    assert arrival_alarm == event_time_crossing
    assert buffer.pending_count == buffer.buffered_count == 0
