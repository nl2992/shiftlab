include(joinpath(@__DIR__, "test_hsvi_gadget_extraction.jl"))
using HSVIforOSPOSGs
using LinearAlgebra: dot

const SEQUENTIAL_GAME = joinpath(@__DIR__, "fixtures", "candidate_d_sequential_adversarial_toy.osposg")
const SEQUENTIAL_OUT = joinpath(REPO, ".aris", "runs", "candidate_d_sequential_adversarial_toy")

function evaluate_stage(osposg, node, states, row0, row1, column0, column1)
    p0 = node.action_probabilities[row0]
    p1 = node.action_probabilities[row1]
    worst_payoff = Inf
    largest_abs_payoff = 0.0
    for state in states, column in (column0, column1)
        payoff = (
                p0 * osposg.reward_map[state, row0, column] +
                p1 * osposg.reward_map[state, row1, column]
        )
        worst_payoff = min(worst_payoff, payoff)
        largest_abs_payoff = max(largest_abs_payoff, abs(payoff))
    end
    return worst_payoff, largest_abs_payoff
end

function run_sequential_toy()
    mkpath(SEQUENTIAL_OUT)
    osposg = OSPOSG(SEQUENTIAL_GAME)
    epsilon = 1e-4
    hsvi = HSVI(neighborhood = 1e-8, presolve_epsilon = 1e-8, presolve_time_limit = 10.0)
    started = time()
    recorder = solve(osposg, hsvi, epsilon, 30.0)
    solve_seconds = time() - started
    root = osposg.partitions[osposg.initial_partition]
    lower = HSVIforOSPOSGs.LB_value(osposg, hsvi)
    upper = HSVIforOSPOSGs.UB_value(osposg, hsvi)
    alpha_index = argmax([dot(alpha, osposg.initial_belief) for alpha in root.gamma])
    terminal = only(findall(p -> p.index == 3, osposg.partitions))
    controller = extract_controller(osposg, hsvi, root, osposg.initial_belief, root.gamma[alpha_index], terminal)

    labels = osposg.player1_action_labels
    row0_t1 = findfirst(==("row0_t1"), labels)
    row1_t1 = findfirst(==("row1_t1"), labels)
    row0_t2 = findfirst(==("row0_t2"), labels)
    row1_t2 = findfirst(==("row1_t2"), labels)
    column0 = findfirst(==("column0"), osposg.player2_action_labels)
    column1 = findfirst(==("column1"), osposg.player2_action_labels)
    p_row0_t1 = controller.action_probabilities[row0_t1]
    p_row1_t1 = controller.action_probabilities[row1_t1]
    initial_security, initial_max_abs = evaluate_stage(osposg, controller, root.states, row0_t1, row1_t1, column0, column1)

    see0 = findfirst(==("see0"), osposg.observation_labels)
    see1 = findfirst(==("see1"), osposg.observation_labels)
    child0 = controller.children[(row0_t1, see0)]
    child1 = controller.children[(row0_t1, see1)]
    part2 = osposg.partitions[child0.partition]
    child0_security, child0_max_abs = evaluate_stage(osposg, child0, part2.states, row0_t2, row1_t2, column0, column1)
    child1_security, child1_max_abs = evaluate_stage(osposg, child1, part2.states, row0_t2, row1_t2, column0, column1)

    result = (
        solver_lower = lower,
        solver_upper = upper,
        solver_gap = upper - lower,
        exact_security_value = 0.0,
        root_security_value = initial_security,
        root_largest_abs_state_column_payoff = initial_max_abs,
        root_row0_probability = p_row0_t1,
        root_row1_probability = p_row1_t1,
        see0_row0_probability = child0.action_probabilities[row0_t2],
        see1_row0_probability = child1.action_probabilities[row0_t2],
        see0_security_value = child0_security,
        see1_security_value = child1_security,
        see0_largest_abs_state_column_payoff = child0_max_abs,
        see1_largest_abs_state_column_payoff = child1_max_abs,
        controller_nodes = node_count(controller),
        gadget_residual = maximum(node.gadget_residual for node in (controller, values(controller.children)...)),
        solve_seconds = solve_seconds,
        explorations = recorder.exploration_count,
    )
    result.solver_gap <= epsilon || error("sequential adversarial HSVI gap exceeded threshold")
    abs(result.root_row0_probability - 0.5) <= 1e-3 || error("root controller is not minimax")
    abs(result.see0_row0_probability - 0.5) <= 1e-3 || error("see0 continuation is not minimax")
    abs(result.see1_row0_probability - 0.5) <= 1e-3 || error("see1 continuation is not minimax")
    abs(result.root_security_value) <= 1e-3 || error("root security value disagrees with exact value")
    abs(result.see0_security_value) <= 1e-3 || error("see0 security value disagrees with exact value")
    abs(result.see1_security_value) <= 1e-3 || error("see1 security value disagrees with exact value")
    result.root_largest_abs_state_column_payoff <= 1e-3 || error("root fails statewise opponent-action check")
    result.see0_largest_abs_state_column_payoff <= 1e-3 || error("see0 fails statewise opponent-action check")
    result.see1_largest_abs_state_column_payoff <= 1e-3 || error("see1 fails statewise opponent-action check")
    result.controller_nodes == 5 || error("unexpected sequential controller node count")
    result.gadget_residual < 1e-7 || error("gadget residual exceeded threshold")

    open(joinpath(SEQUENTIAL_OUT, "result.json"), "w") do io
        println(io, "{\n  \"status\": \"pass\",")
        for (index, (key, value)) in enumerate(pairs(result))
            comma = index == length(result) ? "" : ","
            json_value = value isa AbstractVector ? "[" * join(value, ", ") * "]" : string(value)
            println(io, "  \"$(key)\": $(json_value)$(comma)")
        end
        println(io, "}")
    end
    return result
end

mkpath(SEQUENTIAL_OUT)
open(joinpath(SEQUENTIAL_OUT, "run.log"), "w") do io
    result = redirect_stdout(io) do
        redirect_stderr(io) do
            run_sequential_toy()
        end
    end
    display(result)
end
