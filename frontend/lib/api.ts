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

export interface ResultsResponse {
  summary: MeetingSummary;
  slides: UniqueSlide[];
}

/**
 * Upload a video file.
 */
export async function uploadVideo(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

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



