import type { Express } from "express";
import type { Server } from "http";
import { api } from "@shared/routes";
import { z } from "zod";

export async function registerRoutes(
  _httpServer: Server, // underscore = intentionally unused
  app: Express
): Promise<Server> {

  app.post(api.calculations.calculate.path, async (req, res) => {
    try {
      // 1️⃣ Validate input (Python-aligned schema)
      const input = api.calculations.calculate.input.parse(req.body);

      // 2️⃣ Call Python service (native fetch)
      const pythonResponse = await fetch(
        "http://127.0.0.1:8000/calculate-risk",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            inheritance_type: input.inheritance_type,
            parent1: input.parent1,
            parent2: input.parent2,
            child_sex: input.child_sex,
            observed_child_outcome: input.observed_child_outcome || null,
          }),
        }
      );

      if (!pythonResponse.ok) {
        throw new Error("Python service error");
      }

      const pythonResult = await pythonResponse.json();

      // 3️⃣ Return result to frontend
      res.status(200).json(pythonResult);

    } catch (err) {
      if (err instanceof z.ZodError) {
        res.status(400).json({
          message: err.errors[0].message,
          field: err.errors[0].path.join("."),
        });
      } else {
        console.error(err);
        res.status(500).json({ message: "Internal server error" });
      }
    }
  });

  // History endpoint (unchanged)
  app.get(api.calculations.history.path, async (_req, res) => {
    // In-memory placeholder history until persistence is added back
    res.json([]);
  });

  return _httpServer;
}
