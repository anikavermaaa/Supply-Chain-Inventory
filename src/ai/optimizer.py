# src/ai/optimizer.py
from pulp import LpProblem, LpMinimize, LpVariable, lpSum

def optimize_inventory(forecasts, stock, reorder_cost):
    """
    forecasts: dict -> {sku: predicted_next_day_units}
    stock: dict -> {sku: current_on_hand_units}
    reorder_cost: dict -> {sku: cost_per_unit_to_reorder}
    """

    model = LpProblem("Inventory_Optimization", LpMinimize)
    order = {sku: LpVariable(f"order_{sku}", lowBound=0) for sku in forecasts}

    # Objective: minimize total reorder cost
    model += lpSum(reorder_cost[sku] * order[sku] for sku in forecasts)

    # Constraint: after reordering, total >= forecast demand
    for sku in forecasts:
        model += stock[sku] + order[sku] >= forecasts[sku]

    model.solve()

    # Return suggested reorder qty per SKU
    return {sku: round(order[sku].value(), 2) for sku in forecasts}
