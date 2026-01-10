# Genetic Inheritance Risk Modeling System

An explainable genetic inheritance risk modeling platform that estimates familial risk using Mendelian inheritance rules and Bayesian probability updates.  
Built for education, simulation, and decision-support — not medical diagnosis.

---

## Problem Statement

Genetic risk assessment is complex due to incomplete family information, uncertain carrier status, and multiple inheritance patterns.  
Most real-world scenarios require probabilistic reasoning rather than deterministic predictions.

---

## Solution Overview

This system models genetic inheritance across multiple generations and dynamically updates risk estimates as new family evidence becomes available.  
It mirrors real genetic counseling workflows by combining rule-based inheritance logic with probability updates.

---

## Core Features

- Three-generation inheritance modeling (grandparents → parents → child)
- Support for autosomal recessive, autosomal dominant, and X-linked inheritance
- Probabilistic handling of unknown or uncertain carrier status
- Bayesian probability updates based on observed family outcomes
- Individual child risk calculation
- Probability ranges instead of fixed answers
- Human-readable explanation generation
- Preloaded genetic disorders with auto-filled inheritance logic

---

## Technical Approach

- **Mendelian Inheritance**:  
  Rule-based probability calculations define how traits are passed from parents to children.

- **Bayesian Updating**:  
  Initial probabilities are updated when new evidence is observed, allowing risk estimates to evolve instead of remaining fixed.

---

## Architecture

- **Frontend**: React + Vite  
- **Backend**: Python (FastAPI)  
- **Logic**: Mendelian inheritance engine + Bayesian update module  
- **Communication**: JSON-based API  

---

## Workflow

1. User inputs family data via UI  
2. Data is structured into JSON  
3. Mendelian rules compute forward risk  
4. Bayesian updates refine probabilities if evidence exists  
5. Risk is returned as a probability range  
6. Explanation is generated and displayed

   ![WhatsApp Image 2026-01-09 at 2 40 51 PM](https://github.com/user-attachments/assets/cfb670b9-077e-4578-9fbd-887ff644fd17)
 

---

## Business Perspective

- Market entry through education and research platforms
- SaaS licensing and API access for scaling
- Premium reports and disorder modules as future offerings

---

## Ethical Disclaimer

This project is for educational and analytical purposes only.  
It does not provide medical diagnosis or clinical advice.

---

## Future Scope

- Multi-child Bayesian inference
- PDF risk reports
- Expanded disorder database
- Enhanced pedigree visualization
