"""
INPUT FORMAT:

parent = {
    "status": "affected" | "carrier" | "unaffected" | "unknown"
}

child_sex = "male" | "female"
"""

"""
child_outcome:
- None          -> no observation (default)
- "affected"    -> observed affected
- "unaffected"  -> observed unaffected
"""


def validate_inputs(parent1, parent2, child_sex, inheritance_type):
    if inheritance_type not in [
        """
        # Copy the corrected implementation from src/genetics_logic.py so both services
        # are consistent. This file intentionally mirrors the source module.
        """

        from ..src import genetics_logic as _src_impl

        # Re-export the primary functions for compatibility
        validate_inputs = _src_impl.validate_inputs
        calculate_risk = _src_impl.calculate_risk
        calculate_risk_with_observation = _src_impl.calculate_risk_with_observation
        reverse_update_parents_from_child = _src_impl.reverse_update_parents_from_child
        get_carrier_probability = _src_impl.get_carrier_probability

    inheritance_type,
    parent1,
    parent2,
    child_sex,
    observed_child_outcome=None
):
    """
    Wrapper function.
    - Always does forward calculation
    - Optionally performs reverse update if outcome is observed
    """

    # Step 1: forward calculation (pure)
    forward_result = calculate_risk(
        inheritance_type,
        parent1,
        parent2,
        child_sex
    )

    # Step 2: reverse update ONLY if explicitly requested
    if observed_child_outcome is not None and observed_child_outcome != "unknown":
        # Make copies to avoid mutating original inputs
        updated_parent1 = parent1.copy()
        updated_parent2 = parent2.copy()
        
        reverse_update_parents_from_child(
            inheritance_type,
            observed_child_outcome,
            updated_parent1,
            updated_parent2,
            child_sex
        )
        
        # Recalculate with updated parent probabilities
        updated_result = calculate_risk(
            inheritance_type,
            updated_parent1,
            updated_parent2,
            child_sex
        )
        
        # Append metadata about the Bayesian update
        forward_result["bayesian_update"] = {
            "observed_outcome": observed_child_outcome,
            "parent1_original_status": parent1.get("status"),
            "parent2_original_status": parent2.get("status"),
            "parent1_carrier_probability": updated_parent1.get("carrier_probability", get_carrier_probability(updated_parent1)),
            "parent2_carrier_probability": updated_parent2.get("carrier_probability", get_carrier_probability(updated_parent2)),
            "updated_risk": updated_result
        }

    return forward_result