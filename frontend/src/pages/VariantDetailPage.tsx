import { useEffect, useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import type { VariantResultRead } from '../types/api';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';

export default function VariantDetailPage() {
  const { variantId } = useParams();
  const location = useLocation();
  const stateVariant = location.state?.variant as VariantResultRead | undefined;
  
  const [variant] = useState<VariantResultRead | null>(stateVariant || null);

  useEffect(() => {
    // If we have state variant, we don't necessarily need to fetch unless we want full tracks
    if (!variant && variantId) {
       // In a complete implementation we could fetch individual variant by ID
       // We'll rely on the Router state for now.
    }
  }, [variantId, variant]);

  if (!variant) return (
    <div className="p-8 text-center text-gray-500">
      Variant data not found. Please <Link to="/" className="text-blue-500 hover:underline">go back</Link> and try again.
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link to={`/dashboard/${variant.analysis_job_id}`} className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
      </Link>
      
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold mb-2">{variant.gene_name || 'Unknown Gene'} Variant</h1>
          <p className="text-gray-600 text-lg">
            {variant.chromosome}:{variant.position} ({variant.reference_bases} → {variant.alternate_bases})
          </p>
        </div>
        <Badge variant={variant.gemini_risk_level === 'high' ? 'destructive' : 'secondary'} className="text-lg py-1 px-4 capitalize">
          Risk: {variant.gemini_risk_level || 'Unknown'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Clinical Significance (ClinVar)</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              <li className="capitalize"><strong>Classification:</strong> {variant.clinvar_classification ? variant.clinvar_classification.replace('_', ' ') : 'Not Provided'}</li>
              <li><strong>Review Status:</strong> {variant.clinvar_review_status || 'Not Provided'}</li>
              <li><strong>ClinVar ID:</strong> {variant.clinvar_id || 'N/A'}</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AlphaGenome Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              <li><strong>Rank Position:</strong> #{variant.rank_position || 'N/A'}</li>
              <li><strong>Rank Score:</strong> {variant.rank_score !== null ? variant.rank_score.toFixed(4) : 'N/A'}</li>
              <li><strong>Splicing Score:</strong> {variant.splicing_score !== null ? variant.splicing_score.toFixed(4) : 'N/A'}</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900">
            <AlertTriangle className="w-5 h-5" /> AI Clinical Interpretation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-blue-800 leading-relaxed whitespace-pre-wrap">
            {variant.gemini_summary || "No AI interpretation available for this variant."}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
