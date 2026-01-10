# Three-Generation Genetics Model

## Overview

The `ThreeGenModel` implements a three-generation genetic risk calculation model that considers the relationship: **Grandparent → Parent → Child**. This model uses joint genotype enumeration and Bayesian inference to compute more precise risk estimates by incorporating grandparental information.

## Basic Usage

### Creating a ThreeGenModel

```python
from src.genetics.factory import create_model

# Create a 3-generation model
model = create_model(generations=3)

# Or create with custom epsilon for numerical stability
model = create_model(generations=3, epsilon=1e-12)
```

### Computing Risk

```python
# Define pedigree structure
pedigree = {
    "grandparent": {"status": "carrier"},    # Grandparent status
    "parent": {"status": "carrier"},         # Parent status  
    "child": {"status": "unknown"}           # Target child (prediction)
}

# Define model parameters
params = {
    "inheritance_type": "autosomal_recessive",
    "grandparent_sex": "female",             # Sex of grandparent
    "parent_sex": "female",                  # Sex of parent
    "child_sex": "male"                      # Sex of target child
}

# Compute risk
result = model.compute_risk(pedigree, params)

print(f"Risk: {result['min']:.2%} - {result['max']:.2%}")
print(f"Confidence: {result['confidence']}")
print(f"Marginal posteriors: {result.get('marginal_posteriors', {})}")
```

### Example Output

```python
{
    "min": 0.0025,                    # Minimum risk probability
    "max": 0.0025,                    # Maximum risk probability
    "confidence": "high",              # Confidence level
    "model": "three_generation",       # Model identifier
    "factors": [...],                  # Explanatory factors
    "joint_posteriors": {...},        # Joint genotype probabilities
    "marginal_posteriors": {          # Marginal probabilities per generation
        "grandparent": {"AA": 0.5, "Aa": 0.5, "aa": 0.0},
        "parent": {"AA": 0.25, "Aa": 0.75, "aa": 0.0},
        "child": {"AA": 0.5625, "Aa": 0.375, "aa": 0.0625}
    }
}
```

## Bayesian Update

The model supports Bayesian updates to refine probabilities based on observed phenotypes:

```python
# Define observations
observations = {
    "grandparent": "carrier",          # Observed grandparent status
    "parent": "unknown",               # Parent status (if known)
    "child": "affected"                # Observed child outcome
}

# Define prior probabilities
priors = {
    "grandparent": {"status": "unknown"},
    "parent": {"status": "unknown"},
    "child": {"status": "unknown"}
}

# Parameters
params = {
    "inheritance_type": "autosomal_recessive",
    "grandparent_sex": "female",
    "parent_sex": "female",
    "child_sex": "male"
}

# Perform Bayesian update
result = model.bayesian_update(observations, priors, params)

print(f"Updated posteriors: {result['posterior_probabilities']}")
print(f"Joint posteriors: {result.get('joint_posteriors', {})}")
```

## Supported Inheritance Patterns

### Autosomal Recessive

```python
pedigree = {
    "grandparent": {"status": "carrier"},  # Aa
    "parent": {"status": "carrier"},       # Aa
    "child": {"status": "unknown"}
}

params = {
    "inheritance_type": "autosomal_recessive",
    "grandparent_sex": "female",
    "parent_sex": "female",
    "child_sex": "male"
}
```

### Autosomal Dominant

```python
pedigree = {
    "grandparent": {"status": "affected"},  # Aa (heterozygous)
    "parent": {"status": "affected"},       # Aa (heterozygous)
    "child": {"status": "unknown"}
}

params = {
    "inheritance_type": "autosomal_dominant",
    "grandparent_sex": "female",
    "parent_sex": "female",
    "child_sex": "male"
}
```

### X-Linked Recessive

```python
# Maternal line example
pedigree = {
    "grandparent": {"status": "carrier"},  # XrX (grandmother)
    "parent": {"status": "carrier"},       # XrX (mother)
    "child": {"status": "unknown"}         # Son
}

params = {
    "inheritance_type": "x_linked",
    "grandparent_sex": "female",
    "parent_sex": "female",
    "child_sex": "male"  # Sons inherit X only from mother
}
```

## Status Values

Valid status values for individuals:
- `"affected"` - Observed affected phenotype
- `"carrier"` - Observed carrier (for recessive conditions)
- `"unaffected"` - Observed unaffected (no known mutant allele)
- `"unknown"` - No phenotype/genotype information available

## Advanced Usage

### Handling Missing Data

The model handles missing priors gracefully by using population defaults:
- **Autosomal Recessive**: Carrier prior = 0.01, Affected prior = 0.0001
- **Autosomal Dominant**: Affected prior = 0.001
- **X-Linked**: Mother carrier prior = 0.01, Father affected prior = 0.0005

You can override these by providing explicit probabilities in the individual dictionaries:

```python
pedigree = {
    "grandparent": {
        "status": "unknown",
        "carrier_probability": 0.05  # Custom prior
    },
    "parent": {"status": "unknown"},
    "child": {"status": "unknown"}
}
```

### Numerical Stability

The model uses epsilon (default: 1e-10) to handle:
- Zero likelihood scenarios (conflicting observations)
- Missing priors
- Small state spaces

```python
# Create model with custom epsilon
model = create_model(generations=3, epsilon=1e-12)
```

## Integration with Existing Code

The three-generation model is integrated with the existing API via the `genetics_adapter` module:

```python
from src.genetics_adapter import calculate_risk_with_observation

result = calculate_risk_with_observation(
    inheritance_type="autosomal_recessive",
    parent1={"status": "carrier"},  # Interpreted as grandparent for 3-gen
    parent2={"status": "carrier"},  # Interpreted as parent for 3-gen
    child_sex="male",
    observed_child_outcome=None,
    generations=3  # Use 3-generation model
)
```

## Comparison: 2-Gen vs 3-Gen

- **2-Generation Model**: Considers only Parent → Child relationship. Faster, simpler, uses existing proven logic.
- **3-Generation Model**: Considers Grandparent → Parent → Child. More precise when grandparent information is available, provides joint and marginal posterior distributions.

## Example: Complete Workflow

```python
from src.genetics.factory import create_model

# Create model
model = create_model(generations=3)

# Initial risk calculation
pedigree = {
    "grandparent": {"status": "carrier"},
    "parent": {"status": "unknown"},
    "child": {"status": "unknown"}
}

params = {
    "inheritance_type": "autosomal_recessive",
    "grandparent_sex": "female",
    "parent_sex": "female",
    "child_sex": "male"
}

initial_result = model.compute_risk(pedigree, params)
print(f"Initial risk: {initial_result['min']:.2%}")

# Observe affected child and update
observations = {"grandparent": "carrier", "parent": "unknown", "child": "affected"}
priors = {"grandparent": {"status": "carrier"}, "parent": {"status": "unknown"}, "child": {"status": "unknown"}}

bayesian_result = model.bayesian_update(observations, priors, params)
print(f"Parent carrier probability (updated): {bayesian_result['posterior_probabilities']['parent'].get('carrier_probability', 0):.2%}")

# Recompute with updated priors
updated_pedigree = {
    "grandparent": bayesian_result["updated_priors"]["grandparent"],
    "parent": bayesian_result["updated_priors"]["parent"],
    "child": {"status": "affected"}
}

final_result = model.compute_risk(updated_pedigree, params)
print(f"Final risk: {final_result['min']:.2%}")
```

## Running Tests

Run the unit tests to verify functionality:

```bash
python src/test_three_gen.py
```

Tests include:
- No observations scenario
- Conflicting observations handling
- Simple inheritance patterns (autosomal recessive, autosomal dominant)
- Bayesian update functionality
- X-linked inheritance