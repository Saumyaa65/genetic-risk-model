import { pgTable, text, serial, integer, boolean, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const inheritancePatterns = ["autosomal_dominant", "autosomal_recessive", "x_linked"] as const;
export const memberStatuses = ["affected", "carrier", "unaffected", "unknown"] as const;
export const sexes = ["male", "female", "unknown"] as const;

export const calculations = pgTable("calculations", {
  id: serial("id").primaryKey(),
  inheritancePattern: text("inheritance_pattern").notNull(),
  motherStatus: text("mother_status").notNull(),
  fatherStatus: text("father_status").notNull(),
  childSex: text("child_sex").notNull(),
  riskResult: jsonb("risk_result").notNull(),
  createdAt: text("created_at").notNull(),
});

export const insertCalculationSchema = createInsertSchema(calculations).omit({ id: true, createdAt: true });

export type Calculation = typeof calculations.$inferSelect;
export type InsertCalculation = z.infer<typeof insertCalculationSchema>;
