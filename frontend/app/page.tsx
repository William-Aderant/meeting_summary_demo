'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import VideoUpload from '@/components/VideoUpload';

export default function Home() {
  const router = useRouter();
  const [jobId, setJobId] = useState<string | null>(null);

  const handleUploadSuccess = (uploadedJobId: string) => {
    setJobId(uploadedJobId);
    router.push(`/results/${uploadedJobId}`);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Meeting Summary Demo
          </h1>
          <p className="text-lg text-gray-600">
            Upload a meeting video to get automated transcription, summarization, and slide extraction
          </p>
        </div>

        <VideoUpload onUploadSuccess={handleUploadSuccess} />
      </div>
    </main>
  );
}



