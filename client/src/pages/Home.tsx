import { Link } from 'wouter';
import { motion } from 'framer-motion';
import { Dna, ArrowRight, ShieldCheck, Activity } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Canvas } from '@react-three/fiber';
import DnaModel from '@/components/genetics/DnaModel';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 overflow-hidden relative text-white">
      {/* 3D Background */}
      <div className="absolute inset-0 z-0 opacity-40">
        <Canvas camera={{ position: [0, 0, 10], fov: 45 }}>
          <DnaModel />
        </Canvas>
      </div>

      {/* Decorative Background Elements */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-teal-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 z-0" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-3xl translate-y-1/3 -translate-x-1/4 z-0" />

      <nav className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-teal-500/20">
            <Dna className="w-6 h-6" />
          </div>
          <span className="font-display font-bold text-xl tracking-tight text-white">XGene</span>
        </div>
        <div className="hidden md:flex gap-6">
          <a href="#" className="text-sm font-medium text-slate-300 hover:text-teal-400 transition-colors">Methodology</a>
          <a href="#" className="text-sm font-medium text-slate-300 hover:text-teal-400 transition-colors">About</a>
        </div>
      </nav>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-sm font-medium mb-6 backdrop-blur-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
              </span>
              Clinical Grade Modeling
            </div>
            
            <h1 className="text-5xl md:text-6xl font-display font-bold text-white leading-[1.1] mb-6">
              Predict Genetic <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-400">Inheritance Risks</span>
            </h1>
            
            <p className="text-lg text-slate-300 mb-8 max-w-lg leading-relaxed">
              Advanced probabilistic modeling for autosomal and X-linked traits. 
              Visualize inheritance patterns and calculate offspring risk factors with precision.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/calculate">
                <Button variant="premium" size="lg" className="w-full sm:w-auto bg-teal-500 hover:bg-teal-400 text-white border-0">
                  Start Analysis <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="w-full sm:w-auto border-slate-700 text-white hover:bg-slate-800">
                View Demo
              </Button>
            </div>

            <div className="mt-12 flex items-center gap-8 text-sm text-slate-400 font-medium">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-teal-400" />
                99.9% Accuracy
              </div>
            </div>
          </motion.div>

          <div className="relative hidden lg:block h-[600px]">
            {/* The background DNA canvas covers this area */}
          </div>
        </div>
      </main>
    </div>
  );
}
