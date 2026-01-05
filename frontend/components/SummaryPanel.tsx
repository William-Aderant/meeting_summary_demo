'use client';

import { type MeetingSummary } from '@/lib/api';

interface SummaryPanelProps {
  summary: MeetingSummary;
}

export default function SummaryPanel({ summary }: SummaryPanelProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Meeting Summary</h2>

      <div className="space-y-6">
        {/* Executive Summary */}
        <section>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Executive Summary</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {summary.executive_summary}
            </p>
          </div>
        </section>

        {/* Key Decisions */}
        {summary.decisions && summary.decisions.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Key Decisions</h3>
            <ul className="space-y-2">
              {summary.decisions.map((decision, index) => (
                <li key={index} className="flex items-start">
                  <svg
                    className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-700">{decision}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Action Items */}
        {summary.action_items && summary.action_items.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Action Items</h3>
            <ul className="space-y-2">
              {summary.action_items.map((item, index) => (
                <li key={index} className="flex items-start">
                  <svg
                    className="w-5 h-5 text-green-600 mr-2 mt-0.5 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Key Topics */}
        {summary.key_topics && summary.key_topics.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Key Topics</h3>
            <div className="flex flex-wrap gap-2">
              {summary.key_topics.map((topic, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                >
                  {topic}
                </span>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}



