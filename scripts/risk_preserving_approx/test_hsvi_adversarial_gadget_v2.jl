include(joinpath(@__DIR__, "test_hsvi_gadget_extraction.jl"))
using HSVIforOSPOSGs
using LinearAlgebra: dot

const ADVERSARIAL_GAME = joinpath(@__DIR__, "fixtures", "candidate_d_adversarial_toy_v2.osposg")
const ADVERSARIAL_OUT = joinpath(REPO, ".aris", "runs", "candidate_d_adversarial_toy_v2")

function run_adversarial_toy()
    mkpath(ADVERSARIAL_OUT)
    osposg = OSPOSG(ADVERSARIAL_GAME)
    epsilon = 1e-4
    hsvi = HSVI(neighborhood = 1e-8, presolve_epsilon = 1e-8, presolve_time_limit = 10.0)
    started = time()
    recorder = solve(osposg, hsvi, epsilon, 30.0)
    solve_seconds = time() - started
    root = osposg.partitions[osposg.initial_partition]
    lower = HSVIforOSPOSGs.LB_value(osposg, hsvi)
    upper = HSVIforOSPOSGs.UB_value(osposg, hsvi)
    alpha_index = argmax([dot(alpha, osposg.initial_belief) for alpha in root.gamma])
    gadget = root.gamma[alpha_index]
    terminal = only(findall(p -> p.index == 2, osposg.partitions))
    extracted = extract_controller(osposg, hsvi, root, osposg.initial_belief, gadget, terminal)

    row0 = findfirst(==("row0"), osposg.player1_action_labels)
    row1 = findfirst(==("row1"), osposg.player1_action_labels)
    col0 = findfirst(==("column0"), osposg.player2_action_labels)
    col1 = findfirst(==("column1"), osposg.player2_action_labels)
    p_row0 = extracted.action_probabilities[row0]
    p_row1 = extracted.action_probabilities[row1]
    payoff_col0 = sum(osposg.initial_belief[si] * (
        p_row0 * osposg.reward_map[s, row0, col0] + p_row1 * osposg.reward_map[s, row1, col0]
    ) for (si, s) in enumerate(root.states))
    payoff_col1 = sum(osposg.initial_belief[si] * (
        p_row0 * osposg.reward_map[s, row0, col1] + p_row1 * osposg.reward_map[s, row1, col1]
    ) for (si, s) in enumerate(root.states))
    security_value = min(payoff_col0, payoff_col1)
    result = (
        solver_lower = lower,
        solver_upper = upper,
        solver_gap = upper - lower,
        exact_security_value = 0.0,
        extracted_security_value = security_value,
        row0_probability = p_row0,
        row1_probability = p_row1,
        column0_payoff = payoff_col0,
        column1_payoff = payoff_col1,
        gadget_residual = extracted.gadget_residual,
        solve_seconds = solve_seconds,
        explorations = recorder.exploration_count,
    )
    result.solver_gap <= epsilon || error("adversarial toy HSVI gap exceeded protocol threshold")
    abs(p_row0 + p_row1 - 1.0) < 1e-8 || error("extracted root action distribution is not normalized")
    abs(result.extracted_security_value - result.exact_security_value) <= 1e-3 ||
        error("extracted controller failed independent maximin evaluation")
    result.gadget_residual < 1e-7 || error("gadget residual exceeded threshold")
    open(joinpath(ADVERSARIAL_OUT, "result.json"), "w") do io
        println(io, "{\n  \"status\": \"pass\",")
        for (index, (key, value)) in enumerate(pairs(result))
            comma = index == length(result) ? "" : ","
            println(io, "  \"$(key)\": $(value)$(comma)")
        end
        println(io, "}")
    end
    return result
end

mkpath(ADVERSARIAL_OUT)
open(joinpath(ADVERSARIAL_OUT, "run.log"), "w") do io
    result = redirect_stdout(io) do
        redirect_stderr(io) do
            run_adversarial_toy()
        end
    end
    display(result)
end
