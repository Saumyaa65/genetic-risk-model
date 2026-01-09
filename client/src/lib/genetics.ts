import { z } from 'zod';
import { type InsertCalculation } from '@shared/schema';

// This library handles the "local" logic requested in the implementation notes.
// It simulates what the backend would return.

export const RISK_LEVELS = {
  HIGH: { label: "High Risk", color: "text-red-600", bg: "bg-red-50", border: "border-red-200" },
  MEDIUM: { label: "Moderate Risk", color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200" },
  LOW: { label: "Low Risk", color: "text-green-600", bg: "bg-green-50", border: "border-green-200" },
};

export interface CalculationResult {
  riskPercentage: number;
  riskRange: string;
  confidence: "High" | "Medium" | "Low";
  reasoning: string[];
  explanation: string;
  // Optional Bayesian metadata when an observed outcome is provided
  bayesianUpdate?: {
    parent1_carrier_probability: number;
    parent2_carrier_probability: number;
    updated_risk: { min: number; max: number } | null;
  } | null;
}

export function calculateLocalRisk(data: InsertCalculation & { observed_child_outcome?: string }): CalculationResult {
  const { inheritancePattern, motherStatus, fatherStatus } = data;
  const observed = (data as any).observed_child_outcome;
  
  let riskPercentage = 0;
  let riskRange = "0% - 10%";
  let reasoning: string[] = [];
  let explanation = "";
  let bayesian: CalculationResult['bayesianUpdate'] = null;

  // Simplified Mock Logic
  if (inheritancePattern === "autosomal_recessive") {
    if (motherStatus === "carrier" && fatherStatus === "carrier") {
      riskPercentage = 25;
      riskRange = "20% - 30%";
      reasoning = [
        "Mother is a Carrier",
        "Father is a Carrier",
        "Autosomal Recessive Pattern"
      ];
      explanation = "When both parents are carriers of an autosomal recessive condition, there is a 25% chance with each pregnancy that the child will inherit the mutated gene from both parents and be affected.";
    } else if ((motherStatus === "carrier" && fatherStatus === "affected") || (motherStatus === "affected" && fatherStatus === "carrier")) {
      riskPercentage = 50;
      riskRange = "45% - 55%";
      reasoning = ["One parent Affected, one Carrier"];
      explanation = "There is a 50% chance the child will be affected.";
    } else if (motherStatus === "affected" && fatherStatus === "affected") {
      riskPercentage = 100;
      riskRange = "> 99%";
      reasoning = ["Both parents Affected"];
      explanation = "All children will inherit the recessive genes.";
    } else {
       riskPercentage = 0; // Simplified for demo
       reasoning = ["At least one parent is unaffected/non-carrier"];
       explanation = "Risk is low as both parents do not carry the gene.";
    }
  } else if (inheritancePattern === "autosomal_dominant") {
     if (motherStatus === "affected" || fatherStatus === "affected") {
       riskPercentage = 50;
       riskRange = "45% - 55%";
       reasoning = ["One parent Affected (Heterozygous presumed)"];
       explanation = "In autosomal dominant conditions, if one parent is affected (heterozygous), there is a 50% chance of passing the condition.";
     }
  }

  // Fallback for demo
  if (riskPercentage === 0 && (motherStatus !== 'unaffected' || fatherStatus !== 'unaffected')) {
      riskPercentage = 5; 
      riskRange = "< 5%";
      explanation = "Based on the provided statuses, the specific risk calculation is complex or low. A detailed genetic counseling session is recommended.";
  }

  // If an observed child outcome is provided, compute a simple Bayesian update for parents
  if (observed && observed !== 'unknown') {
    // simple priors from statuses
    const prior1 = motherStatus === 'carrier' || motherStatus === 'affected' ? 1 : motherStatus === 'unknown' ? 0.5 : 0;
    const prior2 = fatherStatus === 'carrier' || fatherStatus === 'affected' ? 1 : fatherStatus === 'unknown' ? 0.5 : 0;

    if (inheritancePattern === 'autosomal_recessive') {
      if (observed === 'affected') {
        bayesian = {
          parent1_carrier_probability: 1.0,
          parent2_carrier_probability: 1.0,
          updated_risk: { min: 0.25, max: 0.25 }
        };
        // reflect updated risk in display values
        riskPercentage = 25;
        riskRange = '25% - 25%';
        explanation = 'Observed affected child implies both parents are likely carriers.';
      } else if (observed === 'unaffected') {
        // posterior = (likelihood_carrier * prior) / (likelihood_carrier*prior + likelihood_noncarrier*(1-prior))
        const likelihood_carrier = 0.75;
        const likelihood_noncarrier = 1.0;
        const post1 = prior1 > 0 && prior1 < 1 ? (likelihood_carrier * prior1) / (likelihood_carrier * prior1 + likelihood_noncarrier * (1 - prior1)) : prior1;
        const post2 = prior2 > 0 && prior2 < 1 ? (likelihood_carrier * prior2) / (likelihood_carrier * prior2 + likelihood_noncarrier * (1 - prior2)) : prior2;

        bayesian = {
          parent1_carrier_probability: post1,
          parent2_carrier_probability: post2,
          // compute updated child risk
          updated_risk: { min: post1 * post2 * 0.25, max: post1 * post2 * 0.25 }
        };

        // reflect updated risk in display values
        const updatedRiskPct = bayesian.updated_risk.min * 100;
        riskPercentage = Math.round(updatedRiskPct);
        riskRange = `${updatedRiskPct.toFixed(2)}% - ${updatedRiskPct.toFixed(2)}%`;
        explanation = 'Observed unaffected child reduces the posterior probability that both parents are carriers.';
      }
    }
    // other inheritance patterns could be added similarly
  }

  return {
    riskPercentage,
    riskRange,
    confidence: "High",
    reasoning,
    explanation,
    bayesianUpdate: bayesian,
  };
}
