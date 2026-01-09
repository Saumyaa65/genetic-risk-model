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
        "autosomal_recessive",
        "autosomal_dominant",
        "x_linked"
    ]:
        raise ValueError("Invalid inheritance type")

    if child_sex not in ["male", "female"]:
        raise ValueError("Invalid child sex")

    for p in [parent1, parent2]:
        if p.get("status") not in [
            "affected", "carrier", "unaffected", "unknown"
        ]:
            raise ValueError("Invalid parent status")


def confidence_level(min_risk, max_risk):
    if min_risk == max_risk:
        return "high"
    if (max_risk - min_risk) <= 0.2:
        return "medium"
    return "low"


def get_carrier_probability(person):
    status = person.get("status")

    if status == "carrier":
        return 1.0
    if status == "affected":
        return 1.0
    if status == "unaffected":
        return 0.0
    if status == "unknown":
        return 0.5

    return 0.0

def autosomal_recessive_risk(parent1, parent2):
    p1 = get_carrier_probability(parent1)
    p2 = get_carrier_probability(parent2)

    risk = p1 * p2 * 0.25

    return {
        "min": risk,
        "max": risk,
        "confidence": confidence_level(risk, risk),
        "model": "autosomal_recessive",
        "factors": [
            f"Parent 1 status: {parent1['status']}",
            f"Parent 2 status: {parent2['status']}",
            "Condition requires two recessive alleles"
        ]
    }


def autosomal_dominant_risk(parent1, parent2):
    p1 = 0.5 if parent1["status"] == "affected" else 0.0
    p2 = 0.5 if parent2["status"] == "affected" else 0.0

    risk = min(1.0, p1 + p2)

    return {
        "min": risk,
        "max": risk,
        "confidence": confidence_level(risk, risk),
        "model": "autosomal_dominant",
        "factors": [
            f"Parent 1 status: {parent1['status']}",
            f"Parent 2 status: {parent2['status']}",
            "Single affected allele is sufficient"
        ]
    }


def x_linked_recessive_risk(mother, father, child_sex):
    mother_carrier = get_carrier_probability(mother)

    if child_sex == "male":
        risk = mother_carrier * 0.5
        return {
            "min": risk,
            "max": risk,
            "confidence": confidence_level(risk, risk),
            "model": "x_linked",
            "factors": [
                f"Mother status: {mother['status']}",
                "Male child inherits X chromosome from mother"
            ]
        }

    # female child
    return {
        "min": 0.0,
        "max": mother_carrier * 0.5,
        "confidence": confidence_level(0.0, mother_carrier * 0.5),
        "model": "x_linked",
        "factors": [
            f"Mother status: {mother['status']}",
            "Female child may become a carrier"
        ]
    }


def calculate_risk(inheritance_type, parent1, parent2, child_sex):
    validate_inputs(parent1, parent2, child_sex, inheritance_type)

    if inheritance_type == "autosomal_recessive":
        return autosomal_recessive_risk(parent1, parent2)

    if inheritance_type == "autosomal_dominant":
        return autosomal_dominant_risk(parent1, parent2)

    if inheritance_type == "x_linked":
        return x_linked_recessive_risk(parent2, parent1, child_sex)

    return {
        "min": 0.0,
        "max": 0.0,
        "confidence": "low",
        "model": "unknown",
        "factors": []
    }

def reverse_update_parents_from_child(
    inheritance_type,
    child_outcome,
    parent1,
    parent2
):
    """
    Updates parent carrier probabilities based on an observed child outcome.
    This runs ONLY in observed-outcome mode.
    """

    # Only act if outcome is observed
    if child_outcome not in ["affected", "unaffected"]:
        return

    # --- AUTOSOMAL RECESSIVE ---
    if inheritance_type == "autosomal_recessive":
        if child_outcome == "affected":
            # An affected child MUST have received one allele from each parent
            parent1["carrier_probability"] = 1.0
            parent2["carrier_probability"] = 1.0

        elif child_outcome == "unaffected":
            # Weak evidence → do nothing (keep uncertainty)
            pass


def calculate_risk_with_observation(
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
    if observed_child_outcome is not None:
        reverse_update_parents_from_child(
            inheritance_type,
            observed_child_outcome,
            parent1,
            parent2
        )

    return forward_result
