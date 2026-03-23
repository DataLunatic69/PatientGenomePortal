import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { Dna, LogOut } from 'lucide-react';
import { Button } from '../ui/button';

interface PageShellProps {
  children: ReactNode;
  onLogout?: () => void;
}

export default function PageShell({ children, onLogout }: PageShellProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b sticky top-0 z-10 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-primary hover:opacity-80 transition-opacity">
          <Dna className="w-8 h-8" />
          <span className="text-xl font-bold tracking-tight text-gray-900">PatientGenomePortal</span>
        </Link>
        {onLogout && (
          <Button variant="ghost" size="sm" onClick={onLogout} className="flex items-center gap-2">
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </Button>
        )}
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {children}
      </main>
      <footer className="bg-white border-t px-6 py-4 text-center text-sm text-gray-500">
        &copy; {new Date().getFullYear()} PatientGenomePortal by AI. All rights reserved.
      </footer>
    </div>
  );
}
