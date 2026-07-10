from scopp.map.io import load_map
from scopp.path_comparison import compare_path_planners


def test_path_comparison_uses_one_fixed_assignment_and_separates_distance_models() -> None:
    report = compare_path_planners(load_map("examples/maps/indoor_lab.yaml"), random_seed=0)

    assert report.assignment == (("node-04", 23), ("node-03", 38), ("node-02", 19), ("node-01", 29))
    assert sum(count for _, count in report.assignment) == report.cell_count == 109
    assert [node.cell_count for node in report.current_metric_tsp.nodes] == [23, 38, 19, 29]
    assert [node.cell_count for node in report.public_code_nn.nodes] == [23, 38, 19, 29]
    assert report.current_metric_tsp.direct_makespan_m < report.public_code_nn.direct_makespan_m
    assert report.current_metric_tsp.direct_total_m < report.public_code_nn.direct_total_m
    assert all(node.transit_inflation >= 1.0 for node in report.current_metric_tsp.nodes)
    assert all(node.transit_inflation >= 1.0 for node in report.public_code_nn.nodes)
