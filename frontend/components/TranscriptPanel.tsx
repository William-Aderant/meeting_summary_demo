'use client';

import { useState } from 'react';
import { type TranscriptSegment } from '@/lib/api';

interface TranscriptPanelProps {
  transcript: TranscriptSegment[];
}

function formatTimestamp(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function getSpeakerColor(speaker: number | undefined): string {
  if (speaker === undefined || speaker === null) return 'bg-gray-100 text-gray-800';
  const colors = [
    'bg-blue-100 text-blue-800',
    'bg-green-100 text-green-800',
    'bg-purple-100 text-purple-800',
    'bg-orange-100 text-orange-800',
    'bg-pink-100 text-pink-800',
    'bg-teal-100 text-teal-800',
    'bg-indigo-100 text-indigo-800',
    'bg-yellow-100 text-yellow-800',
  ];
  return colors[speaker % colors.length];
}

export default function TranscriptPanel({ transcript }: TranscriptPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  if (!transcript || transcript.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Transcript</h2>
        <p className="text-gray-600">No transcript available for this video.</p>
      </div>
    );
  }

  // Filter transcript based on search
  const filteredTranscript = searchQuery
    ? transcript.filter(segment =>
        segment.text.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : transcript;

  // Get unique speakers
  const speakers = [...new Set(transcript.map(s => s.speaker).filter(s => s !== undefined && s !== null))];

  // Calculate total duration
  const totalDuration = transcript.length > 0 
    ? formatTimestamp(transcript[transcript.length - 1].end)
    : '00:00:00';

  // Show preview or full transcript
  const displayedTranscript = isExpanded ? filteredTranscript : filteredTranscript.slice(0, 10);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Full Transcript</h2>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>{transcript.length} segments</span>
          <span>•</span>
          <span>{speakers.length} speaker{speakers.length !== 1 ? 's' : ''}</span>
          <span>•</span>
          <span>{totalDuration}</span>
        </div>
      </div>

      {/* Search bar */}
      <div className="mb-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Search transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg
            className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        {searchQuery && (
          <p className="mt-2 text-sm text-gray-500">
            Found {filteredTranscript.length} matching segment{filteredTranscript.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      {/* Speaker legend */}
      {speakers.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {speakers.map(speaker => (
            <span
              key={speaker}
              className={`px-3 py-1 rounded-full text-sm font-medium ${getSpeakerColor(speaker)}`}
            >
              Speaker {speaker}
            </span>
          ))}
        </div>
      )}

      {/* Transcript segments */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
        {displayedTranscript.map((segment, index) => (
          <div
            key={index}
            className="flex gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100"
          >
            <div className="flex-shrink-0 w-20">
              <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {formatTimestamp(segment.start)}
              </span>
            </div>
            <div className="flex-grow">
              {segment.speaker !== undefined && segment.speaker !== null && (
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-1 ${getSpeakerColor(segment.speaker)}`}
                >
                  Speaker {segment.speaker}
                </span>
              )}
              <p className="text-gray-700 leading-relaxed">{segment.text}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Show more/less button */}
      {filteredTranscript.length > 10 && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors"
          >
            {isExpanded ? (
              <>
                <span>Show Less</span>
                <svg
                  className="inline-block w-4 h-4 ml-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              </>
            ) : (
              <>
                <span>Show All {filteredTranscript.length} Segments</span>
                <svg
                  className="inline-block w-4 h-4 ml-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

