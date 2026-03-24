import UploadCard from '../components/upload/UploadCard';
import { Dna } from 'lucide-react';

export default function UploadPage() {
  return (
    <div className="relative flex flex-col items-center justify-center min-h-[85vh] py-12 px-6">
      {/* Decorative background elements */}
      <div className="absolute top-1/4 left-0 w-72 h-72 bg-primary/5 rounded-full blur-3xl -z-10 pointer-events-none" />
      <div className="absolute bottom-1/4 right-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl -z-10 pointer-events-none" />
      
      <div className="text-center mb-10 max-w-2xl relative z-10">
        <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-2xl mb-6 shadow-sm ring-1 ring-primary/20">
          <Dna className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold text-foreground tracking-tight mb-4 drop-shadow-sm">
          Sequence Upload
        </h1>
        <p className="text-lg text-muted-foreground leading-relaxed">
          Upload next-generation sequencing data for fast, automated clinical interpretation powered by our genomic AI engine.
        </p>
      </div>
      
      <div className="relative z-10 w-full max-w-xl">
        <UploadCard />
      </div>
    </div>
  );
}
