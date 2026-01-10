"""
Base interface for genetics models.

Defines the common interface that all genetics models must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class GeneticsModel(ABC):
    """
    Abstract base class for genetics risk calculation models.
    
    All genetics models must implement:
    - compute_risk: Forward calculation of risk given pedigree and parameters
    - bayesian_update: Reverse Bayesian update given observations, priors, and parameters
    """
    
    @abstractmethod
    def compute_risk(self, pedigree: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute the genetic risk for the target individual given pedigree information.
        
        Args:
            pedigree: Dictionary containing pedigree structure and phenotypes.
                     For 2-gen: {parent1: {...}, parent2: {...}, child: {...}}
                     For 3-gen: {grandparent: {...}, parent: {...}, child: {...}}
            params: Dictionary of model parameters (inheritance_type, child_sex, etc.)
        
        Returns:
            Dictionary containing:
            - min: Minimum risk probability (float)
            - max: Maximum risk probability (float)
            - confidence: Confidence level (str: "high", "medium", "low")
            - model: Model type identifier (str)
            - factors: List of explanatory factors (list[str])
            - joint_posteriors: (optional) Joint posterior probabilities (dict)
            - marginal_posteriors: (optional) Marginal posterior probabilities (dict)
        """
        pass
    
    @abstractmethod
    def bayesian_update(
        self,
        observations: Dict[str, Any],
        priors: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform Bayesian update given observed phenotypes and prior probabilities.
        
        Args:
            observations: Dictionary of observed phenotypes for individuals in pedigree
            priors: Dictionary of prior probabilities for genotypes/statuses
            params: Dictionary of model parameters (inheritance_type, etc.)
        
        Returns:
            Dictionary containing:
            - updated_priors: Updated prior probabilities after Bayesian inference
            - posterior_probabilities: Posterior probabilities for each individual
            - joint_posteriors: (optional) Joint posterior distributions
            - marginal_posteriors: (optional) Marginal posterior distributions
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name/identifier of this model."""
        pass
    
    @property
    @abstractmethod
    def generation_count(self) -> int:
        """Return the number of generations this model handles (2 or 3)."""
        pass