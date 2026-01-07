'use client';

import { useState } from 'react';
import { type UniqueSlide, getSlideImageUrl } from '@/lib/api';

interface SlideGalleryProps {
  slides: UniqueSlide[];
  jobId: string;
}

export default function SlideGallery({ slides, jobId }: SlideGalleryProps) {
  const [selectedSlide, setSelectedSlide] = useState<UniqueSlide | null>(null);

  if (slides.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Slides</h2>
        <p className="text-gray-600">No slides detected in this video.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Unique Slides ({slides.length})
      </h2>

      {/* Slide Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {slides.map((slide) => (
          <div
            key={slide.slide_id}
            className="border border-gray-200 rounded-lg overflow-hidden cursor-pointer hover:shadow-lg transition-shadow group"
            onClick={() => setSelectedSlide(slide)}
          >
            <div className="aspect-video bg-gray-100 relative">
              <img
                src={getSlideImageUrl(jobId, slide.slide_id)}
                alt={`Slide ${slide.slide_id}`}
                className="w-full h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage not available%3C/text%3E%3C/svg%3E';
                }}
              />
              {/* Overlay indicator for discussion summary */}
              {slide.discussion_summary && (
                <div className="absolute top-2 right-2 bg-blue-600 text-white p-1.5 rounded-full shadow-md" title="Has discussion summary">
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </div>
            <div className="p-3">
              <div className="flex justify-between items-start mb-1">
                <p className="text-sm font-medium text-gray-900">
                  {slide.slide_id}
                </p>
                <p className="text-xs text-gray-500">
                  {slide.appearances.length}x
                </p>
              </div>
              {/* Show discussion summary preview */}
              {slide.discussion_summary ? (
                <div className="mt-2">
                  <p className="text-xs text-blue-600 font-medium mb-1">Discussion Summary:</p>
                  <p className="text-xs text-gray-600 line-clamp-2">
                    {slide.discussion_summary}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-gray-400 mt-2 italic">
                  No discussion summary
                </p>
              )}
              {/* Show OCR preview if available */}
              {slide.ocr_text && (
                <p className="text-xs text-gray-500 mt-2 line-clamp-1 opacity-0 group-hover:opacity-100 transition-opacity" title={slide.ocr_text}>
                  📄 {slide.ocr_text.slice(0, 50)}...
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Slide Detail Modal */}
      {selectedSlide && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedSlide(null)}
        >
          <div
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-2xl font-bold text-gray-900">
                  {selectedSlide.slide_id}
                </h3>
                <button
                  onClick={() => setSelectedSlide(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>

              <div className="mb-6">
                <img
                  src={getSlideImageUrl(jobId, selectedSlide.slide_id)}
                  alt={`Slide ${selectedSlide.slide_id}`}
                  className="w-full rounded-lg border border-gray-200"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage not available%3C/text%3E%3C/svg%3E';
                  }}
                />
              </div>

              {/* Appearances */}
              <div className="mb-4">
                <h4 className="text-lg font-semibold text-gray-800 mb-2">
                  Appearances
                </h4>
                <div className="flex flex-wrap gap-2">
                  {selectedSlide.appearances.map((app, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                    >
                      {app.start} - {app.end}
                    </span>
                  ))}
                </div>
              </div>

              {/* OCR Text */}
              {selectedSlide.ocr_text && (
                <div className="mb-4">
                  <h4 className="text-lg font-semibold text-gray-800 mb-2">
                    Extracted Text
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 text-sm whitespace-pre-wrap">
                      {selectedSlide.ocr_text}
                    </p>
                  </div>
                </div>
              )}

              {/* Discussion Summary */}
              {selectedSlide.discussion_summary && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-2">
                    Discussion Summary
                  </h4>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <p className="text-gray-700 text-sm">
                      {selectedSlide.discussion_summary}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}



