"""
Two-generation genetics model.

Wraps the existing 2-generation genetics logic into the GeneticsModel interface.
This model handles parent-child relationships for genetic risk calculation.
"""

from typing import Dict, Any
from .model import GeneticsModel
import sys
import os

# Import existing genetics logic from parent directory
# Add parent directory to path to import genetics_logic
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    from genetics_logic import (
        calculate_risk,
        reverse_update_parents_from_child,
        DEFAULT_PRIORS
    )
except ImportError:
    # Fallback: try relative import if package structure allows
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "genetics_logic",
        os.path.join(_parent_dir, "genetics_logic.py")
    )
    _genetics_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_genetics_module)
    calculate_risk = _genetics_module.calculate_risk
    reverse_update_parents_from_child = _genetics_module.reverse_update_parents_from_child
    DEFAULT_PRIORS = _genetics_module.DEFAULT_PRIORS


class TwoGenModel(GeneticsModel):
    """
    Two-generation genetics model.
    
    Handles parent-child relationships for genetic risk calculation.
    Wraps the existing genetics_logic functions to match the GeneticsModel interface.
    """
    
    def compute_risk(self, pedigree: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute risk for child given parent phenotypes and inheritance pattern.
        
        Args:
            pedigree: Dictionary with keys:
                - parent1: dict with 'status' field (father)
                - parent2: dict with 'status' field (mother)
            params: Dictionary with keys:
                - inheritance_type: str ("autosomal_recessive", "autosomal_dominant", "x_linked")
                - child_sex: str ("male", "female")
        
        Returns:
            Risk calculation result with min, max, confidence, model, factors.
        """
        parent1 = pedigree.get("parent1", {})
        parent2 = pedigree.get("parent2", {})
        
        inheritance_type = params.get("inheritance_type")
        child_sex = params.get("child_sex", "unknown")
        
        if not inheritance_type:
            raise ValueError("inheritance_type is required in params")
        
        # Use existing calculate_risk function
        result = calculate_risk(inheritance_type, parent1, parent2, child_sex)
        
        return result
    
    def bayesian_update(
        self,
        observations: Dict[str, Any],
        priors: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform Bayesian update to refine parent carrier probabilities based on child outcome.
        
        Args:
            observations: Dictionary with:
                - child_outcome: str ("affected", "unaffected", "unknown")
            priors: Dictionary with:
                - parent1: dict with status and optional carrier_probability/affected_probability
                - parent2: dict with status and optional carrier_probability/affected_probability
            params: Dictionary with:
                - inheritance_type: str
                - child_sex: str (optional)
        
        Returns:
            Dictionary with updated_priors containing modified parent1 and parent2 dictionaries.
        """
        parent1 = priors.get("parent1", {}).copy()
        parent2 = priors.get("parent2", {}).copy()
        
        child_outcome = observations.get("child_outcome")
        inheritance_type = params.get("inheritance_type")
        child_sex = params.get("child_sex", "unknown")
        
        if not inheritance_type:
            raise ValueError("inheritance_type is required in params")
        
        # Use existing reverse_update_parents_from_child function
        if child_outcome and child_outcome != "unknown":
            reverse_update_parents_from_child(
                inheritance_type,
                child_outcome,
                parent1,
                parent2,
                child_sex
            )
        
        return {
            "updated_priors": {
                "parent1": parent1,
                "parent2": parent2
            },
            "posterior_probabilities": {
                "parent1": parent1.get("carrier_probability", parent1.get("affected_probability")),
                "parent2": parent2.get("carrier_probability", parent2.get("affected_probability"))
            }
        }
    
    @property
    def model_name(self) -> str:
        """Return the model name."""
        return "two_generation"
    
    @property
    def generation_count(self) -> int:
        """Return the number of generations (2)."""
        return 2