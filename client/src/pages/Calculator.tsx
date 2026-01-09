import { useState } from 'react';
import { useLocation } from 'wouter';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, RefreshCw, Calculator as CalcIcon, Save } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { insertCalculationSchema, type InsertCalculation } from '@shared/schema';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { FamilyMemberNode } from '@/components/genetics/FamilyTree';
import { RiskDisplay } from '@/components/genetics/RiskDisplay';
import { useCalculateRisk } from '@/hooks/use-calculations';
// import { cn } from '@/components/ui/button';

// Default initial state
const INITIAL_DATA: InsertCalculation = {
  inheritancePattern: "autosomal_recessive",
  motherStatus: "carrier",
  fatherStatus: "carrier",
  childSex: "unknown", // Maps to 'unknown' sex but logic handles biological sex usually
  riskResult: {}, // Backend handles this, but we need it for type satisfaction if strict
};

export default function Calculator() {
  const [step, setStep] = useState<"input" | "result">("input");
  const [, setLocation] = useLocation();
  
  // React Hook Form for state management and validation
  const form = useForm<InsertCalculation>({
    resolver: zodResolver(insertCalculationSchema),
    defaultValues: INITIAL_DATA,
  });

  const { mutate: calculate, isPending, data: result } = useCalculateRisk();
  const { mutate: calculateWithObservation, isPending: isRecalculating, data: reversedResult } = useCalculateRisk();

  const onSubmit = (data: InsertCalculation) => {
    calculate(data, {
      onSuccess: () => setStep("result"),
    });
  };

  // Bayesian / "What If" local state
  const [observedOutcome, setObservedOutcome] = useState<string>("unknown");

  // Handler for Recalculate Parent Risk button
  const handleRecalculateParentRisk = () => {
    if (!result || observedOutcome === "unknown") return;

    const currentFormData = form.getValues();
    
    // Prepare data for reverse Bayesian calculation
    const dataWithObservation = {
      ...currentFormData,
      childSex: currentFormData.childSex as "male" | "female",
      observed_child_outcome: observedOutcome,
    };

    calculateWithObservation(dataWithObservation as any, {
      onSuccess: () => {
        // Result will be displayed automatically via reversedResult state
      },
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => step === 'result' ? setStep('input') : setLocation('/')}>
              <ArrowLeft className="w-5 h-5 text-slate-500" />
            </Button>
            <h1 className="font-display font-bold text-lg text-slate-900">
              New Calculation
            </h1>
          </div>
          <div className="text-sm text-slate-500 hidden sm:block">
            Session ID: <span className="font-mono text-xs bg-slate-100 px-2 py-1 rounded">#8X29-L</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {step === "input" ? (
            <motion.div
              key="input"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <div className="space-y-8">

                
                {/* Configuration Card */}
                <Card>
                  <CardHeader>
                    <CardTitle>Inheritance Configuration</CardTitle>
                    <CardDescription>Select the known genetic pattern for this condition.</CardDescription>
                  </CardHeader>
                  <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">Inheritance Pattern</label>
                      <select 
                        {...form.register("inheritancePattern")}
                        className="w-full rounded-xl border-slate-200 shadow-sm focus:border-teal-500 focus:ring-teal-500 py-3 px-4 bg-slate-50"
                      >
                        <option value="autosomal_recessive">Autosomal Recessive</option>
                        <option value="autosomal_dominant">Autosomal Dominant</option>
                        <option value="x_linked">X-Linked Recessive</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">Child's Sex (Projected)</label>
                      <select 
                        {...form.register("childSex")}
                        className="w-full rounded-xl border-slate-200 shadow-sm focus:border-teal-500 focus:ring-teal-500 py-3 px-4 bg-slate-50"
                      >
                        <option value="unknown">Any / Unknown</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                      </select>
                    </div>
                  </CardContent>
                </Card>

                {/* Family Tree Visualizer */}
                <Card className="overflow-hidden border-teal-100 shadow-teal-900/5">
                  <div className="bg-gradient-to-b from-teal-50/50 to-white p-8">
                    <div className="flex flex-col items-center relative min-h-[400px]">
                      
                      {/* Parents Layer */}
                      <div className="flex justify-center gap-24 md:gap-48 relative z-10 w-full mb-24">
                        <FamilyMemberNode 
                          role="Mother" 
                          status={form.watch("motherStatus") as any}
                          onChange={(val) => form.setValue("motherStatus", val)}
                        />
                        <FamilyMemberNode 
                          role="Father" 
                          status={form.watch("fatherStatus") as any}
                          onChange={(val) => form.setValue("fatherStatus", val)}
                        />
                      </div>

                      {/* Connecting Lines Graphic */}
                      <div className="absolute inset-0 top-12 pointer-events-none">
                         {/* We position this absolutely to overlay nicely */}
                         <div className="w-[calc(100%-100px)] md:w-[400px] border-t-2 border-slate-300 mx-auto absolute left-0 right-0 top-12"></div>
                         <div className="h-32 border-l-2 border-slate-300 absolute left-1/2 -translate-x-1/2 top-12"></div>
                      </div>

                      {/* Child Layer */}
                      <div className="relative z-10">
                         <FamilyMemberNode 
                           role="Child" 
                           status="unknown" 
                           readOnly 
                         />
                         <div className="absolute -right-32 top-8 hidden md:block w-48 text-xs text-slate-400 italic">
                           * Projecting risk for this generation
                         </div>
                      </div>

                    </div>
                  </div>
                  <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-end">
                    <Button
                      type="button"
                      size="lg"
                      onClick={form.handleSubmit(onSubmit)}
                      className="w-full md:w-auto shadow-teal-500/25 shadow-lg"
                      disabled={isPending}
                    >
                      <CalcIcon className="mr-2 w-4 h-4" />
                      {isPending ? 'Calculating…' : 'Calculate Risk'}
                    </Button>
                  </div>
                </Card>

              </div>
            </motion.div>
          ) : (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              className="space-y-8"
            >
               {/* Summary Card */}
               <Card className="border-teal-200 shadow-lg shadow-teal-900/5 overflow-hidden">
                 <div className="bg-teal-600 p-6 text-white flex justify-between items-center">
                   <div>
                     <h2 className="text-2xl font-display font-bold">Analysis Results</h2>
                     <p className="text-teal-100 opacity-90">Based on {form.getValues("inheritancePattern").replace("_", " ")} inheritance</p>
                   </div>
                   <Button variant="secondary" size="sm" onClick={() => setStep("input")}>Edit Parameters</Button>
                 </div>
                 
                 <CardContent className="pt-8">
                   {result && (
                     <RiskDisplay 
                       percentage={result.riskPercentage}
                       range={result.riskRange}
                       confidence={result.confidence}
                       explanation={result.explanation}
                     />
                   )}
                 </CardContent>
               </Card>

               {/* "What If" Section */}
               <Card>
                 <CardHeader>
                   <CardTitle>Bayesian Update (What-If Analysis)</CardTitle>
                   <CardDescription>Update parental probabilities based on observed clinical outcomes in the child.</CardDescription>
                 </CardHeader>
                 <CardContent>
                   <div className="flex flex-col md:flex-row items-center gap-6 p-6 bg-slate-50 rounded-xl border border-slate-100">
                     <div className="flex-1 w-full">
                       <label className="block text-sm font-medium text-slate-700 mb-2">Observed Child Outcome</label>
                       <select 
                         value={observedOutcome}
                         onChange={(e) => setObservedOutcome(e.target.value)}
                         className="w-full rounded-xl border-slate-200 shadow-sm py-3 px-4"
                       >
                         <option value="unknown">No Observation (Standard)</option>
                         <option value="affected">Child is Affected</option>
                         <option value="unaffected">Child is Unaffected</option>
                       </select>
                     </div>
                     <div className="pt-6">
                       <Button 
                         variant="outline" 
                         className="w-full md:w-auto"
                         onClick={handleRecalculateParentRisk}
                         disabled={observedOutcome === "unknown" || isRecalculating}
                       >
                         <RefreshCw className={`w-4 h-4 mr-2 ${isRecalculating ? 'animate-spin' : ''}`} /> 
                         {isRecalculating ? 'Recalculating…' : 'Recalculate Parent Risk'}
                       </Button>
                     </div>
                   </div>
                   <p className="text-sm text-slate-500 mt-4 italic">
                     * This module mocks a reverse Bayesian calculation to refine the probability of parents being carriers if their status was initially unknown.
                   </p>
                 </CardContent>
               </Card>

               {/* Bayesian Update Results */}
               {reversedResult && observedOutcome !== "unknown" && (
                 <motion.div
                   initial={{ opacity: 0, y: 10 }}
                   animate={{ opacity: 1, y: 0 }}
                   className="space-y-4"
                 >
                   <Card className="border-amber-200 bg-amber-50/50 shadow-lg shadow-amber-900/5 overflow-hidden">
                     <div className="bg-amber-600 p-6 text-white flex items-center justify-between">
                       <div>
                         <h3 className="text-xl font-display font-bold">Updated Risk Analysis</h3>
                         <p className="text-amber-100 opacity-90">Based on observed child outcome: {observedOutcome}</p>
                       </div>
                       <RefreshCw className="w-6 h-6 opacity-75" />
                     </div>
                     
                     <CardContent className="pt-8">
                       {reversedResult && (
                         <RiskDisplay 
                           percentage={reversedResult.riskPercentage}
                           range={reversedResult.riskRange}
                           confidence={reversedResult.confidence}
                           explanation={reversedResult.explanation}
                         />
                       )}
                     </CardContent>
                   </Card>
                 </motion.div>
               )}

               <div className="flex justify-center gap-4">
                 <Button variant="outline" size="lg" onClick={() => setStep('input')}>
                    <ArrowLeft className="mr-2 w-4 h-4" /> Start Over
                 </Button>
                 <Button variant="default" size="lg">
                    <Save className="mr-2 w-4 h-4" /> Save Report
                 </Button>
               </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
