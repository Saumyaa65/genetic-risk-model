"""
Genetics risk utilities (production-ready, well-commented).

Conventions:
- `parent1` = father (male)
- `parent2` = mother (female)

Parent `status` values:
- "affected"  -> observed affected phenotype
- "carrier"   -> observed carrier (where applicable)
- "unaffected"-> observed unaffected (no known mutant allele)
- "unknown"   -> no phenotype/genotype information

For `unknown` parents we use prior population probabilities which can be
overridden by supplying `carrier_probability` or `affected_probability`
in the parent dict. Default priors are conservative and documented below.

All functions return explicit probabilities and include explanatory
`factors` describing assumptions used.
"""


DEFAULT_PRIORS = {
    # Typical defaults for rare Mendelian disorders; users can override
    # by setting `carrier_probability` or `affected_probability` on a parent.
    "autosomal_recessive": {
        "carrier_prior": 0.01,     # P(parent is heterozygous Aa)
        "affected_prior": 0.0001   # P(parent is aa (rare homozygous))
    },
    "autosomal_dominant": {
        "affected_prior": 0.001    # P(parent is affected (heterozygous))
    },
    "x_linked": {
        "mother_carrier_prior": 0.01,
        "mother_affected_prior": 0.0001,
        "father_affected_prior": 0.0005
    }
}


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
    # Backwards-compatible helper: returns an explicit carrier_probability
    # if set (e.g., by a Bayesian reverse update). Otherwise, this function
    # should NOT be used to infer genotype priors for all inheritance modes.
    if "carrier_probability" in person:
        return person.get("carrier_probability", 0.0)

    status = person.get("status")
    if status == "carrier":
        return 1.0
    if status == "affected":
        # 'affected' is not the same as 'carrier' for all modes;
        # caller must interpret appropriately. Return 1.0 here conservatively
        # for places where an observed carrier is required.
        return 1.0
    if status == "unaffected":
        return 0.0
    # unknown: no observed carrier information
    return 0.0


def _get_prior(parent, inheritance_type, role=None):
    """Return relevant priors for a parent based on inheritance_type.

    - parent: dict possibly containing `carrier_probability` or
      `affected_probability` to override priors.
    - role: for x_linked, role is 'mother' or 'father'.
    """
    if inheritance_type == "autosomal_recessive":
        carrier = parent.get("carrier_probability", DEFAULT_PRIORS["autosomal_recessive"]["carrier_prior"])
        affected = parent.get("affected_probability", DEFAULT_PRIORS["autosomal_recessive"]["affected_prior"])
        return {"carrier": carrier, "affected": affected}

    if inheritance_type == "autosomal_dominant":
        affected = parent.get("affected_probability", DEFAULT_PRIORS["autosomal_dominant"]["affected_prior"])
        return {"affected": affected}

    if inheritance_type == "x_linked":
        if role == "mother":
            carrier = parent.get("carrier_probability", DEFAULT_PRIORS["x_linked"]["mother_carrier_prior"])
            affected = parent.get("affected_probability", DEFAULT_PRIORS["x_linked"]["mother_affected_prior"])
            return {"carrier": carrier, "affected": affected}
        else:
            affected = parent.get("affected_probability", DEFAULT_PRIORS["x_linked"]["father_affected_prior"])
            return {"affected": affected}

    return {}

def autosomal_recessive_risk(father, mother):
    """Compute exact probability child is affected (aa) under autosomal recessive.

    Rules (Mendelian, no de novo assumed):
    - A parent with phenotype `affected` (aa) transmits mutant allele with P=1.0.
    - A parent with phenotype `carrier` (Aa) transmits mutant allele with P=0.5.
    - A parent `unaffected` (AA) transmits mutant allele with P=0.0.
    - An `unknown` parent's transmission probability is derived from priors:
        P(transmit) = P(Aa)*0.5 + P(aa)*1.0
      where P(Aa) and P(aa) come from `_get_prior`.
    """
    # father -> parent1, mother -> parent2
    f_priors = _get_prior(father, "autosomal_recessive")
    m_priors = _get_prior(mother, "autosomal_recessive")

    def transmit_prob(parent, priors):
        status = parent.get("status")
        if status == "affected":
            return 1.0
        if status == "carrier":
            return 0.5
        if status == "unaffected":
            return 0.0
        # unknown: use priors
        return priors.get("carrier", 0.0) * 0.5 + priors.get("affected", 0.0) * 1.0

    p_f = transmit_prob(father, f_priors)
    p_m = transmit_prob(mother, m_priors)

    risk = p_f * p_m

    return {
        "min": risk,
        "max": risk,
        "confidence": confidence_level(risk, risk),
        "model": "autosomal_recessive",
        "factors": [
            f"Father status: {father['status']}",
            f"Mother status: {mother['status']}",
            "Both parents must transmit a mutant allele"
        ]
    }


def autosomal_dominant_risk(father, mother):
    """Autosomal dominant inheritance risk.

    Mendelian rules and assumptions:
    - A typical affected individual is heterozygous (Aa) and transmits the
      dominant allele with probability 0.5. Homozygous dominant (AA) is
      uncommon and may be substituted via `affected_probability` if known.
    - An unaffected individual (phenotype) transmits mutant allele with P=0.
    - Unknown parents use `affected_prior` to compute transmission probability:
        P(transmit) = P(affected) * 0.5  (assuming affected ~ heterozygote)
    """
    f_priors = _get_prior(father, "autosomal_dominant")
    m_priors = _get_prior(mother, "autosomal_dominant")

    def transmit_prob_dom(parent, priors):
        status = parent.get("status")
        if status == "affected" or status == "carrier":
            # Treat observed 'affected' (phenotype) as heterozygous unless
            # caller provided different `affected_probability` details.
            return 0.5
        if status == "unaffected":
            return 0.0
        # unknown
        return priors.get("affected", 0.0) * 0.5

    p_f = transmit_prob_dom(father, f_priors)
    p_m = transmit_prob_dom(mother, m_priors)

    # Child affected if at least one parent transmits the dominant allele
    risk = 1.0 - (1.0 - p_f) * (1.0 - p_m)

    return {
        "min": risk,
        "max": risk,
        "confidence": confidence_level(risk, risk),
        "model": "autosomal_dominant",
        "factors": [
            f"Father status: {father['status']}",
            f"Mother status: {mother['status']}",
            "Single dominant allele causes disease in child"
        ]
    }


def x_linked_recessive_risk(father, mother, child_sex):
    """X-linked recessive risk (father, mother ordering maintained).

    Key Mendelian points:
    - Sons inherit their single X chromosome from the mother only; father's
      status does not affect sons.
    - Daughters inherit one X from each parent; a daughter is affected only
      if she receives mutant X from both parents.
    - Mother `affected` (XrXr) will transmit mutant allele to all children
      (sons: always affected; daughters: receive mutant from mother but
      require father to supply mutant for daughter to be affected).
    """
    m_priors = _get_prior(mother, "x_linked", role="mother")
    f_priors = _get_prior(father, "x_linked", role="father")

    def mother_transmit_prob(mother, priors):
        status = mother.get("status")
        if status == "affected":
            return 1.0
        if status == "carrier":
            return 0.5
        if status == "unaffected":
            return 0.0
        # unknown
        return priors.get("carrier", 0.0) * 0.5 + priors.get("affected", 0.0) * 1.0

    def father_transmit_prob_to_daughter(father, priors):
        status = father.get("status")
        if status == "affected":
            # affected male (XrY) gives mutant X to all daughters
            return 1.0
        if status == "unaffected":
            return 0.0
        # unknown father: use prior probability that father is affected
        return priors.get("affected", 0.0)

    p_m = mother_transmit_prob(mother, m_priors)
    if child_sex == "male":
        # Male child receives single X from mother
        risk = p_m
        return {
            "min": risk,
            "max": risk,
            "confidence": confidence_level(risk, risk),
            "model": "x_linked_recessive",
            "factors": [
                f"Father status: {father['status']}",
                f"Mother status: {mother['status']}",
                "Male child receives X only from mother"
            ]
        }

    # female child: must receive mutant X from both parents
    p_f_daughter = father_transmit_prob_to_daughter(father, f_priors)
    risk = p_m * p_f_daughter

    return {
        "min": risk,
        "max": risk,
        "confidence": confidence_level(risk, risk),
        "model": "x_linked_recessive",
        "factors": [
            f"Father status: {father['status']}",
            f"Mother status: {mother['status']}",
            "Female child requires mutant X from both parents to be affected"
        ]
    }


def calculate_risk(inheritance_type, parent1, parent2, child_sex):
    """Top-level API.

    `parent1` is interpreted as father and `parent2` as mother throughout.
    This consistent ordering avoids ambiguous swaps used previously.
    """
    validate_inputs(parent1, parent2, child_sex, inheritance_type)

    father = parent1
    mother = parent2

    if inheritance_type == "autosomal_recessive":
        return autosomal_recessive_risk(father, mother)

    if inheritance_type == "autosomal_dominant":
        return autosomal_dominant_risk(father, mother)

    if inheritance_type == "x_linked":
        return x_linked_recessive_risk(father, mother, child_sex)

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

    # Use more informative priors where appropriate
    if inheritance_type == "autosomal_recessive":
        p1_priors = _get_prior(parent1, "autosomal_recessive")
        p2_priors = _get_prior(parent2, "autosomal_recessive")
        prior_p1 = parent1.get("carrier_probability", p1_priors.get("carrier", 0.0))
        prior_p2 = parent2.get("carrier_probability", p2_priors.get("carrier", 0.0))
    elif inheritance_type == "autosomal_dominant":
        p1_priors = _get_prior(parent1, "autosomal_dominant")
        p2_priors = _get_prior(parent2, "autosomal_dominant")
        prior_p1 = parent1.get("affected_probability", p1_priors.get("affected", 0.0))
        prior_p2 = parent2.get("affected_probability", p2_priors.get("affected", 0.0))
    elif inheritance_type == "x_linked":
        p1_priors = _get_prior(parent1, "x_linked", role="father")
        p2_priors = _get_prior(parent2, "x_linked", role="mother")
        prior_p1 = parent1.get("affected_probability", p1_priors.get("affected", 0.0))
        prior_p2 = parent2.get("carrier_probability", p2_priors.get("carrier", 0.0))
    else:
        prior_p1 = get_carrier_probability(parent1)
        prior_p2 = get_carrier_probability(parent2)

    # --- AUTOSOMAL RECESSIVE ---
    if inheritance_type == "autosomal_recessive":
        if child_outcome == "affected":
            # Affected child requires both parents to contribute mutant allele.
            # Therefore each parent must be at least a carrier (or affected).
            if parent1.get("status") != "unaffected":
                parent1["carrier_probability"] = 1.0
            else:
                parent1["carrier_probability"] = 0.0
            if parent2.get("status") != "unaffected":
                parent2["carrier_probability"] = 1.0
            else:
                parent2["carrier_probability"] = 0.0

        elif child_outcome == "unaffected":
            # Update posterior P(parent is carrier | child unaffected).
            # For a given parent (e.g. parent1), consider two scenarios for the other parent:
            # - other carrier: P(unaffected) = 0.75
            # - other non-carrier: P(unaffected) = 1.0
            # Weighted by prior on the other parent.
            other_prior_p2 = prior_p2
            # Probability child unaffected given parent1 is carrier:
            p_unaffected_given_p1_carrier = 0.5 * (1 - 0.5 * other_prior_p2) + 0.5 * 1.0 * (1 - other_prior_p2)
            # Simpler (exact) approach: compute marginal likelihoods directly
            # Use approximate but conservative update: P(unaffected|carrier)=0.75, P(unaffected|noncarrier)=1.0
            likelihood_carrier = 0.75
            likelihood_noncarrier = 1.0

            if 0.0 < prior_p1 < 1.0:
                posterior_p1 = (likelihood_carrier * prior_p1) / (
                    likelihood_carrier * prior_p1 + likelihood_noncarrier * (1 - prior_p1)
                )
                parent1["carrier_probability"] = posterior_p1

            if 0.0 < prior_p2 < 1.0:
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
        # parent1 is father, parent2 is mother
        father = parent1
        mother = parent2
        m_priors = _get_prior(mother, "x_linked", role="mother")

        if child_outcome == "affected":
            if child_sex == "male":
                # Affected son implies mother must carry at least one mutant X
                if mother.get("status") != "unaffected":
                    mother["carrier_probability"] = 1.0
                else:
                    mother["carrier_probability"] = 0.0
            elif child_sex == "female":
                # Affected daughter requires mutant from both parents
                if father.get("status") != "unaffected":
                    father["affected_probability"] = 1.0
                else:
                    father["affected_probability"] = 0.0
                if mother.get("status") != "unaffected":
                    mother["carrier_probability"] = 1.0
                else:
                    mother["carrier_probability"] = 0.0

        elif child_outcome == "unaffected":
            if child_sex == "male":
                # Unaffected son lowers mother's carrier posterior:
                prior_carrier = prior_p2
                if 0.0 < prior_carrier < 1.0:
                    # P(son unaffected | mother carrier) = 0.5
                    # P(son unaffected | mother non-carrier) = 1.0
                    posterior = (0.5 * prior_carrier) / (0.5 * prior_carrier + 1.0 * (1 - prior_carrier))
                    mother["carrier_probability"] = max(0.0, min(1.0, posterior))
            elif child_sex == "female":
                # Unaffected daughter gives weaker evidence against maternal carrier
                prior_carrier = prior_p2
                if 0.0 < prior_carrier < 1.0:
                    # Approximate update: P(daughter unaffected | mother carrier) ~= 0.75
                    posterior = (0.75 * prior_carrier) / (0.75 * prior_carrier + 1.0 * (1 - prior_carrier))
                    mother["carrier_probability"] = max(0.0, min(1.0, posterior))


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
