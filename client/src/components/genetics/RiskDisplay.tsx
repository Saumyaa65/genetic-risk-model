import { motion } from 'framer-motion';
import { Activity, Info } from 'lucide-react';

interface RiskDisplayProps {
  percentage: number;
  range: string;
  confidence: string;
  explanation: string;
}

export function RiskDisplay({ percentage, range, confidence, explanation }: RiskDisplayProps) {
  // Determine color based on risk
  const isHigh = percentage > 25;
  const colorClass = isHigh ? "text-red-600" : percentage > 0 ? "text-amber-600" : "text-emerald-600";
  const bgClass = isHigh ? "bg-red-50" : percentage > 0 ? "bg-amber-50" : "bg-emerald-50";
  const borderClass = isHigh ? "border-red-100" : percentage > 0 ? "border-amber-100" : "border-emerald-100";

  return (
    <div className="space-y-8">
      {/* Big Donut/Circle Chart */}
      <div className="flex justify-center py-8">
        <div className="relative w-64 h-64">
           {/* SVG Circle for Progress */}
           <svg className="w-full h-full transform -rotate-90">
             <circle
               cx="128"
               cy="128"
               r="120"
               stroke="currentColor"
               strokeWidth="12"
               fill="transparent"
               className="text-slate-100"
             />
             <motion.circle
               initial={{ strokeDasharray: "0 1000" }}
               animate={{ strokeDasharray: `${(percentage / 100) * 754} 1000` }}
               transition={{ duration: 1.5, ease: "easeOut" }}
               cx="128"
               cy="128"
               r="120"
               stroke="currentColor"
               strokeWidth="12"
               fill="transparent"
               strokeLinecap="round"
               className={colorClass}
               style={{ strokeDasharray: "754", strokeDashoffset: "754" }} 
             />
           </svg>
           <div className="absolute inset-0 flex flex-col items-center justify-center">
             <span className={`text-5xl font-bold ${colorClass}`}>{percentage}%</span>
             <span className="text-slate-500 font-medium mt-2">Probability</span>
           </div>
        </div>
      </div>

      <div className={`grid grid-cols-1 md:grid-cols-2 gap-4`}>
         <div className={`p-4 rounded-xl border ${bgClass} ${borderClass}`}>
            <div className="flex items-center gap-2 mb-2">
                <Activity className={`w-5 h-5 ${colorClass}`} />
                <h4 className="font-semibold text-slate-900">Risk Range</h4>
            </div>
            <p className="text-2xl font-display font-bold text-slate-800">{range}</p>
         </div>

         <div className="p-4 rounded-xl border border-slate-100 bg-white">
            <div className="flex items-center gap-2 mb-2">
                <Info className="w-5 h-5 text-blue-500" />
                <h4 className="font-semibold text-slate-900">Confidence</h4>
            </div>
            <p className="text-2xl font-display font-bold text-slate-800">{confidence}</p>
         </div>
      </div>

      <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
        <h4 className="font-semibold text-slate-900 mb-2">Clinical Explanation</h4>
        <p className="text-slate-600 leading-relaxed">{explanation}</p>
      </div>
    </div>
  );
}
