import os
from google import genai
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# SYSTEM_PROMPT = """
# You are an explanation generator for a genetic risk modeling system.

# Rules:
# - Do NOT change or reinterpret numbers.
# - Do NOT infer new genetic facts.
# - Do NOT make medical or diagnostic claims.
# - Use probabilistic, non-deterministic language only.
# - Explain the reasoning strictly using the provided factors.
# - Output a single concise paragraph.
# - If an observed child outcome is provided, explain how this observation affects confidence and reasoning without implying certainty or diagnosis.
# """

SYSTEM_PROMPT = """
You explain genetic risk to a general audience with no medical background.

Rules:
- Use very simple, everyday language.
- Avoid scientific or medical jargon.
- Do NOT use terms like "allele", "phenotype", "genotype", or "inheritance framework".
- Explain risk using simple ideas like chance, sharing, or passing traits.
- Do NOT change or reinterpret numbers.
- Do NOT infer new genetic facts.
- Do NOT make medical or diagnostic claims.
- Use probabilistic, non-deterministic language only.
- Explain the reasoning strictly using the provided factors.
- Output a single short paragraph.
- If an observed child outcome is provided, explain it as "this fits what we expected" or "this reduces uncertainty", without implying certainty or diagnosis.
- Write as if explaining to a high school student or a parent.
"""


DISCLAIMER = (
    "This output represents a probabilistic model for educational purposes only "
    "and does not provide medical diagnosis or clinical guidance."
)


def generate_explanation(
    risk_output: dict,
    child_sex: str,
    observed_child_outcome: str | None = None
) -> str:
    """
    Generates a human-readable explanation of genetic risk.
    Uses LLM first, falls back to deterministic text if LLM fails.
    """

    prompt = {
        "inheritance_model": risk_output.get("model"),
        "risk_min": risk_output.get("min"),
        "risk_max": risk_output.get("max"),
        "confidence": risk_output.get("confidence"),
        "child_sex": child_sex,
        "factors": risk_output.get("factors", []),

        "observed_child_outcome": observed_child_outcome,
        "reverse_update_applied": observed_child_outcome == "affected"
    }

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                SYSTEM_PROMPT,
                f"Input data:\n{prompt}\n\nGenerate the explanation."
            ]
        )

        text = response.text.strip()
        if text:
            return text + "\n\n" + DISCLAIMER

    except Exception as e:
        print("LLM failed, using fallback:", e)

    return fallback_explanation(prompt) + "\n\n" + DISCLAIMER


def fallback_explanation(prompt: dict) -> str:
    """
    Deterministic explanation if LLM is unavailable.
    """

    min_r = int(prompt["risk_min"] * 100)
    max_r = int(prompt["risk_max"] * 100)

    # Observed affected child → reverse inference explanation
    if prompt.get("observed_child_outcome") == "affected":
        return (
            "An observed affected outcome provides evidence that both parents likely carry "
            "the relevant allele, which reduces uncertainty in the inheritance assumptions. "
            f"The estimated risk remains {min_r}%, "
            f"with {prompt['confidence']} confidence."
        )

    # Exact probability
    if min_r == max_r:
        return (
            f"Based on the provided family information, the estimated risk is {min_r}%. "
            f"The confidence in this estimate is {prompt['confidence']}."
        )

    # Probability range
    return (
        f"Based on the provided family information, the estimated risk ranges between "
        f"{min_r}% and {max_r}%. This range reflects uncertainty due to incomplete information. "
        f"The confidence in this estimate is {prompt['confidence']}."
    )
