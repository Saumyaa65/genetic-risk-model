DATA FLOW OVERVIEW

1. The UI loads familyData.json into application state.
2. User changes:
   - inheritanceType OR
   - a person's status (affected / carrier / unknown).
3. Updated familyData object is passed to calculateRisk().
4. calculateRisk() reads:
   - people[]
   - relationships[]
   - inheritanceType
5. calculateRisk() returns per-child risk:
   - min_probability
   - max_probability
   - structured reasoning factors.
6. Structured output is passed to generateExplanation().
7. UI displays:
   - probability range
   - natural language explanation.
