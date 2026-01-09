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
    # First, check if an explicit carrier_probability was set (from Bayesian update)
    if "carrier_probability" in person:
        return person.get("carrier_probability", 0.5)
    
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
    # Use carrier_probability if available (from Bayesian update), otherwise use status
    p1_carrier = get_carrier_probability(parent1)
    p2_carrier = get_carrier_probability(parent2)
    
    # For autosomal dominant: risk is 0.5 if parent is affected/carrier
    # If both parents could be carriers, risk = 1 - (1-p1*0.5)*(1-p2*0.5)
    # Simplified: if either parent is definitely affected, risk = 0.5
    # If both are unknown, we calculate based on probabilities
    if p1_carrier == 1.0 or parent1["status"] == "affected":
        p1_risk = 0.5
    elif p1_carrier == 0.0:
        p1_risk = 0.0
    else:
        # Unknown status: probability of passing = carrier_prob * 0.5
        p1_risk = p1_carrier * 0.5
    
    if p2_carrier == 1.0 or parent2["status"] == "affected":
        p2_risk = 0.5
    elif p2_carrier == 0.0:
        p2_risk = 0.0
    else:
        # Unknown status: probability of passing = carrier_prob * 0.5
        p2_risk = p2_carrier * 0.5
    
    # Combined risk: P(child affected) = 1 - P(both parents don't pass)
    # = 1 - (1-p1_risk)*(1-p2_risk)
    risk = 1.0 - (1.0 - p1_risk) * (1.0 - p2_risk)
    risk = min(1.0, risk)

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
    parent2,
    child_sex="unknown"
):
    """
    Updates parent carrier probabilities based on an observed child outcome.
    Uses Bayesian inference to refine parent probabilities given child phenotype.
    
    For autosomal recessive:
    - If child is AFFECTED: Both parents must be at least carriers (prob = 1.0)
    - If child is UNAFFECTED: Weak evidence of at least one non-carrier parent
    
    For autosomal dominant:
    - If child is AFFECTED: At least one parent passed the dominant allele
    - If child is UNAFFECTED: Neither parent is affected/heterozygous
    
    For X-linked:
    - If male child AFFECTED: Mother must be at least carrier
    - If female child AFFECTED: Both parents contributed
    """
    
    # Only act if outcome is observed
    if child_outcome not in ["affected", "unaffected"]:
        return

    prior_p1 = get_carrier_probability(parent1)
    prior_p2 = get_carrier_probability(parent2)

    # --- AUTOSOMAL RECESSIVE ---
    if inheritance_type == "autosomal_recessive":
        if child_outcome == "affected":
            # An affected child MUST have received mutant alleles from both parents
            # Posterior probability: parent must be carrier (if prior was unknown)
            parent1["carrier_probability"] = 1.0
            parent2["carrier_probability"] = 1.0
        
        elif child_outcome == "unaffected":
            # Unaffected child has at least one normal allele
            # Update using Bayes' theorem: P(carrier|unaffected)
            
            # P(unaffected | carrier, other carrier) = 0.75
            # P(unaffected | carrier, non-carrier) = 1.0
            # P(unaffected | non-carrier, non-carrier) = 1.0
            
            likelihood_carrier = 0.75  # Can have affected child 25% of time
            likelihood_noncarrier = 1.0  # Cannot have affected child
            
            # Update parent1
            if prior_p1 > 0 and prior_p1 < 1:
                posterior_p1 = (likelihood_carrier * prior_p1) / (
                    likelihood_carrier * prior_p1 + likelihood_noncarrier * (1 - prior_p1)
                )
                parent1["carrier_probability"] = posterior_p1
            
            # Update parent2
            if prior_p2 > 0 and prior_p2 < 1:
                posterior_p2 = (likelihood_carrier * prior_p2) / (
                    likelihood_carrier * prior_p2 + likelihood_noncarrier * (1 - prior_p2)
                )
                parent2["carrier_probability"] = posterior_p2

    # --- AUTOSOMAL DOMINANT ---
    elif inheritance_type == "autosomal_dominant":
        if child_outcome == "affected":
            # Affected child received dominant allele from at least one parent
            # Using Bayes' theorem: P(parent affected | child affected)
            
            if prior_p1 == 0 and prior_p2 == 0:
                # Both parents were unaffected - consider de novo mutation (very low prob)
                parent1["carrier_probability"] = 0.01
                parent2["carrier_probability"] = 0.01
            elif prior_p1 == 1.0 or prior_p2 == 1.0:
                # At least one parent is definitely affected
                # Use Bayes' theorem to update the other parent's probability
                if prior_p1 == 1.0 and prior_p2 > 0 and prior_p2 < 1:
                    # Parent1 is definitely affected, update parent2
                    # P(child affected | parent1 affected, parent2 unknown) = 0.5 (from parent1) + 0.5 * 0.5 * prior_p2 (from parent2 if affected AND parent1 didn't pass)
                    # = 0.5 + 0.25 * prior_p2
                    # But more accurately: P(child affected) = 1 - P(child unaffected)
                    # P(child unaffected | parent1 affected, parent2 unknown) = 0.5 * (1 - 0.5*prior_p2) = 0.5 - 0.25*prior_p2
                    # P(child affected) = 1 - (0.5 - 0.25*prior_p2) = 0.5 + 0.25*prior_p2
                    p_child_affected = 0.5 + 0.25 * prior_p2
                    
                    # P(parent2 affected | child affected, parent1 affected) using Bayes
                    # P(child affected | parent2 affected, parent1 affected) = 1 - P(child unaffected | both affected)
                    # = 1 - 0.5 * 0.5 = 0.75
                    p_child_given_p2_affected = 0.75
                    posterior_p2 = (prior_p2 * p_child_given_p2_affected) / p_child_affected
                    parent2["carrier_probability"] = min(1.0, max(0.0, posterior_p2))
                
                if prior_p2 == 1.0 and prior_p1 > 0 and prior_p1 < 1:
                    # Parent2 is definitely affected, update parent1
                    p_child_affected = 0.5 + 0.25 * prior_p1
                    p_child_given_p1_affected = 0.75
                    posterior_p1 = (prior_p1 * p_child_given_p1_affected) / p_child_affected
                    parent1["carrier_probability"] = min(1.0, max(0.0, posterior_p1))
            else:
                # Both parents are unknown (0 < prior < 1)
                # For autosomal dominant: if child is affected, at least one parent must be affected
                # P(child affected) = 1 - P(both parents don't pass allele)
                # P(parent doesn't pass | parent affected) = 0.5
                # P(parent doesn't pass | parent unaffected) = 1.0
                # P(child unaffected) = (1 - 0.5*prior_p1) * (1 - 0.5*prior_p2)
                # P(child affected) = 1 - (1 - 0.5*prior_p1) * (1 - 0.5*prior_p2)
                
                p_child_unaffected = (1.0 - 0.5 * prior_p1) * (1.0 - 0.5 * prior_p2)
                p_child_affected = 1.0 - p_child_unaffected
                
                if p_child_affected > 0:
                    # P(parent1 affected | child affected) using Bayes' theorem
                    # P(parent1 affected and child affected) = prior_p1 * P(child affected | parent1 affected)
                    # P(child affected | parent1 affected) = 1 - P(child unaffected | parent1 affected)
                    # = 1 - 0.5 * (1 - 0.5*prior_p2) = 1 - 0.5 + 0.25*prior_p2 = 0.5 + 0.25*prior_p2
                    p_child_given_p1_affected = 0.5 + 0.25 * prior_p2
                    posterior_p1 = (prior_p1 * p_child_given_p1_affected) / p_child_affected
                    
                    p_child_given_p2_affected = 0.5 + 0.25 * prior_p1
                    posterior_p2 = (prior_p2 * p_child_given_p2_affected) / p_child_affected
                    
                    parent1["carrier_probability"] = min(1.0, max(0.0, posterior_p1))
                    parent2["carrier_probability"] = min(1.0, max(0.0, posterior_p2))
        
        elif child_outcome == "unaffected":
            # Unaffected child did NOT receive dominant allele from either parent
            # Using Bayes' theorem: P(parent affected | child unaffected)
            # P(child unaffected | parent affected) = 0.5 (50% chance of not passing)
            # P(child unaffected | parent unaffected) = 1.0
            
            if prior_p1 > 0 and prior_p1 < 1:
                # P(child unaffected) = P(child unaffected | parent1 affected) * P(parent1 affected) 
                #                      + P(child unaffected | parent1 unaffected) * P(parent1 unaffected)
                # = 0.5 * prior_p1 + 1.0 * (1 - prior_p1) = 1 - 0.5 * prior_p1
                # But we also need to account for parent2
                # P(child unaffected) = (1 - 0.5*prior_p1) * (1 - 0.5*prior_p2)
                p_child_unaffected = (1.0 - 0.5 * prior_p1) * (1.0 - 0.5 * prior_p2)
                if p_child_unaffected > 0:
                    # P(parent1 affected | child unaffected) = P(child unaffected | parent1 affected) * P(parent1 affected) / P(child unaffected)
                    # = (0.5 * prior_p1 * (1 - 0.5*prior_p2)) / p_child_unaffected
                    p_child_unaffected_given_p1 = 0.5 * (1.0 - 0.5 * prior_p2)
                    posterior_p1 = (prior_p1 * p_child_unaffected_given_p1) / p_child_unaffected
                    parent1["carrier_probability"] = max(0.0, min(1.0, posterior_p1))
            
            if prior_p2 > 0 and prior_p2 < 1:
                p_child_unaffected = (1.0 - 0.5 * prior_p1) * (1.0 - 0.5 * prior_p2)
                if p_child_unaffected > 0:
                    p_child_unaffected_given_p2 = 0.5 * (1.0 - 0.5 * prior_p1)
                    posterior_p2 = (prior_p2 * p_child_unaffected_given_p2) / p_child_unaffected
                    parent2["carrier_probability"] = max(0.0, min(1.0, posterior_p2))

    # --- X-LINKED RECESSIVE ---
    elif inheritance_type == "x_linked":
        if child_outcome == "affected":
            # Male affected: mother MUST be carrier
            # Female affected: both parents must contribute
            if child_sex == "male":
                parent2["carrier_probability"] = 1.0  # mother (second parent)
            elif child_sex == "female":
                parent1["carrier_probability"] = 1.0  # father (first parent)
                parent2["carrier_probability"] = 1.0  # mother (second parent)
        
        elif child_outcome == "unaffected":
            # Unaffected male: mother is likely non-carrier
            # Unaffected female: could still be carrier
            if child_sex == "male":
                if prior_p2 > 0 and prior_p2 < 1:
                    parent2["carrier_probability"] = prior_p2 * 0.2
            elif child_sex == "female":
                # Female unaffected with unknown parent status gives weak evidence
                if prior_p2 > 0 and prior_p2 < 1:
                    parent2["carrier_probability"] = prior_p2 * 0.5


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
    
    Returns both forward and potentially updated risks.
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
