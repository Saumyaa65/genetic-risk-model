"""
Factory for creating genetics models.

Provides a factory function to create the appropriate genetics model
based on the number of generations required.
"""

from typing import Dict, Any, Union
from .model import GeneticsModel
from .two_gen import TwoGenModel
from .three_gen import ThreeGenModel


def create_model(
    generations: int = 2,
    **kwargs
) -> GeneticsModel:
    """
    Factory function to create the appropriate genetics model.
    
    Args:
        generations: Number of generations (2 or 3). Defaults to 2.
        **kwargs: Additional keyword arguments passed to model constructor.
                  For ThreeGenModel, can include 'epsilon' for numerical stability.
    
    Returns:
        GeneticsModel instance (TwoGenModel or ThreeGenModel)
    
    Raises:
        ValueError: If generations is not 2 or 3
    
    Examples:
        >>> # Create a 2-generation model
        >>> model = create_model(generations=2)
        >>> 
        >>> # Create a 3-generation model with custom epsilon
        >>> model = create_model(generations=3, epsilon=1e-12)
    """
    if generations == 2:
        return TwoGenModel()
    elif generations == 3:
        epsilon = kwargs.get("epsilon", 1e-10)
        return ThreeGenModel(epsilon=epsilon)
    else:
        raise ValueError(f"Unsupported number of generations: {generations}. Must be 2 or 3.")


def create_model_from_params(params: Dict[str, Any]) -> GeneticsModel:
    """
    Create a genetics model from a parameters dictionary.
    
    Args:
        params: Dictionary containing model parameters.
                Should include 'generations' key (2 or 3).
                Additional keys are passed to model constructor.
    
    Returns:
        GeneticsModel instance
    
    Examples:
        >>> params = {"generations": 3, "epsilon": 1e-12}
        >>> model = create_model_from_params(params)
    """
    generations = params.get("generations", 2)
    kwargs = {k: v for k, v in params.items() if k != "generations"}
    return create_model(generations=generations, **kwargs)