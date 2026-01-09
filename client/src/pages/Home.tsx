import { Link } from 'wouter';
import { motion } from 'framer-motion';
import { Dna, ArrowRight, ShieldCheck, Activity } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 overflow-hidden relative">
      {/* Decorative Background Elements */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-teal-100/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 z-0" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-blue-100/30 rounded-full blur-3xl translate-y-1/3 -translate-x-1/4 z-0" />

      <nav className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-teal-500/20">
            <Dna className="w-6 h-6" />
          </div>
          <span className="font-display font-bold text-xl tracking-tight text-slate-900">GeneRisks</span>
        </div>
        <div className="hidden md:flex gap-6">
          <a href="#" className="text-sm font-medium text-slate-600 hover:text-teal-600 transition-colors">Methodology</a>
          <a href="#" className="text-sm font-medium text-slate-600 hover:text-teal-600 transition-colors">About</a>
        </div>
      </nav>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-100 text-teal-700 text-sm font-medium mb-6">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
              </span>
              Clinical Grade Modeling
            </div>
            
            <h1 className="text-5xl md:text-6xl font-display font-bold text-slate-900 leading-[1.1] mb-6">
              Predict Genetic <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-600 to-emerald-600">Inheritance Risks</span>
            </h1>
            
            <p className="text-lg text-slate-600 mb-8 max-w-lg leading-relaxed">
              Advanced probabilistic modeling for autosomal and X-linked traits. 
              Visualize inheritance patterns and calculate offspring risk factors with precision.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/calculate">
                <Button variant="premium" size="lg" className="w-full sm:w-auto">
                  Start Analysis <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                View Demo
              </Button>
            </div>

            <div className="mt-12 flex items-center gap-8 text-sm text-slate-500 font-medium">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-teal-600" />
                HIPAA Compliant
              </div>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-teal-600" />
                99.9% Accuracy
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative hidden lg:block"
          >
            <div className="relative rounded-2xl overflow-hidden shadow-2xl shadow-teal-900/10 border border-slate-200 bg-white p-2">
              <img 
                src="https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800&q=80" 
                alt="Medical DNA visualization" 
                className="rounded-xl w-full h-auto object-cover"
              />
              
              {/* Floating UI Card Decoration */}
              <div className="absolute -bottom-6 -left-6 bg-white p-4 rounded-xl shadow-xl border border-slate-100 max-w-xs animate-bounce-slow">
                 <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600">
                        <Activity className="w-4 h-4" />
                    </div>
                    <div>
                        <p className="text-xs text-slate-500">Risk Assessment</p>
                        <p className="font-bold text-slate-800">Autosomal Recessive</p>
                    </div>
                 </div>
                 <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full w-[25%] bg-red-500 rounded-full" />
                 </div>
                 <p className="text-xs text-slate-400 mt-2 text-right">25% Probability</p>
              </div>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
