from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path to import from src
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from src.genetics_adapter import calculate_risk_with_observation
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
    generations: Optional[int] = 2  # Default to 2-gen for backward compatibility


# -------- API endpoint --------
@app.post("/calculate-risk")
def calculate_risk_endpoint(data: RiskRequest):
    # Convert Pydantic models to dicts
    parent1 = data.parent1.dict()
    parent2 = data.parent2.dict()
    
    # Default to 2-gen if not specified (backward compatibility)
    generations = data.generations if data.generations is not None else 2

    # Step 1: Calculate risk
    risk_output = calculate_risk_with_observation(
        inheritance_type=data.inheritance_type,
        parent1=parent1,
        parent2=parent2,
        child_sex=data.child_sex,
        observed_child_outcome=data.observed_child_outcome,
        generations=generations
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
