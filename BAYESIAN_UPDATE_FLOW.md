# Bayesian Update Flow: "Recalculate Parent Risk" Button

## Overview
This document explains how the "Recalculate Parent Risk" button works, including which files are involved and the complete data flow.

## User Interaction Flow

### 1. User Interface (Frontend)
**File:** `genetic-risk-model/client/src/pages/Calculator.tsx`

**Location:** Lines 249-258 (Button definition)
- User selects an observed child outcome from dropdown (affected/unaffected)
- User clicks "Recalculate Parent Risk" button
- Button handler: `handleRecalculateParentRisk()` (lines 50-78)

**Button Handler Steps:**
1. Validates that an outcome is selected (not "unknown")
2. Gets current form data using `form.getValues()`
3. Prepares data with `observed_child_outcome` field
4. Optionally computes local Bayesian fallback for immediate UI feedback
5. Calls `calculateWithObservation()` mutation
6. Switches view to result step

### 2. API Call (Frontend Hook)
**File:** `genetic-risk-model/client/src/hooks/use-calculations.ts`

**Function:** `useCalculateRisk()` (lines 22-72)

**Process:**
1. Creates a mutation using React Query's `useMutation`
2. Sends POST request to `/calculate-risk` endpoint
3. Request body includes:
   - `inheritance_type`: The inheritance pattern (autosomal_recessive, autosomal_dominant, x_linked)
   - `parent1`: Mother status object
   - `parent2`: Father status object
   - `child_sex`: Child's sex
   - `observed_child_outcome`: "affected" or "unaffected" (the key field for Bayesian update)

### 3. Backend API Endpoint
**File:** `genetic-risk-model/python-service/app.py`

**Endpoint:** `POST /calculate-risk` (lines 25-51)

**Process:**
1. Receives `RiskRequest` with all parameters
2. Converts Pydantic models to dictionaries
3. Calls `calculate_risk_with_observation()` from genetics_logic
4. Calls `generate_explanation()` from explanation_generator
5. Returns JSON response with:
   - `risk`: Risk calculation result (includes `bayesian_update` if applicable)
   - `explanation`: Human-readable explanation

### 4. Risk Calculation with Bayesian Update
**File:** `genetic-risk-model/src/genetics_logic.py`

**Function:** `calculate_risk_with_observation()` (lines 261-314)

**Process:**
1. **Forward Calculation (Step 1):**
   - Calls `calculate_risk()` with original parent statuses
   - Returns initial risk estimate

2. **Bayesian Update (Step 2):**
   - Only executes if `observed_child_outcome` is provided and not "unknown"
   - Creates copies of parent dictionaries to avoid mutating originals
   - Calls `reverse_update_parents_from_child()` to update parent carrier probabilities
   - Recalculates risk using updated parent probabilities
   - Attaches Bayesian update metadata to result

**Function:** `reverse_update_parents_from_child()` (lines 150-259)

**Process:**
- Updates parent `carrier_probability` based on observed child outcome
- Uses proper Bayesian inference for each inheritance type:

  **Autosomal Recessive:**
  - If child affected → Both parents must be carriers (probability = 1.0)
  - If child unaffected → Updates probabilities using Bayes' theorem

  **Autosomal Dominant:**
  - If child affected → At least one parent must be affected
  - Calculates posterior probabilities using Bayes' theorem
  - Accounts for 50% transmission probability from affected parent

  **X-Linked:**
  - If male child affected → Mother must be carrier
  - If female child affected → Both parents must contribute
  - Updates probabilities accordingly

### 5. Risk Calculation Functions
**File:** `genetic-risk-model/src/genetics_logic.py`

**Functions:**
- `autosomal_recessive_risk()` (lines 63-79)
- `autosomal_dominant_risk()` (lines 82-98) - **Updated to use carrier_probability**
- `x_linked_recessive_risk()` (lines 101-127)

**Key Change:**
- `autosomal_dominant_risk()` now uses `get_carrier_probability()` to respect Bayesian updates
- This ensures updated parent probabilities are reflected in risk calculations

### 6. Explanation Generation
**File:** `genetic-risk-model/src/explanation_generator.py`

**Function:** `generate_explanation()` (lines 49-87)

**Process:**
1. Attempts to use LLM (Gemini) for natural language explanation
2. Falls back to `fallback_explanation()` if LLM fails
3. Provides inheritance-type-specific explanations for Bayesian updates

### 7. Response Display (Frontend)
**File:** `genetic-risk-model/client/src/pages/Calculator.tsx`

**Location:** Lines 268-316 (Bayesian Update Results Card)

**Display Components:**
1. **Bayesian Update Details Card:**
   - Original Risk
   - Confidence level
   - Bayesian Update Applied (Yes/No)
   - Mother Carrier Probability
   - Father Carrier Probability
   - Updated Risk Range

2. **Clinical Explanation Card:**
   - Human-readable explanation of the Bayesian update
   - Explains how the observed outcome affects parent probabilities

## Data Flow Summary

```
User clicks button
    ↓
handleRecalculateParentRisk() [Calculator.tsx]
    ↓
calculateWithObservation() [use-calculations.ts hook]
    ↓
POST /calculate-risk [app.py]
    ↓
calculate_risk_with_observation() [genetics_logic.py]
    ↓
    ├─→ calculate_risk() [forward calculation]
    └─→ reverse_update_parents_from_child() [Bayesian update]
        └─→ Updates parent carrier_probability
    ↓
    └─→ calculate_risk() [recalculation with updated probabilities]
    ↓
generate_explanation() [explanation_generator.py]
    ↓
Response returned to frontend
    ↓
Display in "Updated Risk Analysis" card [Calculator.tsx]
```

## Key Files Involved

1. **Frontend UI:**
   - `genetic-risk-model/client/src/pages/Calculator.tsx` - Main calculator component
   - `genetic-risk-model/client/src/hooks/use-calculations.ts` - API hook

2. **Backend API:**
   - `genetic-risk-model/python-service/app.py` - FastAPI endpoint

3. **Core Logic:**
   - `genetic-risk-model/src/genetics_logic.py` - Risk calculation and Bayesian updates
   - `genetic-risk-model/src/explanation_generator.py` - Explanation generation

## Important Notes

1. **Bayesian Update Only Applies When:**
   - `observed_child_outcome` is "affected" or "unaffected" (not "unknown")
   - Parent statuses are "unknown" or have probabilities between 0 and 1

2. **Parent Probability Updates:**
   - Updates are stored in `carrier_probability` field on parent dictionaries
   - Original parent statuses are preserved (copies are made)
   - Updated probabilities are used in recalculation

3. **Risk Calculation:**
   - Forward calculation uses original parent statuses
   - Updated risk uses Bayesian-updated parent probabilities
   - Both are included in the response for comparison

