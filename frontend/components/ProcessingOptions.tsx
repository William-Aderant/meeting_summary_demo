'use client';

import { useState } from 'react';
import { ProcessingOptions } from '@/lib/api';

interface ProcessingOptionsProps {
  options: ProcessingOptions;
  onChange: (options: ProcessingOptions) => void;
}

export default function ProcessingOptionsPanel({ options, onChange }: ProcessingOptionsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleChange = (field: keyof ProcessingOptions, value: boolean | string) => {
    onChange({
      ...options,
      [field]: value,
    });
  };

  return (
    <div className="w-full border border-gray-200 rounded-lg p-4 bg-white">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-left"
      >
        <h3 className="text-lg font-semibold text-gray-800">Processing Options</h3>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Feature Toggles */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Enable Features</h4>
            
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options.enable_transcription}
                onChange={(e) => handleChange('enable_transcription', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Transcribe Audio</span>
            </label>

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options.enable_slide_detection}
                onChange={(e) => handleChange('enable_slide_detection', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Detect Slides</span>
            </label>

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options.enable_summarization}
                onChange={(e) => handleChange('enable_summarization', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Generate Summary</span>
            </label>

            <label className="flex items-start space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options.enable_slide_summaries}
                onChange={(e) => handleChange('enable_slide_summaries', e.target.checked)}
                disabled={!options.enable_slide_detection || !options.enable_transcription}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed mt-0.5"
              />
              <div className="flex-1">
                <span className={`text-sm font-medium ${(!options.enable_slide_detection || !options.enable_transcription) ? 'text-gray-400' : 'text-gray-700'}`}>
                  Generate Individual Slide Summaries
                </span>
                <p className={`text-xs mt-0.5 ${(!options.enable_slide_detection || !options.enable_transcription) ? 'text-gray-400' : 'text-gray-500'}`}>
                  Creates a unique summary for each slide based on its text and discussion during its appearance
                </p>
              </div>
            </label>
          </div>

          {/* Return Options */}
          <div className="space-y-3 border-t pt-3">
            <h4 className="text-sm font-medium text-gray-700">Include in Results</h4>
            
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options.return_transcript}
                onChange={(e) => handleChange('return_transcript', e.target.checked)}
                disabled={!options.enable_transcription}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <span className={`text-sm ${!options.enable_transcription ? 'text-gray-400' : 'text-gray-700'}`}>
                Include Transcript
              </span>
            </label>

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options.return_slides}
                onChange={(e) => handleChange('return_slides', e.target.checked)}
                disabled={!options.enable_slide_detection}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <span className={`text-sm ${!options.enable_slide_detection ? 'text-gray-400' : 'text-gray-700'}`}>
                Include Slides
              </span>
            </label>
          </div>

          {/* Deduplication Method */}
          {options.enable_slide_detection && (
            <div className="space-y-2 border-t pt-3">
              <h4 className="text-sm font-medium text-gray-700">Slide Deduplication Method</h4>
              
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="deduplication_method"
                  value="both"
                  checked={options.deduplication_method === 'both'}
                  onChange={(e) => handleChange('deduplication_method', e.target.value)}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Both (Visual + Text Similarity)</span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="deduplication_method"
                  value="text_only"
                  checked={options.deduplication_method === 'text_only'}
                  onChange={(e) => handleChange('deduplication_method', e.target.value)}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Text Similarity Only</span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="deduplication_method"
                  value="visual_only"
                  checked={options.deduplication_method === 'visual_only'}
                  onChange={(e) => handleChange('deduplication_method', e.target.value)}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Visual Similarity Only</span>
              </label>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

