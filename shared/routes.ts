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
        observed_child_outcome: z.enum(['affected','unaffected','unknown']).optional()
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
