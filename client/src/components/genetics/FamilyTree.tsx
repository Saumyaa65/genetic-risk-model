import { motion } from 'framer-motion';
import { User, CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

// Types for props
type Status = "affected" | "carrier" | "unaffected" | "unknown";

interface FamilyMemberNodeProps {
  role: "Mother" | "Father" | "Child" | "Maternal Grandparent" | "Paternal Grandparent" | "Grandparent" | "Maternal Grandmother" | "Maternal Grandfather" | "Paternal Grandmother" | "Paternal Grandfather";
  status: Status;
  sex?: "male" | "female";
  onChange?: (status: Status) => void;
  readOnly?: boolean;
}

const statusColors = {
  affected: "bg-red-100 border-red-200 text-red-700",
  carrier: "bg-amber-100 border-amber-200 text-amber-700",
  unaffected: "bg-emerald-100 border-emerald-200 text-emerald-700",
  unknown: "bg-slate-100 border-slate-200 text-slate-600",
};

const statusIcons = {
  affected: AlertTriangle,
  carrier: AlertTriangle, // Or a half-filled icon if available, reusing alert for now
  unaffected: CheckCircle2,
  unknown: HelpCircle,
};

export function FamilyMemberNode({ role, status, sex, onChange, readOnly }: FamilyMemberNodeProps) {
  const Icon = statusIcons[status] || HelpCircle;

  return (
    <div className="flex flex-col items-center gap-3 relative z-10">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className={cn(
          "w-24 h-24 rounded-full flex items-center justify-center border-4 shadow-sm transition-colors duration-300 bg-white",
          statusColors[status]
        )}
      >
        <User className="w-10 h-10 opacity-80" />
      </motion.div>
      
      <div className="text-center">
        <p className="font-display font-bold text-lg text-slate-800">{role}</p>
        {!readOnly && (
           <select
             className="mt-1 block w-32 text-sm rounded-md border-gray-300 py-1.5 pl-3 pr-8 text-base focus:border-teal-500 focus:outline-none focus:ring-teal-500 sm:text-sm bg-white shadow-sm border"
             value={status}
             onChange={(e) => onChange?.(e.target.value as Status)}
           >
             <option value="unknown">Unknown</option>
             <option value="unaffected">Unaffected</option>
             <option value="carrier">Carrier</option>
             <option value="affected">Affected</option>
           </select>
        )}
        {readOnly && (
          <span className={cn("text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full mt-1 inline-block", statusColors[status])}>
            {status}
          </span>
        )}
      </div>
    </div>
  );
}

interface ConnectorLinesProps {
    vertical?: boolean;
}

export function ConnectorLines() {
  return (
    <div className="absolute top-12 left-0 right-0 h-12 -z-0 pointer-events-none flex justify-center">
      {/* Horizontal Line connecting parents */}
      <div className="w-[60%] h-full border-t-2 border-slate-300 relative top-12"></div>
      
      {/* Vertical Line to child */}
      <div className="absolute top-12 h-24 border-l-2 border-slate-300"></div>
    </div>
  );
}
