using HSVIforOSPOSGs
using LinearAlgebra: dot

include(joinpath(@__DIR__, "candidate_d_gadget_adapter_v2.jl"))

function collect_controller_nodes!(nodes, node)
    push!(nodes, node)
    for key in sort!(collect(keys(node.children)))
        collect_controller_nodes!(nodes, node.children[key])
    end
end

function write_controller(path, controller)
    nodes = ControllerNode[]
    collect_controller_nodes!(nodes, controller)
    ids = Dict(objectid(node.children) => i for (i, node) in enumerate(nodes))
    open(path, "w") do io
        println(io, "NODES\t", length(nodes))
        for (i, node) in enumerate(nodes)
            println(io, "N\t", i, "\t", node.partition - 1, "\t", node.gadget_residual)
            for action in sort!(collect(keys(node.action_probabilities)))
                println(io, "A\t", i, "\t", action - 1, "\t", node.action_probabilities[action])
            end
            for (action, observation) in sort!(collect(keys(node.children)))
                child = node.children[(action, observation)]
                println(io, "C\t", i, "\t", action - 1, "\t", observation - 1, "\t", ids[objectid(child.children)])
            end
        end
    end
    return length(nodes)
end

function main()
    run_dir = joinpath(@__DIR__, "..", "..", ".aris", "runs", "candidate_d_t2_extraction_v1")
    game_path = joinpath(run_dir, "switching.osposg")
    controller_path = joinpath(run_dir, "controller.tsv")
    osposg = OSPOSG(game_path)
    hsvi = HSVI(neighborhood=1e-8, presolve_epsilon=1e-8, presolve_time_limit=10.0)
    solve_start = time()
    recorder = solve(osposg, hsvi, 1e-4, 30.0)
    solve_seconds = time() - solve_start
    lower = HSVIforOSPOSGs.LB_value(osposg, hsvi)
    upper = HSVIforOSPOSGs.UB_value(osposg, hsvi)

    root = osposg.partitions[osposg.initial_partition]
    root_index = argmax([dot(alpha, osposg.initial_belief) for alpha in root.gamma])
    root_gadget = root.gamma[root_index]
    terminal_partition = only(
        p.index for p in osposg.partitions
        if length(p.states) == 1 && p.player1_actions == [6]
    )
    extraction_start = time()
    controller = extract_controller(
        osposg, hsvi, root, osposg.initial_belief, root_gadget, terminal_partition
    )
    extraction_seconds = time() - extraction_start
    node_count = write_controller(controller_path, controller)
    max_residual = maximum(node.gadget_residual for node in (controller, values(controller.children)...))
    println("lower=", lower)
    println("upper=", upper)
    println("width=", upper - lower)
    println("explorations=", recorder.exploration_count)
    println("solve_seconds=", solve_seconds)
    println("extraction_seconds=", extraction_seconds)
    println("controller_nodes=", node_count)
    println("max_gadget_residual=", max_residual)
    println("controller_path=", controller_path)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
