import { type Calculation, type InsertCalculation } from "@shared/schema";
import { db } from "./db";
import { calculations } from "@shared/schema";
import { eq } from "drizzle-orm";

export interface IStorage {
  getCalculations(): Promise<Calculation[]>;
  createCalculation(calculation: InsertCalculation): Promise<Calculation>;
}

export class DatabaseStorage implements IStorage {
  async getCalculations(): Promise<Calculation[]> {
    return await db.select().from(calculations);
  }

  async createCalculation(insertCalculation: InsertCalculation): Promise<Calculation> {
    const [calculation] = await db
      .insert(calculations)
      .values({ ...insertCalculation, createdAt: new Date().toISOString() })
      .returning();
    return calculation;
  }
}

export const storage = new DatabaseStorage();
