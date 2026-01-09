from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from genetics_logic import calculate_risk_with_observation
from explanation_generator import generate_explanation

app = FastAPI(title="Genetic Risk Modeling Service")


# -------- Input schema --------
class Parent(BaseModel):
    status: str


class RiskRequest(BaseModel):
    inheritance_type: str
    parent1: Parent
    parent2: Parent
    child_sex: str
    observed_child_outcome: Optional[str] = None


# -------- API endpoint --------
@app.post("/calculate-risk")
def calculate_risk_endpoint(data: RiskRequest):
    # Convert Pydantic models to dicts
    parent1 = data.parent1.dict()
    parent2 = data.parent2.dict()

    # Step 1: Calculate risk
    risk_output = calculate_risk_with_observation(
        inheritance_type=data.inheritance_type,
        parent1=parent1,
        parent2=parent2,
        child_sex=data.child_sex,
        observed_child_outcome=data.observed_child_outcome
    )

    # Step 2: Generate explanation
    explanation = generate_explanation(
        risk_output=risk_output,
        child_sex=data.child_sex,
        observed_child_outcome=data.observed_child_outcome
    )

    # Step 3: Return response
    return {
        "risk": risk_output,
        "explanation": explanation
    }
