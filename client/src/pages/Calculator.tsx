import { useState } from 'react';
import { useLocation } from 'wouter';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, RefreshCw, Calculator as CalcIcon, Save } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { calculateLocalRisk } from '@/lib/genetics';
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

// Example conditions mapping (educational only)
type ExampleConditionKey = "cystic_fibrosis" | "sickle_cell_anemia" | "huntingtons_disease" | "hemophilia_a";

const EXAMPLE_CONDITIONS: Record<ExampleConditionKey, {
  inheritancePattern: InsertCalculation["inheritancePattern"];
  motherStatus: InsertCalculation["motherStatus"];
  fatherStatus: InsertCalculation["fatherStatus"];
}> = {
  "cystic_fibrosis": { 
    inheritancePattern: "autosomal_recessive", 
    motherStatus: "carrier", 
    fatherStatus: "carrier" 
  },
  "sickle_cell_anemia": { 
    inheritancePattern: "autosomal_recessive", 
    motherStatus: "carrier", 
    fatherStatus: "carrier" 
  },
  "huntingtons_disease": { 
    inheritancePattern: "autosomal_dominant", 
    motherStatus: "affected", 
    fatherStatus: "unaffected" 
  },
  "hemophilia_a": { 
    inheritancePattern: "x_linked", 
    motherStatus: "carrier", 
    fatherStatus: "unaffected" 
  },
};

export default function Calculator() {
  const [step, setStep] = useState<"input" | "result">("input");
  const [, setLocation] = useLocation();
  const [selectedExample, setSelectedExample] = useState<string>("");
  
  // React Hook Form for state management and validation
  const form = useForm<InsertCalculation>({
    resolver: zodResolver(insertCalculationSchema),
    defaultValues: INITIAL_DATA,
  });

  const { mutate: calculate, isPending, data: result } = useCalculateRisk();
  const { mutate: calculateWithObservation, isPending: isRecalculating, data: reversedResult } = useCalculateRisk();

  // Handle example condition selection
  const handleExampleConditionChange = (value: string) => {
    setSelectedExample(value);
    if (value && value in EXAMPLE_CONDITIONS) {
      const example = EXAMPLE_CONDITIONS[value as ExampleConditionKey];
      form.setValue("inheritancePattern", example.inheritancePattern);
      form.setValue("motherStatus", example.motherStatus);
      form.setValue("fatherStatus", example.fatherStatus);
    }
  };

  const onSubmit = (data: InsertCalculation) => {
    calculate(data, {
      onSuccess: () => setStep("result"),
    });
  };

  // Bayesian / "What If" local state
  const [observedOutcome, setObservedOutcome] = useState<string>("unknown");
  const [localBayesian, setLocalBayesian] = useState<any | null>(null);

  // Handler for Recalculate Parent Risk button
  const handleRecalculateParentRisk = () => {
    if (observedOutcome === "unknown") return;

    const currentFormData = form.getValues();
    
    // Prepare data for reverse Bayesian calculation
    const dataWithObservation = {
      ...currentFormData,
      childSex: (currentFormData.childSex as any) === 'unknown' ? 'male' : (currentFormData.childSex as any),
      observed_child_outcome: observedOutcome,
    };

    // compute local Bayesian fallback immediately so UI can show parent probabilities
    try {
      const local = calculateLocalRisk(dataWithObservation as any);
      setLocalBayesian(local.bayesianUpdate ?? null);
    } catch (e) {
      setLocalBayesian(null);
    }

    // ensure we're showing the result view
    setStep('result');

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
                  <CardContent className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        Example Condition <span className="text-xs text-slate-500 font-normal">(optional, educational only)</span>
                      </label>
                      <select 
                        value={selectedExample}
                        onChange={(e) => handleExampleConditionChange(e.target.value)}
                        className="w-full rounded-xl border-slate-200 shadow-sm focus:border-teal-500 focus:ring-teal-500 py-3 px-4 bg-slate-50"
                      >
                        <option value="">None - Manual Entry</option>
                        <option value="cystic_fibrosis">Cystic Fibrosis</option>
                        <option value="sickle_cell_anemia">Sickle Cell Anemia</option>
                        <option value="huntingtons_disease">Huntington's Disease</option>
                        <option value="hemophilia_a">Hemophilia A</option>
                      </select>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                         <div className="space-y-4">
                           {/* Textual Bayesian summary similar to test output */}
                           <div className="p-4 bg-white rounded border border-slate-100">
                             <div className="border-b pb-2 mb-3 text-slate-700 font-semibold text-base">Bayesian Update Details</div>

                            <div className="space-y-2 text-sm text-slate-700">
                              <div className="flex justify-between">
                                <span className="font-medium">Original Risk:</span>
                                <span className="text-slate-900">{result?.riskRange ?? reversedResult?.riskRange ?? 'N/A'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="font-medium">Confidence:</span>
                                <span className="text-slate-900 capitalize">{result?.confidence ?? reversedResult?.confidence ?? 'N/A'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="font-medium">Bayesian Update Applied:</span>
                                <span className="text-slate-900">{reversedResult.bayesianUpdate ? 'Yes' : 'No'}</span>
                              </div>
                              {reversedResult.bayesianUpdate && (
                                <div className="space-y-3 pt-2">
                                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                                    <div className="text-xs font-semibold text-slate-600 mb-2">Updated Parent Probabilities</div>
                                    <div className="space-y-2">
                                      <div>
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-sm font-medium text-slate-700">Mother:</span>
                                          <span className="text-sm font-semibold text-slate-900">
                                            {(() => {
                                              const origStatus = reversedResult.bayesianUpdate.parent1_original_status || 'unknown';
                                              const prob = (reversedResult.bayesianUpdate.parent1_carrier_probability ?? 0) * 100;
                                              if (origStatus === 'affected') {
                                                return `Affected (100%)`;
                                              } else if (origStatus === 'unaffected') {
                                                return `Unaffected (0%)`;
                                              } else {
                                                return `${prob.toFixed(1)}% probability of being affected`;
                                              }
                                            })()}
                                          </span>
                                        </div>
                                        {reversedResult.bayesianUpdate.parent1_original_status === 'unknown' && (
                                          <div className="text-xs text-slate-500 italic">
                                            Original: Unknown (50%) → Updated: {((reversedResult.bayesianUpdate.parent1_carrier_probability ?? 0) * 100).toFixed(1)}%
                                          </div>
                                        )}
                                      </div>
                                      <div>
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-sm font-medium text-slate-700">Father:</span>
                                          <span className="text-sm font-semibold text-slate-900">
                                            {(() => {
                                              const origStatus = reversedResult.bayesianUpdate.parent2_original_status || 'unknown';
                                              const prob = (reversedResult.bayesianUpdate.parent2_carrier_probability ?? 0) * 100;
                                              if (origStatus === 'affected') {
                                                return `Affected (100%)`;
                                              } else if (origStatus === 'unaffected') {
                                                return `Unaffected (0%)`;
                                              } else {
                                                return `${prob.toFixed(1)}% probability of being affected`;
                                              }
                                            })()}
                                          </span>
                                        </div>
                                        {reversedResult.bayesianUpdate.parent2_original_status === 'unknown' && (
                                          <div className="text-xs text-slate-500 italic">
                                            Original: Unknown (50%) → Updated: {((reversedResult.bayesianUpdate.parent2_carrier_probability ?? 0) * 100).toFixed(1)}%
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )}
                              <div className="flex justify-between pt-2 border-t border-slate-200">
                                <span className="font-semibold">Updated Risk:</span>
                                <span className="text-slate-900 font-semibold">{(() => {
                                  const br = reversedResult.bayesianUpdate?.updated_risk;
                                  if (br && typeof br.min === 'number' && typeof br.max === 'number') {
                                    return `${(br.min*100).toFixed(1)}% - ${(br.max*100).toFixed(1)}%`;
                                  }
                                  return reversedResult.riskRange ?? 'N/A';
                                })()}</span>
                              </div>
                            </div>
                           </div>

                           {/* Clinical explanation card */}
                           <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
                             <h4 className="text-sm font-medium text-slate-700 mb-2">Clinical Explanation</h4>
                             <p className="text-sm text-slate-600">{reversedResult.explanation}</p>
                           </div>
                         </div>
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
