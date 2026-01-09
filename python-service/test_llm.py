from explanation_generator import generate_explanation

risk_output = {
    "model": "autosomal_recessive",
    "min": 0.25,
    "max": 0.25,
    "confidence": "high",
    "factors": [
        "Parent 1 status: carrier",
        "Parent 2 status: carrier",
        "Condition requires two recessive alleles"
    ]
}

print(generate_explanation(risk_output, child_sex="male"))
print()
print(generate_explanation(
    risk_output,
    child_sex="male",
    observed_child_outcome="affected"
))
