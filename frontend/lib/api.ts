/** API client functions for backend communication. */
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface UploadResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface ProcessingStep {
  name: string;
  progress: number;
  status: string; // "pending", "in_progress", "complete", "error"
  details?: string;
}

export interface StatusResponse {
  job_id: string;
  status: string;
  progress?: number;
  current_step?: string;
  steps?: ProcessingStep[];
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface SlideAppearance {
  start: string;
  end: string;
}

export interface UniqueSlide {
  slide_id: string;
  image_url: string;
  appearances: SlideAppearance[];
  ocr_text: string;
  discussion_summary?: string;
}

export interface MeetingSummary {
  executive_summary: string;
  decisions: string[];
  action_items: string[];
  key_topics?: string[];
}

export interface ProcessingOptions {
  enable_transcription: boolean;
  enable_slide_detection: boolean;
  enable_summarization: boolean;
  enable_slide_summaries: boolean;
  return_transcript: boolean;
  return_slides: boolean;
  deduplication_method: 'both' | 'text_only' | 'visual_only';
}

export interface ResultsResponse {
  summary?: MeetingSummary;
  slides?: UniqueSlide[];
  transcript?: any[];
}

/**
 * Upload a video file with processing options.
 */
export async function uploadVideo(
  file: File,
  options?: Partial<ProcessingOptions>
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  // Add processing options as form fields
  const defaultOptions: ProcessingOptions = {
    enable_transcription: true,
    enable_slide_detection: true,
    enable_summarization: true,
    enable_slide_summaries: false,
    return_transcript: true,
    return_slides: true,
    deduplication_method: 'both',
  };
  
  const finalOptions = { ...defaultOptions, ...options };
  formData.append('enable_transcription', String(finalOptions.enable_transcription));
  formData.append('enable_slide_detection', String(finalOptions.enable_slide_detection));
  formData.append('enable_summarization', String(finalOptions.enable_summarization));
  formData.append('enable_slide_summaries', String(finalOptions.enable_slide_summaries));
  formData.append('return_transcript', String(finalOptions.return_transcript));
  formData.append('return_slides', String(finalOptions.return_slides));
  formData.append('deduplication_method', finalOptions.deduplication_method);

  const response = await api.post<UploadResponse>('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Get processing status for a job.
 */
export async function getStatus(jobId: string): Promise<StatusResponse> {
  const response = await api.get<StatusResponse>(`/api/status/${jobId}`);
  return response.data;
}

/**
 * Get final results for a completed job.
 */
export async function getResults(jobId: string): Promise<ResultsResponse> {
  const response = await api.get<ResultsResponse>(`/api/results/${jobId}`);
  return response.data;
}

/**
 * Get slide image URL.
 */
export function getSlideImageUrl(jobId: string, slideId: string): string {
  return `${API_URL}/api/results/${jobId}/slide/${slideId}`;
}



