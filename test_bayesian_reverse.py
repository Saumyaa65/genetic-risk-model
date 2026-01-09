#!/usr/bin/env python
"""
Test script for Bayesian reverse logic
"""
import sys
sys.path.insert(0, 'src')

from genetics_logic import calculate_risk_with_observation

# Test 1: Autosomal Recessive - Child is Affected
print("=" * 60)
print("Test 1: Autosomal Recessive - Child is Affected")
print("=" * 60)

parent1 = {"status": "unknown"}
parent2 = {"status": "unknown"}

result = calculate_risk_with_observation(
    inheritance_type="autosomal_recessive",
    parent1=parent1,
    parent2=parent2,
    child_sex="male",
    observed_child_outcome="affected"
)

print(f"Original Risk: {result['min']:.2%} - {result['max']:.2%}")
print(f"Confidence: {result['confidence']}")
print(f"Bayesian Update Applied: {'bayesian_update' in result}")
if 'bayesian_update' in result:
    print(f"Parent 1 Carrier Prob: {result['bayesian_update']['parent1_carrier_probability']:.2%}")
    print(f"Parent 2 Carrier Prob: {result['bayesian_update']['parent2_carrier_probability']:.2%}")
    print(f"Updated Risk: {result['bayesian_update']['updated_risk']['min']:.2%} - {result['bayesian_update']['updated_risk']['max']:.2%}")

# Test 2: Autosomal Recessive - Child is Unaffected
print("\n" + "=" * 60)
print("Test 2: Autosomal Recessive - Child is Unaffected")
print("=" * 60)

parent1 = {"status": "unknown"}
parent2 = {"status": "unknown"}

result = calculate_risk_with_observation(
    inheritance_type="autosomal_recessive",
    parent1=parent1,
    parent2=parent2,
    child_sex="male",
    observed_child_outcome="unaffected"
)

print(f"Original Risk: {result['min']:.2%} - {result['max']:.2%}")
print(f"Confidence: {result['confidence']}")
print(f"Bayesian Update Applied: {'bayesian_update' in result}")
if 'bayesian_update' in result:
    print(f"Parent 1 Carrier Prob: {result['bayesian_update']['parent1_carrier_probability']:.2%}")
    print(f"Parent 2 Carrier Prob: {result['bayesian_update']['parent2_carrier_probability']:.2%}")
    print(f"Updated Risk: {result['bayesian_update']['updated_risk']['min']:.2%} - {result['bayesian_update']['updated_risk']['max']:.2%}")

# Test 3: Autosomal Dominant - Child is Affected
print("\n" + "=" * 60)
print("Test 3: Autosomal Dominant - Child is Affected")
print("=" * 60)

parent1 = {"status": "unknown"}
parent2 = {"status": "unknown"}

result = calculate_risk_with_observation(
    inheritance_type="autosomal_dominant",
    parent1=parent1,
    parent2=parent2,
    child_sex="male",
    observed_child_outcome="affected"
)

print(f"Original Risk: {result['min']:.2%} - {result['max']:.2%}")
print(f"Confidence: {result['confidence']}")
print(f"Bayesian Update Applied: {'bayesian_update' in result}")
if 'bayesian_update' in result:
    print(f"Parent 1 Carrier Prob: {result['bayesian_update']['parent1_carrier_probability']:.2%}")
    print(f"Parent 2 Carrier Prob: {result['bayesian_update']['parent2_carrier_probability']:.2%}")
    print(f"Updated Risk: {result['bayesian_update']['updated_risk']['min']:.2%} - {result['bayesian_update']['updated_risk']['max']:.2%}")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)
