import { Activity } from "lucide-react";
import { Link } from "react-router-dom";

export default function Header() {
  return (
    <header className="border-b bg-white">
      <div className="flex h-16 items-center px-4 container mx-auto">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl text-primary">
          <Activity className="h-6 w-6" />
          PatientGenomePortal
        </Link>
      </div>
    </header>
  )
}
