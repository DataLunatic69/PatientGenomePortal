import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import type { AnalysisJobRead } from '../types/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';

export default function ProgressPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState<AnalysisJobRead | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: number;

    async function pollStatus() {
      if (!jobId) return;
      try {
        const data = await api.getAnalysisStatus(jobId);
        setJob(data);

        if (data.status === 'completed') {
          clearInterval(interval);
          setTimeout(() => navigate(`/dashboard/${jobId}`), 1500);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setError(data.error_message || 'Analysis failed with an unknown error.');
        }
      } catch (err: any) {
        clearInterval(interval);
        setError(err.message || 'Failed to fetch status.');
      }
    }

    pollStatus();
    interval = window.setInterval(pollStatus, 3000);

    return () => clearInterval(interval);
  }, [jobId, navigate]);

  const getProgressValue = (status?: string, pct?: number) => {
    if (pct !== undefined && pct > 0) return pct;
    
    switch (status) {
      case 'pending': return 5;
      case 'parsing': return 25;
      case 'enriching': return 50;
      case 'scoring': return 75;
      case 'ranking': return 85;
      case 'explaining': return 95;
      case 'completed': return 100;
      case 'failed': return 100;
      default: return 0;
    }
  };

  if (error) {
    return (
      <div className="max-w-xl mx-auto mt-20">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto mt-20">
      <Card className="text-center p-6">
        <CardHeader>
          <CardTitle className="text-2xl">Analysis in Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-6 flex flex-col items-center justify-center">
            {job?.status === 'completed' ? (
              <CheckCircle2 className="w-16 h-16 text-green-500 mb-4" />
            ) : (
              <Loader2 className="w-16 h-16 text-blue-500 animate-spin mb-4" />
            )}
            <h3 className="text-lg font-medium capitalize">
              {job?.status || 'Processing...'}
            </h3>
            <p className="text-sm text-gray-500 mt-2">Job ID: {jobId}</p>
          </div>
          
          <Progress 
            value={getProgressValue(job?.status, job?.progress_pct)} 
            className={`w-full h-3 ${job?.status === 'failed' ? 'bg-red-200' : ''}`}
          />
        </CardContent>
      </Card>
    </div>
  );
}
