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
  let riskRange = "0% - 0%";
  let reasoning: string[] = [];
  let explanation = "";
  let bayesian: CalculationResult['bayesianUpdate'] = null;

  // Priors matching server implementation
  const DEFAULT_PRIORS = {
    autosomal_recessive: { carrier_prior: 0.01, affected_prior: 0.0001 },
    autosomal_dominant: { affected_prior: 0.001 },
    x_linked: { mother_carrier_prior: 0.01, mother_affected_prior: 0.0001, father_affected_prior: 0.0005 }
  };

  function transmitProbAR(status: string, role: 'father' | 'mother') {
    if (status === 'affected') return 1.0;
    if (status === 'carrier') return 0.5;
    if (status === 'unaffected') return 0.0;
    // unknown: use priors
    if (role === 'mother') {
      const carrier = DEFAULT_PRIORS.x_linked.mother_carrier_prior;
      const affected = DEFAULT_PRIORS.autosomal_recessive.affected_prior;
      return carrier * 0.5 + affected * 1.0;
    }
    const carrier = DEFAULT_PRIORS.autosomal_recessive.carrier_prior;
    const affected = DEFAULT_PRIORS.autosomal_recessive.affected_prior;
    return carrier * 0.5 + affected * 1.0;
  }

  function transmitProbAD(status: string) {
    if (status === 'affected' || status === 'carrier') return 0.5;
    if (status === 'unaffected') return 0.0;
    // unknown
    return DEFAULT_PRIORS.autosomal_dominant.affected_prior * 0.5;
  }

  function motherTransmitXLR(status: string) {
    if (status === 'affected') return 1.0;
    if (status === 'carrier') return 0.5;
    if (status === 'unaffected') return 0.0;
    return DEFAULT_PRIORS.x_linked.mother_carrier_prior * 0.5 + DEFAULT_PRIORS.x_linked.mother_affected_prior * 1.0;
  }

  function fatherTransmitToDaughterXLR(status: string) {
    if (status === 'affected') return 1.0;
    if (status === 'unaffected') return 0.0;
    return DEFAULT_PRIORS.x_linked.father_affected_prior;
  }

  // Compute forward risk according to corrected Mendelian rules
  if (inheritancePattern === 'autosomal_recessive') {
    const p_f = transmitProbAR(fatherStatus, 'father');
    const p_m = transmitProbAR(motherStatus, 'mother');
    const risk = p_f * p_m;
    riskPercentage = Math.round(risk * 100);
    riskRange = `${(risk * 100).toFixed(2)}% - ${(risk * 100).toFixed(2)}%`;
    explanation = 'Autosomal recessive: child affected if both parents transmit mutant allele.';
    reasoning = [`Father: ${fatherStatus}`, `Mother: ${motherStatus}`];
  } else if (inheritancePattern === 'autosomal_dominant') {
    const p_f = transmitProbAD(fatherStatus);
    const p_m = transmitProbAD(motherStatus);
    const risk = 1.0 - (1.0 - p_f) * (1.0 - p_m);
    riskPercentage = Math.round(risk * 100);
    riskRange = `${(risk * 100).toFixed(2)}% - ${(risk * 100).toFixed(2)}%`;
    explanation = 'Autosomal dominant: child affected if at least one parent transmits dominant allele.';
    reasoning = [`Father: ${fatherStatus}`, `Mother: ${motherStatus}`];
  } else if (inheritancePattern === 'x_linked') {
    const p_m = motherTransmitXLR(motherStatus);
    if (data.childSex === 'male') {
      const risk = p_m;
      riskPercentage = Math.round(risk * 100);
      riskRange = `${(risk * 100).toFixed(2)}% - ${(risk * 100).toFixed(2)}%`;
      explanation = 'X-linked recessive: male child affected if mother transmits mutant X.';
      reasoning = [`Mother: ${motherStatus}`, `Father: ${fatherStatus}`];
    } else if (data.childSex === 'female') {
      const p_f_d = fatherTransmitToDaughterXLR(fatherStatus);
      const risk = p_m * p_f_d;
      riskPercentage = Math.round(risk * 100);
      riskRange = `${(risk * 100).toFixed(2)}% - ${(risk * 100).toFixed(2)}%`;
      explanation = 'X-linked recessive: female child affected only if both parents provide mutant X.';
      reasoning = [`Mother: ${motherStatus}`, `Father: ${fatherStatus}`];
    } else {
      const p_f_d = fatherTransmitToDaughterXLR(fatherStatus);
      const maleRisk = p_m;
      const femaleRisk = p_m * p_f_d;
      const minRisk = Math.min(maleRisk, femaleRisk);
      const maxRisk = Math.max(maleRisk, femaleRisk);
      riskPercentage = Math.round((maleRisk + femaleRisk) / 2 * 100);
      riskRange = `${(minRisk * 100).toFixed(2)}% - ${(maxRisk * 100).toFixed(2)}%`;
      explanation = 'X-linked recessive: risk differs by sex; males receive maternal X only, females require both parents.';
      reasoning = [`Mother: ${motherStatus}`, `Father: ${fatherStatus}`];
    }
  }

  // Bayesian reverse-update mirroring server behavior for AR and XLR (AD partial)
  if (observed && observed !== 'unknown') {
    if (inheritancePattern === 'autosomal_recessive') {
      if (observed === 'affected') {
        bayesian = {
          parent1_carrier_probability: motherStatus === 'unaffected' ? 0.0 : 1.0,
          parent2_carrier_probability: fatherStatus === 'unaffected' ? 0.0 : 1.0,
          updated_risk: { min: (motherStatus === 'unaffected' ? 0.0 : 1.0) * (fatherStatus === 'unaffected' ? 0.0 : 1.0) , max: (motherStatus === 'unaffected' ? 0.0 : 1.0) * (fatherStatus === 'unaffected' ? 0.0 : 1.0) }
        };
        riskPercentage = Math.round(bayesian.updated_risk!.min * 100);
        riskRange = `${(bayesian.updated_risk!.min * 100).toFixed(2)}% - ${(bayesian.updated_risk!.max * 100).toFixed(2)}%`;
        explanation = 'Observed affected child implies both parents are likely carriers.';
      } else if (observed === 'unaffected') {
        const priorMother = motherStatus === 'carrier' || motherStatus === 'affected' ? 1.0 : motherStatus === 'unknown' ? DEFAULT_PRIORS.autosomal_recessive.carrier_prior : 0.0;
        const priorFather = fatherStatus === 'carrier' || fatherStatus === 'affected' ? 1.0 : fatherStatus === 'unknown' ? DEFAULT_PRIORS.autosomal_recessive.carrier_prior : 0.0;
        const likelihood_carrier = 0.75;
        const likelihood_noncarrier = 1.0;
        const post1 = (0.0 < priorMother && priorMother < 1.0) ? (likelihood_carrier * priorMother) / (likelihood_carrier * priorMother + likelihood_noncarrier * (1 - priorMother)) : priorMother;
        const post2 = (0.0 < priorFather && priorFather < 1.0) ? (likelihood_carrier * priorFather) / (likelihood_carrier * priorFather + likelihood_noncarrier * (1 - priorFather)) : priorFather;
        bayesian = {
          parent1_carrier_probability: post1,
          parent2_carrier_probability: post2,
          updated_risk: { min: post1 * post2, max: post1 * post2 }
        };
        const updatedRiskPct = bayesian.updated_risk!.min * 100;
        riskPercentage = Math.round(updatedRiskPct);
        riskRange = `${updatedRiskPct.toFixed(2)}% - ${updatedRiskPct.toFixed(2)}%`;
        explanation = 'Observed unaffected child reduces the posterior probability that both parents are carriers.';
      }
    }

    if (inheritancePattern === 'x_linked') {
      if (observed === 'affected') {
        if (data.childSex === 'male') {
          bayesian = {
            parent1_carrier_probability: fatherStatus === 'unaffected' ? 0.0 : 1.0,
            parent2_carrier_probability: motherStatus === 'unaffected' ? 0.0 : 1.0,
            updated_risk: { min: motherTransmitXLR(motherStatus), max: motherTransmitXLR(motherStatus) }
          };
        } else if (data.childSex === 'female') {
          bayesian = {
            parent1_carrier_probability: fatherStatus === 'unaffected' ? 0.0 : 1.0,
            parent2_carrier_probability: motherStatus === 'unaffected' ? 0.0 : 1.0,
            updated_risk: { min: motherTransmitXLR(motherStatus) * fatherTransmitToDaughterXLR(fatherStatus), max: motherTransmitXLR(motherStatus) * fatherTransmitToDaughterXLR(fatherStatus) }
          };
        }
      } else if (observed === 'unaffected') {
        if (data.childSex === 'male') {
          const prior = motherStatus === 'unknown' ? DEFAULT_PRIORS.x_linked.mother_carrier_prior : (motherStatus === 'carrier' || motherStatus === 'affected' ? 1.0 : 0.0);
          const posterior = (0.5 * prior) / (0.5 * prior + 1.0 * (1 - prior));
          bayesian = { parent1_carrier_probability: fatherStatus === 'carrier' ? 1.0 : 0.0, parent2_carrier_probability: posterior, updated_risk: { min: posterior, max: posterior } };
        }
      }
    }
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
