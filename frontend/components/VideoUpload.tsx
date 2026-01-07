'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadVideo, ProcessingOptions } from '@/lib/api';
import ProcessingOptionsPanel from './ProcessingOptions';

interface VideoUploadProps {
  onUploadSuccess: (jobId: string) => void;
}

export default function VideoUpload({ onUploadSuccess }: VideoUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [processingOptions, setProcessingOptions] = useState<ProcessingOptions>({
    enable_transcription: true,
    enable_slide_detection: true,
    enable_summarization: true,
    enable_slide_summaries: true,  // Enable per-slide summaries by default
    return_transcript: true,
    return_slides: true,
    deduplication_method: 'both',
  });

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|mov|avi|mkv|webm|m4v)$/i)) {
      setError('Invalid file type. Please upload a video file (mp4, mov, avi, mkv, webm, m4v)');
      return;
    }

    // Validate file size (max 500MB)
    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
      setError('File size too large. Maximum size is 500MB');
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      // Simulate upload progress (in production, use actual upload progress)
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await uploadVideo(file, processingOptions);
      clearInterval(progressInterval);
      setProgress(100);

      onUploadSuccess(response.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setUploading(false);
      setProgress(0);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div className="w-full space-y-4">
      <ProcessingOptionsPanel
        options={processingOptions}
        onChange={setProcessingOptions}
      />
      
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-colors duration-200
          ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50'
          }
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <svg
              className="w-16 h-16 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          {uploading ? (
            <div className="space-y-2">
              <p className="text-lg font-medium text-gray-700">Uploading...</p>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-500">{progress}%</p>
            </div>
          ) : (
            <>
              <p className="text-lg font-medium text-gray-700">
                {isDragActive
                  ? 'Drop the video here'
                  : 'Drag and drop a video file here, or click to select'}
              </p>
              <p className="text-sm text-gray-500">
                Supports MP4, MOV, AVI, MKV, WebM, M4V (max 500MB)
              </p>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}

