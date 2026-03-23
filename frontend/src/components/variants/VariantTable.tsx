import { Link } from 'react-router-dom';
import type { VariantResultRead } from '../../types/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Badge } from '../ui/badge';

interface VariantTableProps {
  variants: VariantResultRead[];
}

export default function VariantTable({ variants }: VariantTableProps) {
  if (variants.length === 0) {
    return <div className="p-8 text-center text-gray-500 border rounded-lg">No variants found matching criteria.</div>;
  }

  const getRiskBadge = (risk: string | null) => {
    switch (risk?.toLowerCase()) {
      case 'high':
        return <Badge variant="destructive">High Risk</Badge>;
      case 'moderate':
        return <Badge variant="default" className="bg-orange-500 hover:bg-orange-600">Moderate Risk</Badge>;
      case 'low':
        return <Badge variant="secondary" className="bg-green-100 text-green-800">Low Risk</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16"># Rank</TableHead>
            <TableHead>Gene</TableHead>
            <TableHead>Locus (Chr:Pos)</TableHead>
            <TableHead>Change</TableHead>
            <TableHead>ClinVar</TableHead>
            <TableHead>AI Risk</TableHead>
            <TableHead className="text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {variants.map((v) => (
            <TableRow key={v.id}>
              <TableCell className="font-semibold text-gray-500">{v.rank_position}</TableCell>
              <TableCell className="font-medium">{v.gene_name || 'N/A'}</TableCell>
              <TableCell>
                {v.chromosome}:{v.position}
              </TableCell>
              <TableCell>
                {v.reference_bases} → {v.alternate_bases}
              </TableCell>
              <TableCell className="capitalize">{v.clinvar_classification ? v.clinvar_classification.replace('_', ' ') : 'Not Provided'}</TableCell>
              <TableCell>{getRiskBadge(v.gemini_risk_level)}</TableCell>
              <TableCell className="text-right">
                <Link
                  to={`/variant/${v.id}`}
                  state={{ variant: v, jobId: v.analysis_job_id }}
                  className="text-blue-600 hover:underline text-sm font-medium"
                >
                  Details
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
