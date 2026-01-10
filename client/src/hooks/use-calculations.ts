import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl } from "@shared/routes";
import { type InsertCalculation } from "@shared/schema";
import { calculateLocalRisk } from "@/lib/genetics"; // Import local engine

// ============================================
// CALCULATIONS HOOKS
// ============================================

export function useCalculationsHistory() {
  return useQuery({
    queryKey: [api.calculations.history.path],
    queryFn: async () => {
      const res = await fetch(api.calculations.history.path, { credentials: "include" });
      if (!res.ok) throw new Error('Failed to fetch history');
      return api.calculations.history.responses[200].parse(await res.json());
    },
  });
}

// 
export function useCalculateRisk() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: InsertCalculation & { 
      observed_child_outcome?: string; 
      generations?: number; 
      maternalGrandmotherStatus?: string;
      maternalGrandfatherStatus?: string;
      paternalGrandmotherStatus?: string;
      paternalGrandfatherStatus?: string;
    }) => {
      try {
        const generations = data.generations || 2;
        
        // For 3-gen: parent1 = maternal grandmother (primary grandparent for maternal line)
        //            parent2 = mother
        // For 2-gen: parent1 = father, parent2 = mother (unchanged)
        const parent1Status = generations === 3 
          ? (data.maternalGrandmotherStatus || "unknown")
          : (data.fatherStatus);
        const parent2Status = generations === 3
          ? (data.motherStatus)
          : (data.motherStatus);
        
        const res = await fetch(api.calculations.calculate.path, {
          method: api.calculations.calculate.method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            inheritance_type: data.inheritancePattern,
            parent1: { status: parent1Status },
            parent2: { status: parent2Status },
            child_sex: data.childSex === "unknown" ? "male" : data.childSex,
            observed_child_outcome: data.observed_child_outcome || undefined,
            generations: generations,
            // Include all grandparents for future use or extended calculations
            maternal_grandmother: generations === 3 ? { status: data.maternalGrandmotherStatus || "unknown" } : undefined,
            maternal_grandfather: generations === 3 ? { status: data.maternalGrandfatherStatus || "unknown" } : undefined,
            paternal_grandmother: generations === 3 ? { status: data.paternalGrandmotherStatus || "unknown" } : undefined,
            paternal_grandfather: generations === 3 ? { status: data.paternalGrandfatherStatus || "unknown" } : undefined,
          }),
        });

        if (!res.ok) {
          throw new Error("Backend calculation failed");
        }

        const pythonResult = await res.json();

        const min = pythonResult.risk.min * 100;
        const max = pythonResult.risk.max * 100;

        // Include optional Bayesian update metadata when present
        const bayesian = pythonResult.risk.bayesian_update || null;

        return {
          riskPercentage: Math.round((min + max) / 2),
          riskRange: `${Math.round(min)}% - ${Math.round(max)}%`,
          confidence: pythonResult.risk.confidence,
          explanation: pythonResult.explanation,
          bayesianUpdate: bayesian,
        };
      } catch (e) {
        // Fallback to local calculation if Python service is unavailable
        const local = calculateLocalRisk(data);
        return local;
      }
    },

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [api.calculations.history.path],
      });
    },
  });
}
