export interface UploadResponse {
  dna_file_id: string;
  job_id: string;
  message: string;
}

export interface AnalysisJobRead {
  id: string;
  dna_file_id: string;
  status: string;
  current_step: string | null;
  progress_pct: number;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface VariantResultRead {
  id: string;
  analysis_job_id: string;
  chromosome: string;
  position: number;
  reference_bases: string;
  alternate_bases: string;
  gene_name: string | null;
  gene_id: string | null;
  delta_scores: Record<string, any> | null;
  splicing_score: number | null;
  rank_score: number | null;
  rank_position: number | null;
  clinvar_id: string | null;
  clinvar_classification: string | null;
  clinvar_review_status: string | null;
  gemini_summary: string | null;
  gemini_risk_level: string | null;
  top_tissues_affected: string[] | null;
}

export interface VariantResultPage {
  total: number;
  page: number;
  page_size: number;
  items: VariantResultRead[];
}

export interface ReportRead {
  job_id: string;
  gemini_report: string;
  total_variants_analyzed: number;
  high_risk_count: number;
  moderate_risk_count: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ResultsChatResponse {
  answer: string;
}
