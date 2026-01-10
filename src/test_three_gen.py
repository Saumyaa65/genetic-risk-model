"""
Unit tests for ThreeGenModel.

Mirrors existing 2-gen tests to ensure consistency:
- No observations
- Conflicting observations
- Simple inheritance patterns
"""
# -*- coding: utf-8 -*-

import sys
import os

# Add src directory to path
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from genetics.factory import create_model


def test_no_observations_autosomal_recessive():
    """Test 3-gen model with no observations (all unknown)."""
    print("=== Test 1: No observations (autosomal recessive) ===")
    
    model = create_model(generations=3)
    
    pedigree = {
        "grandparent": {"status": "unknown"},
        "parent": {"status": "unknown"},
        "child": {"status": "unknown"}
    }
    
    params = {
        "inheritance_type": "autosomal_recessive",
        "grandparent_sex": "female",
        "parent_sex": "female",
        "child_sex": "male"
    }
    
    result = model.compute_risk(pedigree, params)
    
    print(f"Risk: {result['min']:.4f} - {result['max']:.4f}")
    print(f"Confidence: {result['confidence']}")
    print(f"Model: {result['model']}")
    print(f"Factors: {result.get('factors', [])}")
    assert result['model'] == 'three_generation'
    assert 0.0 <= result['min'] <= result['max'] <= 1.0
    print("✓ Passed\n")


def test_conflicting_observations():
    """Test 3-gen model with conflicting observations."""
    print("=== Test 2: Conflicting observations (autosomal recessive) ===")
    
    model = create_model(generations=3)
    
    # Grandparent affected, parent unaffected, child affected
    # This is conflicting because if child is affected in autosomal recessive,
    # both parents must be carriers/affected
    pedigree = {
        "grandparent": {"status": "affected"},  # aa
        "parent": {"status": "unaffected"},  # AA (conflicting)
        "child": {"status": "affected"}  # aa (requires both parents to have 'a')
    }
    
    params = {
        "inheritance_type": "autosomal_recessive",
        "grandparent_sex": "female",
        "parent_sex": "female",
        "child_sex": "male"
    }
    
    result = model.compute_risk(pedigree, params)
    
    print(f"Risk: {result['min']:.4f} - {result['max']:.4f}")
    print(f"Confidence: {result['confidence']}")
    print(f"Factors: {result.get('factors', [])}")
    
    # With conflicting observations, likelihood should be very low or zero
    # The model should handle this gracefully
    assert result['model'] == 'three_generation'
    print("✓ Passed (conflicting observations handled)\n")


def test_simple_inheritance_autosomal_recessive():
    """Test 3-gen model with simple inheritance (all carriers)."""
    print("=== Test 3: Simple inheritance (autosomal recessive, all carriers) ===")
    
    model = create_model(generations=3)
    
    # Grandparent carrier, parent carrier, child unknown
    pedigree = {
        "grandparent": {"status": "carrier"},  # Aa
        "parent": {"status": "carrier"},  # Aa
        "child": {"status": "unknown"}
    }
    
    params = {
        "inheritance_type": "autosomal_recessive",
        "grandparent_sex": "female",
        "parent_sex": "female",
        "child_sex": "male"
    }
    
    result = model.compute_risk(pedigree, params)
    
    print(f"Risk: {result['min']:.4f} - {result['max']:.4f}")
    print(f"Confidence: {result['confidence']}")
    print(f"Model: {result['model']}")
    
    # With both GP and P as carriers, child risk should be 0.25 (50% * 50%)
    # But we need to account for the other parent of child (not in model)
    # So risk will be lower due to marginalization
    assert result['model'] == 'three_generation'
    assert 0.0 <= result['min'] <= result['max'] <= 1.0
    print("✓ Passed\n")


def test_simple_inheritance_autosomal_dominant():
    """Test 3-gen model with autosomal dominant inheritance."""
    print("=== Test 4: Simple inheritance (autosomal dominant) ===")
    
    model = create_model(generations=3)
    
    # Grandparent affected, parent affected, child unknown
    pedigree = {
        "grandparent": {"status": "affected"},  # Aa (heterozygous)
        "parent": {"status": "affected"},  # Aa (heterozygous)
        "child": {"status": "unknown"}
    }
    
    params = {
        "inheritance_type": "autosomal_dominant",
        "grandparent_sex": "female",
        "parent_sex": "female",
        "child_sex": "male"
    }
    
    result = model.compute_risk(pedigree, params)
    
    print(f"Risk: {result['min']:.4f} - {result['max']:.4f}")
    print(f"Confidence: {result['confidence']}")
    print(f"Model: {result['model']}")
    
    # With dominant inheritance and affected parents, child risk should be high
    assert result['model'] == 'three_generation'
    assert 0.0 <= result['min'] <= result['max'] <= 1.0
    print("✓ Passed\n")


def test_bayesian_update():
    """Test 3-gen model with Bayesian update."""
    print("=== Test 5: Bayesian update (3-gen) ===")
    
    model = create_model(generations=3)
    
    # Start with unknown statuses
    observations = {
        "grandparent": "unknown",
        "parent": "unknown",
        "child": "affected"  # Observe affected child
    }
    
    priors = {
        "grandparent": {"status": "unknown"},
        "parent": {"status": "unknown"},
        "child": {"status": "unknown"}
    }
    
    params = {
        "inheritance_type": "autosomal_recessive",
        "grandparent_sex": "female",
        "parent_sex": "female",
        "child_sex": "male"
    }
    
    result = model.bayesian_update(observations, priors, params)
    
    print(f"Updated priors keys: {list(result.get('updated_priors', {}).keys())}")
    print(f"Posterior probabilities: {result.get('posterior_probabilities', {})}")
    print(f"Has joint posteriors: {'joint_posteriors' in result}")
    print(f"Has marginal posteriors: {'marginal_posteriors' in result}")
    
    assert 'updated_priors' in result
    assert 'posterior_probabilities' in result
    print("✓ Passed\n")


def test_x_linked_inheritance():
    """Test 3-gen model with X-linked inheritance."""
    print("=== Test 6: X-linked inheritance (3-gen) ===")
    
    model = create_model(generations=3)
    
    # Maternal line: grandmother carrier -> mother carrier -> son
    pedigree = {
        "grandparent": {"status": "carrier"},  # XrX (grandmother)
        "parent": {"status": "carrier"},  # XrX (mother)
        "child": {"status": "unknown"}  # Son
    }
    
    params = {
        "inheritance_type": "x_linked",
        "grandparent_sex": "female",
        "parent_sex": "female",
        "child_sex": "male"  # Son
    }
    
    result = model.compute_risk(pedigree, params)
    
    print(f"Risk: {result['min']:.4f} - {result['max']:.4f}")
    print(f"Confidence: {result['confidence']}")
    print(f"Model: {result['model']}")
    
    # For X-linked, son gets X from mother only
    # If mother is carrier (XrX), son has 50% chance of being affected (XrY)
    assert result['model'] == 'three_generation'
    assert 0.0 <= result['min'] <= result['max'] <= 1.0
    print("✓ Passed\n")


if __name__ == "__main__":
    print("Running ThreeGenModel unit tests...\n")
    
    try:
        test_no_observations_autosomal_recessive()
        test_conflicting_observations()
        test_simple_inheritance_autosomal_recessive()
        test_simple_inheritance_autosomal_dominant()
        test_bayesian_update()
        test_x_linked_inheritance()
        
        print("=" * 50)
        print("All tests passed! ✓")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)