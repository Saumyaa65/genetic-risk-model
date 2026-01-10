import { z } from 'zod';
import { insertCalculationSchema, calculations, inheritancePatterns } from './schema';

export const errorSchemas = {
  validation: z.object({ message: z.string(), field: z.string().optional() }),
  notFound: z.object({ message: z.string() }),
  internal: z.object({ message: z.string() }),
};

export const api = {
  calculations: {
    calculate: {
      method: 'POST' as const,
      path: '/api/calculate',
      // Request schema aligned with Python service
      input: z.object({
        inheritance_type: z.enum(inheritancePatterns),
        parent1: z.object({ status: z.enum(['affected','carrier','unaffected','unknown'] as const) }),
        parent2: z.object({ status: z.enum(['affected','carrier','unaffected','unknown'] as const) }),
        child_sex: z.enum(['male','female']),
        observed_child_outcome: z.enum(['affected','unaffected','unknown']).optional(),
        generations: z.number().int().min(2).max(3).optional().default(2), // 2-gen or 3-gen, default 2
        // Optional grandparent fields for 3-gen mode (for future extended calculations)
        maternal_grandmother: z.object({ status: z.enum(['affected','carrier','unaffected','unknown'] as const) }).optional(),
        maternal_grandfather: z.object({ status: z.enum(['affected','carrier','unaffected','unknown'] as const) }).optional(),
        paternal_grandmother: z.object({ status: z.enum(['affected','carrier','unaffected','unknown'] as const) }).optional(),
        paternal_grandfather: z.object({ status: z.enum(['affected','carrier','unaffected','unknown'] as const) }).optional(),
      }),
      responses: {
        // Python response shape
        200: z.object({
          risk: z.object({
            min: z.number(),
            max: z.number(),
            confidence: z.string(),
            factors: z.array(z.string()).optional(),
          }),
          explanation: z.string(),
        }),
      },
    },
    history: {
      method: 'GET' as const,
      path: '/api/calculations',
      responses: {
        200: z.array(z.custom<typeof calculations.$inferSelect>()),
      },
    }
  }
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}
