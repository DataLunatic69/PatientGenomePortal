import { Link } from 'react-router-dom';
import { Activity, Shield, Dna, ArrowRight, Microscope, BrainCircuit, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/ui/button';

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Navigation */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2 font-bold text-xl text-primary">
            <Dna className="h-6 w-6" />
            <span>GenomePortal</span>
          </div>
          <nav className="flex items-center gap-6">
            <a href="#features" className="text-sm font-medium hover:text-primary transition-colors">
              Features
            </a>
            <div className="flex items-center gap-4">
              <Link to="/login" className="text-sm font-medium hover:text-primary transition-colors">
                Sign in
              </Link>
              <Link to="/login">
                <Button size="sm">Get Started</Button>
              </Link>
            </div>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section 
          className="relative overflow-hidden py-24 lg:py-32 min-h-[600px] flex items-center bg-slate-900"
          style={{
            backgroundImage: 'url("/pexels-cottonbro-5473956.jpg")',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        >
          <div className="absolute inset-0 bg-slate-900/40 z-0" /> {/* Dark overlay for text readability */}
          <div className="container relative z-10 mx-auto max-w-7xl px-6 text-center text-white">
            <div className="mx-auto flex max-w-3xl flex-col items-center gap-6">
              <div className="inline-flex items-center rounded-full border border-white/20 bg-black/30 backdrop-blur-md px-3 py-1 text-sm font-medium">
                <span className="flex h-2 w-2 rounded-full bg-green-400 mr-2 shadow-[0_0_8px_rgba(74,222,128,0.8)]"></span>
                Next-generation genomic analysis
              </div>
              <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl drop-shadow-lg">
                Unlock the power of your <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-green-400">DNA</span>
              </h1>
              <p className="text-lg text-slate-200 sm:text-xl leading-relaxed drop-shadow-md max-w-2xl">
                Securely upload, sequence, and analyze your genomic data with our state-of-the-art AI pipeline. Get comprehensive insights into variants and potential health markers in minutes.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mt-6">
                <Link to="/login">
                  <Button size="lg" className="w-full sm:w-auto gap-2 bg-white text-slate-900 hover:bg-slate-100 font-bold border-0 shadow-xl">
                    Start Analysis <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link to="/login">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto text-white border-white/50 hover:bg-white/10 backdrop-blur-sm">
                    View Sample Report
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Image Section */}
        <section id="features" className="py-20 bg-white">
          <div className="container mx-auto max-w-7xl px-6">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-6">Revolutionizing Genetic Research</h2>
                <p className="text-lg text-muted-foreground mb-6">
                  Experience a seamless workflow from raw fasta/vcf sequences to actionable clinical knowledge. Our platform takes the heavy lifting out of bioinformatics.
                </p>
                <ul className="space-y-4">
                  {[
                    "Clinical-grade variant classification",
                    "Automated integration with ClinVar & MedGen",
                    "Peta-scale HIPAA compliant data storage",
                    "End-to-End sequence parsing with AlphaGenome"
                  ].map((feature, i) => (
                    <li key={i} className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-primary" />
                      <span className="font-medium text-slate-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-slate-100">
                <img 
                  src="/sangharsh-lohakare-Iy7QyzOs1bo-unsplash.jpg" 
                  alt="Laboratory and research visualization" 
                  className="w-full h-auto object-cover transform hover:scale-105 transition-transform duration-700" 
                />
              </div>
            </div>
          </div>
        </section>

        {/* Workflow Video Section */}
        <section className="py-24 bg-slate-50">
          <div className="container mx-auto max-w-7xl px-6">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <div className="relative rounded-2xl bg-black border border-slate-200 overflow-hidden shadow-2xl">
                <video 
                  src="/13549104_3840_2160_25fps.mp4" 
                  autoPlay 
                  loop 
                  muted 
                  playsInline
                  className="w-full h-full object-cover opacity-90"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-8">
                  <div className="text-white">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity className="h-5 w-5 text-green-400" />
                      <span className="font-mono text-sm tracking-widest">ANALYSIS_ACTIVE</span>
                    </div>
                    <p className="text-slate-300 text-sm">Real-time sequence parsing and genomic mapping via our distributed AI backend.</p>
                  </div>
                </div>
              </div>

              <div className="space-y-8 lg:pl-8">
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">How it works</h2>
                
                <div className="space-y-8">
                  <div className="flex gap-4">
                    <div className="flex-shrink-0 mt-1 flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm ring-4 ring-white">
                      1
                    </div>
                    <div>
                      <h4 className="text-xl font-semibold">Upload Your Files</h4>
                      <p className="text-muted-foreground mt-2">Securely upload your sequenced VCF or FASTA genome files directly to our encrypted storage buckets.</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-4">
                    <div className="flex-shrink-0 mt-1 flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm ring-4 ring-white">
                      2
                    </div>
                    <div>
                      <h4 className="text-xl font-semibold">Automated Pipeline</h4>
                      <p className="text-muted-foreground mt-2">Our architecture parses, normalizes, and runs comprehensive quality control on your genetic sequence.</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-4">
                    <div className="flex-shrink-0 mt-1 flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm ring-4 ring-white">
                      3
                    </div>
                    <div>
                      <h4 className="text-xl font-semibold">Review Insights</h4>
                      <p className="text-muted-foreground mt-2">Explore fully interactive dashboards highlighting pathogenic traits, risks, and personalized health reports.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Platform Capabilities */}
        <section className="py-24">
          <div className="container mx-auto max-w-7xl px-6">
            <div className="flex flex-col items-center justify-center text-center space-y-4 mb-16">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Platform Capabilities</h2>
              <p className="text-lg text-muted-foreground max-w-[800px]">
                Built for precision and security, our platform leverages advanced algorithms to make sense of complex genomic data.
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start text-left hover:border-primary/50 transition-colors">
                <div className="p-3 bg-primary/10 rounded-xl mb-6">
                  <Microscope className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Deep Variant Calling</h3>
                <p className="text-muted-foreground">
                  Identify single nucleotide polymorphisms (SNPs) and structural variations with clinical-grade accuracy.
                </p>
              </div>

              <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start text-left hover:border-primary/50 transition-colors">
                <div className="p-3 bg-amber-500/10 rounded-xl mb-6">
                  <BrainCircuit className="h-8 w-8 text-amber-500" />
                </div>
                <h3 className="text-xl font-semibold mb-3">AI-Powered Enrichment</h3>
                <p className="text-muted-foreground">
                  Cross-reference variants against global databases like ClinVar and gnomAD automatically using specialized AI models.
                </p>
              </div>

              <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start text-left hover:border-primary/50 transition-colors">
                <div className="p-3 bg-green-500/10 rounded-xl mb-6">
                  <Shield className="h-8 w-8 text-green-500" />
                </div>
                <h3 className="text-xl font-semibold mb-3">End-to-End Encryption</h3>
                <p className="text-muted-foreground">
                  Your genetic data is your most sensitive information. We ensure zero-knowledge storage and strict access controls.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t bg-slate-50 py-12">
        <div className="container mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2 font-bold text-lg text-slate-900">
            <Dna className="h-5 w-5 text-primary" />
            <span>GenomePortal</span>
          </div>
          <p className="text-sm text-slate-500">
            &copy; {new Date().getFullYear()} Patient Genome Portal. All rights reserved.
          </p>
          <div className="flex gap-4 text-sm text-slate-500 font-medium">
            <Link to="#" className="hover:text-primary">Privacy Policy</Link>
            <Link to="#" className="hover:text-primary">Terms of Service</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
