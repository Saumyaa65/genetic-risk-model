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
}

export function calculateLocalRisk(data: InsertCalculation): CalculationResult {
  const { inheritancePattern, motherStatus, fatherStatus } = data;
  
  let riskPercentage = 0;
  let riskRange = "0% - 10%";
  let reasoning: string[] = [];
  let explanation = "";

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

  return {
    riskPercentage,
    riskRange,
    confidence: "High",
    reasoning,
    explanation
  };
}
