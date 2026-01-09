from genetics_logic import calculate_risk

result = calculate_risk(
    inheritance_type="autosomal_recessive",
    parent1={"status": "carrier"},
    parent2={"status": "carrier"},
    child_sex="male"
)

print(result)
