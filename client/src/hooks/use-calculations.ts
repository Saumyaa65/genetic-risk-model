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
    mutationFn: async (data: InsertCalculation & { observed_child_outcome?: string }) => {
      try {
        const res = await fetch(api.calculations.calculate.path, {
          method: api.calculations.calculate.method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            inheritance_type: data.inheritancePattern,
            parent1: { status: data.motherStatus },
            parent2: { status: data.fatherStatus },
            child_sex: data.childSex === "unknown" ? "male" : data.childSex,
            observed_child_outcome: data.observed_child_outcome || undefined,
          }),
        });

        if (!res.ok) {
          throw new Error("Backend calculation failed");
        }

        const pythonResult = await res.json();

        const min = pythonResult.risk.min * 100;
        const max = pythonResult.risk.max * 100;

        return {
          riskPercentage: Math.round((min + max) / 2),
          riskRange: `${Math.round(min)}% - ${Math.round(max)}%`,
          confidence: pythonResult.risk.confidence,
          explanation: pythonResult.explanation,
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
