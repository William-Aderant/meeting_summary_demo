'use client';

import { useState } from 'react';

interface DownloadButtonsProps {
  jobId: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DownloadButtons({ jobId }: DownloadButtonsProps) {
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleDownload = async (format: 'txt' | 'pdf') => {
    setDownloading(format);
    try {
      const response = await fetch(`${API_URL}/api/results/${jobId}/download/${format}`);
      
      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `meeting_summary_${jobId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert(`Failed to download ${format.toUpperCase()} file. Please try again.`);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Download Results</h2>
      <p className="text-gray-600 mb-6">
        Download the complete meeting summary, slides information, and transcript in your preferred format.
      </p>
      
      <div className="flex flex-wrap gap-4">
        {/* PDF Download */}
        <button
          onClick={() => handleDownload('pdf')}
          disabled={downloading !== null}
          className="flex items-center gap-3 px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium rounded-lg transition-colors shadow-sm"
        >
          {downloading === 'pdf' ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clipRule="evenodd" />
            </svg>
          )}
          <div className="text-left">
            <div className="font-semibold">Download PDF</div>
            <div className="text-xs text-red-200">Formatted document</div>
          </div>
        </button>

        {/* TXT Download */}
        <button
          onClick={() => handleDownload('txt')}
          disabled={downloading !== null}
          className="flex items-center gap-3 px-6 py-3 bg-gray-700 hover:bg-gray-800 disabled:bg-gray-500 text-white font-medium rounded-lg transition-colors shadow-sm"
        >
          {downloading === 'txt' ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
            </svg>
          )}
          <div className="text-left">
            <div className="font-semibold">Download TXT</div>
            <div className="text-xs text-gray-400">Plain text file</div>
          </div>
        </button>
      </div>
    </div>
  );
}

