import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../lib/api';
import type { VariantResultRead, ReportRead } from '../types/api';
import VariantTable from '../components/variants/VariantTable';
import PatientReport from '../components/reports/PatientReport';
import ResultsChatPanel from '../components/chat/ResultsChatPanel';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Loader2 } from 'lucide-react';

export default function DashboardPage() {
  const { jobId } = useParams();
  const [variants, setVariants] = useState<VariantResultRead[]>([]);
  const [report, setReport] = useState<ReportRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      if (!jobId) return;
      try {
        setLoading(true);
        const [variantData, reportData] = await Promise.all([
          api.getVariants(jobId),
          api.getReport(jobId)
        ]);
        setVariants(variantData.items);
        setReport(reportData);
      } catch (err: any) {
        setError(err.message || 'Failed to load variants');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [jobId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20">
        <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
        <p className="text-gray-500">Loading variant data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500">
        Error loading dashboard: {error}
      </div>
    );
  }

  const highRiskCount = variants.filter(v => v.gemini_risk_level?.toLowerCase() === 'high').length;
  const moderateRiskCount = variants.filter(v => v.gemini_risk_level?.toLowerCase() === 'moderate').length;

  return (
    <div className="mx-auto max-w-7xl">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-10">
        <div className="space-y-6 lg:col-span-7">
          <div>
            <h1 className="mb-2 text-3xl font-bold">Variant Analysis Dashboard</h1>
            <p className="text-gray-500">Job ID: {jobId}</p>
          </div>

          <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">Total Variants Analyzed</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{report?.total_variants_analyzed || variants.length}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">High Risk Findings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-red-600">{report?.high_risk_count ?? highRiskCount}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">Moderate Risk</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-500">{report?.moderate_risk_count ?? moderateRiskCount}</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Top Identified Variants</CardTitle>
            </CardHeader>
            <CardContent>
              <VariantTable variants={variants} />
            </CardContent>
          </Card>

          <PatientReport variants={variants} reportText={report?.gemini_report} />
        </div>

        <div className="lg:col-span-3">
          {jobId ? <ResultsChatPanel jobId={jobId} /> : null}
        </div>
      </div>
    </div>
  );
}
