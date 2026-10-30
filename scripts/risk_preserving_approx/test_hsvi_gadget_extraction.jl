using HSVIforOSPOSGs
using JuMP
using LinearAlgebra: dot

const REPO = normpath(joinpath(@__DIR__, "..", ".."))
const GAME = joinpath(@__DIR__, "fixtures", "candidate_d_gadget_toy.osposg")
const OUTPUT_DIR = joinpath(REPO, ".aris", "runs", "candidate_d_gadget_toy")
const OUTPUT = joinpath(OUTPUT_DIR, "result.json")
const LOG = joinpath(OUTPUT_DIR, "run.log")
const TARGET_VALUE = 11 / 25

struct ControllerNode
    partition::Int
    action_probabilities::Dict{Int,Float64}
    children::Dict{Tuple{Int,Int},ControllerNode}
    gadget_residual::Float64
end

function gadget_stage(osposg, hsvi, partition, belief, rho)
    model = Model(hsvi.optimizer_factory)
    set_silent(model)

    policy1 = Dict(a1 => @variable(model, lower_bound = 0.0, upper_bound = 1.0) for a1 in partition.player1_actions)
    child_keys = Tuple{Int,Int,Int}[]
    lambda_keys = Tuple{Int,Int,Int}[]
    for a1 in partition.player1_actions, o in partition.observations[a1]
        target = osposg.partitions[partition.target[a1, o]]
        append!(child_keys, ((a1, o, spi) for spi in eachindex(target.states)))
        append!(lambda_keys, ((a1, o, i) for i in eachindex(target.gamma)))
    end
    child_value = Dict(key => @variable(model) for key in child_keys)
    lambda = Dict(key => @variable(model, lower_bound = 0.0) for key in lambda_keys)
    state_value = Dict(s => @variable(model) for s in partition.states)

    @objective(model, Max, sum(belief[si] * state_value[s] for (si, s) in enumerate(partition.states)))
    @constraint(model, sum(policy1[a1] for a1 in partition.player1_actions) == 1.0)

    for a1 in partition.player1_actions, o in partition.observations[a1]
        target = osposg.partitions[partition.target[a1, o]]
        @constraint(model, sum(lambda[(a1, o, i)] for i in eachindex(target.gamma)) == policy1[a1])
        for spi in eachindex(target.states)
            @constraint(
                model,
                child_value[(a1, o, spi)] ==
                sum(lambda[(a1, o, i)] * target.gamma[i][spi] for i in eachindex(target.gamma)),
            )
        end
    end

    for (si, s) in enumerate(partition.states)
        @constraint(model, state_value[s] >= rho[si])
        for a2 in osposg.states[s].player2_actions
            continuation = 0.0
            for a1 in partition.player1_actions, o in partition.observations[a1]
                target = osposg.partitions[partition.target[a1, o]]
                for (spi, sp) in enumerate(target.states)
                    continuation += get(osposg.transition_map, (s, a1, a2, o, sp), 0.0) * child_value[(a1, o, spi)]
                end
            end
            immediate = sum(policy1[a1] * get(osposg.reward_map, (s, a1, a2), 0.0) for a1 in partition.player1_actions)
            @constraint(model, state_value[s] <= immediate + osposg.discount * continuation)
        end
    end

    optimize!(model)
    is_solved_and_feasible(model) || error("gadget LP did not solve: $(termination_status(model))")

    probabilities = Dict(a1 => value(policy1[a1]) for a1 in partition.player1_actions)
    child_gadgets = Dict{Tuple{Int,Int},Vector{Float64}}()
    for a1 in partition.player1_actions, o in partition.observations[a1]
        probability = probabilities[a1]
        probability <= 1e-12 && continue
        target = osposg.partitions[partition.target[a1, o]]
        child_gadgets[(a1, o)] = [value(child_value[(a1, o, spi)]) / probability for spi in eachindex(target.states)]
    end
    residual = maximum(max(rho[si] - value(state_value[s]), 0.0) for (si, s) in enumerate(partition.states))
    return probabilities, child_gadgets, residual
end

function successor_belief(osposg, partition, belief, opponent_policy, a1, observation)
    target = osposg.partitions[partition.target[a1, observation]]
    mass_by_state = zeros(length(target.states))
    for (si, s) in enumerate(partition.states)
        for (a2i, a2) in enumerate(osposg.states[s].player2_actions)
            p2 = opponent_policy[si][a2i]
            p2 == 0.0 && continue
            for (o, sp, probability) in get(partition.transitions, (s, a1, a2), Tuple{Int,Int,Float64}[])
                o == observation || continue
                mass_by_state[osposg.states[sp].belief_index] += belief[si] * p2 * probability
            end
        end
    end
    mass = sum(mass_by_state)
    mass > 0.0 || return 0.0, mass_by_state
    return mass, mass_by_state ./ mass
end

function extract_controller(osposg, hsvi, partition, belief, rho, terminal_partition; depth = 0)
    depth <= 2 * length(osposg.partitions) || error("unexpected extraction depth")
    probabilities, child_gadgets, residual = gadget_stage(osposg, hsvi, partition, belief, rho)
    _, opponent_policy, _ = HSVIforOSPOSGs.compute_LB(osposg, hsvi, partition, belief)
    children = Dict{Tuple{Int,Int},ControllerNode}()

    for (a1, p1) in probabilities
        p1 <= 1e-10 && continue
        for observation in partition.observations[a1]
            key = (a1, observation)
            haskey(child_gadgets, key) || continue
            mass, next_belief = successor_belief(osposg, partition, belief, opponent_policy, a1, observation)
            mass <= 1e-12 && continue
            target_index = partition.target[a1, observation]
            target_index == terminal_partition && continue
            target = osposg.partitions[target_index]
            children[key] = extract_controller(
                osposg,
                hsvi,
                target,
                next_belief,
                child_gadgets[key],
                terminal_partition;
                depth = depth + 1,
            )
        end
    end
    return ControllerNode(partition.index, probabilities, children, residual)
end

function controller_value(osposg, node, state)
    partition = osposg.partitions[node.partition]
    total = 0.0
    for (a1, p1) in node.action_probabilities
        p1 <= 1e-12 && continue
        for a2 in osposg.states[state].player2_actions
            reward = get(osposg.reward_map, (state, a1, a2), 0.0)
            continuation = 0.0
            for (observation, next_state, probability) in get(partition.transitions, (state, a1, a2), Tuple{Int,Int,Float64}[])
                child = get(node.children, (a1, observation), nothing)
                child_value = child === nothing ? 0.0 : controller_value(osposg, child, next_state)
                continuation += probability * child_value
            end
            total += p1 * (reward + osposg.discount * continuation)
        end
    end
    return total
end

function node_count(node)
    return 1 + sum(node_count(child) for child in values(node.children); init = 0)
end

function main()
    mkpath(OUTPUT_DIR)
    open(LOG, "w") do io
        redirect_stdout(io) do
            redirect_stderr(io) do
                osposg = OSPOSG(GAME)
                epsilon = 1e-4
                hsvi = HSVI(neighborhood = 1e-8, presolve_epsilon = 1e-8, presolve_time_limit = 10.0)
                start = time()
                recorder = solve(osposg, hsvi, epsilon, 30.0)
                solve_seconds = time() - start
                initial_partition = osposg.partitions[osposg.initial_partition]
                lower = HSVIforOSPOSGs.LB_value(osposg, hsvi)
                upper = HSVIforOSPOSGs.UB_value(osposg, hsvi)
                initial_index = argmax([dot(alpha, osposg.initial_belief) for alpha in initial_partition.gamma])
                initial_gadget = initial_partition.gamma[initial_index]
                terminal_partition = only(findall(p -> p.index == 3, osposg.partitions))
                extraction_start = time()
                controller = extract_controller(
                    osposg,
                    hsvi,
                    initial_partition,
                    osposg.initial_belief,
                    initial_gadget,
                    terminal_partition,
                )
                extraction_seconds = time() - extraction_start
                payoff = sum(
                    osposg.initial_belief[si] * controller_value(osposg, controller, s)
                    for (si, s) in enumerate(initial_partition.states)
                )
                probe_index = findfirst(==("probe"), osposg.player1_action_labels)
                signal0 = findfirst(==("signal0"), osposg.observation_labels)
                signal1 = findfirst(==("signal1"), osposg.observation_labels)
                guess0 = findfirst(==("guess0"), osposg.player1_action_labels)
                guess1 = findfirst(==("guess1"), osposg.player1_action_labels)
                probe_probability = controller.action_probabilities[probe_index]
                guess0_probability = controller.children[(probe_index, signal0)].action_probabilities[guess0]
                guess1_probability = controller.children[(probe_index, signal1)].action_probabilities[guess1]
                result = (
                    status = "candidate",
                    julia_version = string(VERSION),
                    game_states = length(osposg.states),
                    game_transitions = length(osposg.transition_map),
                    lower_bound = lower,
                    upper_bound = upper,
                    gap = upper - lower,
                    target_value = TARGET_VALUE,
                    extracted_payoff = payoff,
                    probe_probability = probe_probability,
                    guess0_after_signal0 = guess0_probability,
                    guess1_after_signal1 = guess1_probability,
                    max_gadget_residual = maximum(node.gadget_residual for node in (controller, values(controller.children)...)),
                    controller_nodes = node_count(controller),
                    solve_seconds = solve_seconds,
                    extraction_seconds = extraction_seconds,
                    hsvi_explorations = recorder.exploration_count,
                )
                display(result)
                result.gap <= epsilon || error("HSVI value gap exceeded protocol threshold")
                result.extracted_payoff >= TARGET_VALUE - 2e-3 || error("extracted strategy missed exact toy value")
                result.max_gadget_residual < 1e-7 || error("gadget constraint residual exceeded threshold")
                result.probe_probability >= 1 - 1e-6 || error("controller did not probe")
                result.guess0_after_signal0 >= 1 - 1e-6 || error("controller failed to guess state 0 after signal 0")
                result.guess1_after_signal1 >= 1 - 1e-6 || error("controller failed to guess state 1 after signal 1")
                open(OUTPUT, "w") do io
                    println(io, "{")
                    println(io, "  \"status\": \"pass\",")
                    println(io, "  \"julia_version\": \"$(VERSION)\",")
                    println(io, "  \"game_states\": $(result.game_states),")
                    println(io, "  \"game_transitions\": $(result.game_transitions),")
                    println(io, "  \"lower_bound\": $(result.lower_bound),")
                    println(io, "  \"upper_bound\": $(result.upper_bound),")
                    println(io, "  \"gap\": $(result.gap),")
                    println(io, "  \"target_value\": $(result.target_value),")
                    println(io, "  \"extracted_payoff\": $(result.extracted_payoff),")
                    println(io, "  \"probe_probability\": $(result.probe_probability),")
                    println(io, "  \"guess0_after_signal0\": $(result.guess0_after_signal0),")
                    println(io, "  \"guess1_after_signal1\": $(result.guess1_after_signal1),")
                    println(io, "  \"max_gadget_residual\": $(result.max_gadget_residual),")
                    println(io, "  \"controller_nodes\": $(result.controller_nodes),")
                    println(io, "  \"solve_seconds\": $(result.solve_seconds),")
                    println(io, "  \"extraction_seconds\": $(result.extraction_seconds),")
                    println(io, "  \"hsvi_explorations\": $(result.hsvi_explorations)")
                    println(io, "}")
                end
            end
        end
    end
end

main()
