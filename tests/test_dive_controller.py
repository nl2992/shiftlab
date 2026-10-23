from shiftlab.dive.controller import ActionEstimate, Intervention, InterventionController


def test_promotion_never_overrides_missing_certificate():
    estimates = {
        Intervention.CONTINUE: ActionEstimate(0.0),
        Intervention.PROMOTE: ActionEstimate(10.0, switching_cost=0.1),
    }
    assert InterventionController().choose(estimates) == Intervention.CONTINUE
    assert (
        InterventionController().choose(estimates, promotion_certified=True) == Intervention.PROMOTE
    )


def test_controller_accounts_for_label_compute_and_switching_costs():
    estimates = {
        Intervention.CONTINUE: ActionEstimate(0.0),
        Intervention.QUERY: ActionEstimate(0.2, label_cost=0.05),
        Intervention.RETRAIN: ActionEstimate(0.5, compute_cost=0.1, switching_cost=0.6),
    }
    assert InterventionController().choose(estimates) == Intervention.QUERY


def test_controller_does_not_take_actions_with_negative_net_value():
    estimates = {
        Intervention.CONTINUE: ActionEstimate(0.0),
        Intervention.QUERY: ActionEstimate(0.01, label_cost=0.05),
    }
    assert InterventionController().choose(estimates) == Intervention.CONTINUE
