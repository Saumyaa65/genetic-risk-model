from genetics_logic import calculate_risk, calculate_risk_with_observation

print("=== Forward calculation test ===")

result = calculate_risk(
    inheritance_type="autosomal_recessive",
    parent1={"status": "carrier"},
    parent2={"status": "carrier"},
    child_sex="male"
)

print(result)

print("\n=== Reverse calculation (observed child) test ===")

parent1 = {"status": "unknown"}
parent2 = {"status": "unknown"}

# Step 1: forward calculation BEFORE observation
print("Before observation:")
print(
    calculate_risk_with_observation(
        inheritance_type="autosomal_recessive",
        parent1=parent1,
        parent2=parent2,
        child_sex="male"
    )
)

# Step 2: observe an affected child (TRIGGERS reverse update)
print("\nObserving affected child...")
calculate_risk_with_observation(
    inheritance_type="autosomal_recessive",
    parent1=parent1,
    parent2=parent2,
    child_sex="male",
    observed_child_outcome="affected"
)

# Step 3: check updated parents
print("\nUpdated parent probabilities:")
print("Parent 1:", parent1)
print("Parent 2:", parent2)
