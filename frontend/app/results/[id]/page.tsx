'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getStatus, getResults, type ResultsResponse, type StatusResponse } from '@/lib/api';
import ProcessingStatus from '@/components/ProcessingStatus';
import SummaryPanel from '@/components/SummaryPanel';
import SlideGallery from '@/components/SlideGallery';
import TranscriptPanel from '@/components/TranscriptPanel';
import DownloadButtons from '@/components/DownloadButtons';

export default function ResultsPage() {
  const params = useParams();
  const jobId = params.id as string;
  
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const fetchStatus = async () => {
      try {
        const statusData = await getStatus(jobId);
        setStatus(statusData);
        
        // Set loading to false once we have status data (even if still processing)
        // This allows the progress bar to be shown instead of the spinner
        setLoading(false);

        if (statusData.status === 'complete') {
          const resultsData = await getResults(jobId);
          setResults(resultsData);
        } else if (statusData.status === 'error') {
          // Error state is already handled
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status');
        setLoading(false);
      }
    };

    fetchStatus();

    // Poll for status updates if not complete
    const pollInterval = setInterval(() => {
      fetchStatus();
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [jobId]);

  // Only show loading spinner on initial load (before we have any status data)
  if (loading && !status) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <a href="/" className="text-blue-600 hover:underline">
            Return to home
          </a>
        </div>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <a
            href="/"
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to upload
          </a>
        </div>

        <ProcessingStatus status={status} />

        {status.status === 'complete' && results && (
          <div className="mt-8 space-y-8">
            {/* Download buttons at the top for easy access */}
            <DownloadButtons jobId={jobId} />
            
            {/* Meeting Summary */}
            {results.summary && <SummaryPanel summary={results.summary} />}
            
            {/* Slides with discussion summaries */}
            {results.slides && results.slides.length > 0 && (
              <SlideGallery slides={results.slides} jobId={jobId} />
            )}
            
            {/* Full transcript */}
            {results.transcript && results.transcript.length > 0 && (
              <TranscriptPanel transcript={results.transcript} />
            )}
          </div>
        )}

        {status.status === 'error' && (
          <div className="mt-8 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              <strong>Error:</strong> {status.error || 'Unknown error occurred'}
            </p>
          </div>
        )}
      </div>
    </main>
  );
}

