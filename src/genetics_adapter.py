"""
Adapter module to bridge existing genetics_logic interface to new GeneticsModel system.

This allows the existing calculate_risk_with_observation API to work with
both 2-generation and 3-generation models via the factory.
"""

import sys
import os
from typing import Dict, Any, Optional

# Add src directory to path
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Import existing genetics logic for 2-gen (fallback and compatibility)
from genetics_logic import (
    calculate_risk as calculate_risk_legacy,
    reverse_update_parents_from_child,
    get_carrier_probability
)

# Import new model system
from genetics.factory import create_model
from genetics.model import GeneticsModel


def calculate_risk_with_observation(
    inheritance_type: str,
    parent1: Dict[str, Any],
    parent2: Dict[str, Any],
    child_sex: str,
    observed_child_outcome: Optional[str] = None,
    generations: int = 2
) -> Dict[str, Any]:
    """
    Calculate risk with optional Bayesian update.
    
    This function bridges the existing API to the new GeneticsModel system.
    For 2-generation mode, it uses the existing logic (unchanged behavior).
    For 3-generation mode, it uses the ThreeGenModel.
    
    Args:
        inheritance_type: "autosomal_recessive", "autosomal_dominant", or "x_linked"
        parent1: Dictionary with 'status' field (father for 2-gen, parent for 3-gen)
        parent2: Dictionary with 'status' field (mother for 2-gen, parent for 3-gen)
        child_sex: "male" or "female"
        observed_child_outcome: Optional "affected" or "unaffected" for Bayesian update
        generations: Number of generations (2 or 3), defaults to 2
    
    Returns:
        Dictionary with min, max, confidence, model, factors, and optionally bayesian_update
    """
    # Default to 2-gen (existing behavior unchanged)
    if generations == 2:
        # Use existing legacy function for 2-gen (preserves existing behavior exactly)
        return _calculate_risk_with_observation_legacy(
            inheritance_type, parent1, parent2, child_sex, observed_child_outcome
        )
    
    # Use new 3-generation model
    elif generations == 3:
        return _calculate_risk_with_observation_3gen(
            inheritance_type, parent1, parent2, child_sex, observed_child_outcome
        )
    
    else:
        raise ValueError(f"Unsupported generations: {generations}. Must be 2 or 3.")


def _calculate_risk_with_observation_legacy(
    inheritance_type: str,
    parent1: Dict[str, Any],
    parent2: Dict[str, Any],
    child_sex: str,
    observed_child_outcome: Optional[str] = None
) -> Dict[str, Any]:
    """
    Legacy 2-generation calculation (unchanged behavior).
    Uses existing genetics_logic functions directly.
    """
    # Step 1: forward calculation
    forward_result = calculate_risk_legacy(
        inheritance_type, parent1, parent2, child_sex
    )
    
    # Step 2: reverse update if observed
    if observed_child_outcome is not None and observed_child_outcome != "unknown":
        updated_parent1 = parent1.copy()
        updated_parent2 = parent2.copy()
        
        reverse_update_parents_from_child(
            inheritance_type,
            observed_child_outcome,
            updated_parent1,
            updated_parent2,
            child_sex
        )
        
        updated_result = calculate_risk_legacy(
            inheritance_type, updated_parent1, updated_parent2, child_sex
        )
        
        forward_result["bayesian_update"] = {
            "observed_outcome": observed_child_outcome,
            "parent1_original_status": parent1.get("status"),
            "parent2_original_status": parent2.get("status"),
            "parent1_carrier_probability": updated_parent1.get("carrier_probability", get_carrier_probability(updated_parent1)),
            "parent2_carrier_probability": updated_parent2.get("carrier_probability", get_carrier_probability(updated_parent2)),
            "updated_risk": updated_result
        }
    
    return forward_result


def _calculate_risk_with_observation_3gen(
    inheritance_type: str,
    parent1: Dict[str, Any],
    parent2: Dict[str, Any],
    child_sex: str,
    observed_child_outcome: Optional[str] = None
) -> Dict[str, Any]:
    """
    3-generation calculation using ThreeGenModel.
    
    For 3-gen, we interpret:
    - parent1/grandparent: the grandparent in the lineage
    - parent2/parent: the parent (child of grandparent, parent of child)
    - child: the target child (grandchild of grandparent)
    
    Note: In a full 3-gen model, we'd need grandparent information, but for
    compatibility with the existing API, we use parent1 as grandparent and
    parent2 as parent, with child being the target.
    """
    model = create_model(generations=3)
    
    # Build pedigree for 3-generation model
    # For 3-gen: grandparent -> parent -> child
    # We use parent1 as grandparent, parent2 as parent, and target child
    pedigree = {
        "grandparent": parent1.copy(),
        "parent": parent2.copy(),
        "child": {"status": "unknown"}  # Child is the target (unknown until observed)
    }
    
    # Determine sexes (defaults based on inheritance pattern)
    # For X-linked, use maternal line (female for GP and P)
    # For autosomal, use reasonable defaults (can be overridden in full implementation)
    if inheritance_type == "x_linked":
        grandparent_sex = "female"  # Maternal line for X-linked
        parent_sex = "female"
    else:
        # Autosomal: use default (both female for consistency)
        # In a full implementation, these could be parameterized
        grandparent_sex = "female"
        parent_sex = "female"
    
    params = {
        "inheritance_type": inheritance_type,
        "grandparent_sex": grandparent_sex,
        "parent_sex": parent_sex,
        "child_sex": child_sex
    }
    
    # Forward calculation
    forward_result = model.compute_risk(pedigree, params)
    
    # Bayesian update if child outcome is observed
    if observed_child_outcome is not None and observed_child_outcome != "unknown":
        observations = {
            "grandparent": parent1.get("status", "unknown"),
            "parent": parent2.get("status", "unknown"),
            "child": observed_child_outcome
        }
        
        priors = {
            "grandparent": parent1.copy(),
            "parent": parent2.copy(),
            "child": {"status": "unknown"}
        }
        
        bayesian_result = model.bayesian_update(observations, priors, params)
        
        # Recompute with updated priors
        updated_pedigree = {
            "grandparent": priors["grandparent"],
            "parent": priors["parent"],
            "child": {"status": observed_child_outcome}
        }
        # Update from bayesian result
        if "updated_priors" in bayesian_result:
            if "grandparent" in bayesian_result["updated_priors"]:
                updated_pedigree["grandparent"].update(bayesian_result["updated_priors"]["grandparent"])
            if "parent" in bayesian_result["updated_priors"]:
                updated_pedigree["parent"].update(bayesian_result["updated_priors"]["parent"])
        
        updated_result = model.compute_risk(updated_pedigree, params)
        
        forward_result["bayesian_update"] = {
            "observed_outcome": observed_child_outcome,
            "parent1_original_status": parent1.get("status"),
            "parent2_original_status": parent2.get("status"),
            "parent1_carrier_probability": bayesian_result.get("posterior_probabilities", {}).get("grandparent", {}).get("carrier_probability", 0.0),
            "parent2_carrier_probability": bayesian_result.get("posterior_probabilities", {}).get("parent", {}).get("carrier_probability", 0.0),
            "updated_risk": {
                "min": updated_result.get("min", 0.0),
                "max": updated_result.get("max", 0.0),
                "confidence": updated_result.get("confidence", "low")
            },
            "joint_posteriors": bayesian_result.get("joint_posteriors", {}),
            "marginal_posteriors": bayesian_result.get("marginal_posteriors", {})
        }
    
    return forward_result