import type { VariantResultRead } from '../../types/api';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Printer } from 'lucide-react';
import { Button } from '../ui/button';
import ReactMarkdown from 'react-markdown';

interface PatientReportProps {
  variants: VariantResultRead[];
  reportText?: string | null;
}

export default function PatientReport({ variants, reportText }: PatientReportProps) {
  const highRisk = variants.filter(v => v.gemini_risk_level?.toLowerCase() === 'high');

  return (
    <Card className="mt-8 border-t-4 border-t-primary">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Clinical Summary Report</CardTitle>
        <Button variant="outline" size="sm" onClick={() => window.print()}>
          <Printer className="w-4 h-4 mr-2" /> Print PDF
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {reportText ? (
          <div className="prose max-w-none text-gray-800">
            <ReactMarkdown>{reportText}</ReactMarkdown>
          </div>
        ) : (
          <div>
            <h3 className="font-semibold text-lg border-b pb-2 mb-3">Key Findings</h3>
            {highRisk.length > 0 ? (
              <ul className="list-disc pl-5 space-y-2">
                {highRisk.map(v => (
                  <li key={v.id}>
                    <strong>{v.gene_name || 'Unknown'} ({v.chromosome}:{v.position})</strong>:{' '}
                    {v.gemini_summary || 'Classified as high risk based on interpretation.'}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-green-600">No high-risk actionable variants identified in this sample.</p>
            )}
          </div>
        )}
        
        <div className="mt-6 p-4 bg-muted rounded-md text-sm text-gray-700">
          <strong>Disclaimer:</strong> This interpretation is AI-generated and for research/informational purposes only. 
          It does not substitute for professional medical advice, diagnosis, or clinical guidelines.
        </div>
      </CardContent>
    </Card>
  );
}
