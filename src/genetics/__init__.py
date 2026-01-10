"""
Genetics models package.

Provides interfaces and implementations for genetic risk calculation models.
"""

from .model import GeneticsModel
from .two_gen import TwoGenModel
from .three_gen import ThreeGenModel
from .factory import create_model

__all__ = ['GeneticsModel', 'TwoGenModel', 'ThreeGenModel', 'create_model']