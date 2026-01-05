'use client';

import { type StatusResponse, type ProcessingStep } from '@/lib/api';

interface ProcessingStatusProps {
  status: StatusResponse;
}

export default function ProcessingStatus({ status }: ProcessingStatusProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'processing':
        return (
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  const getStepStatusIcon = (step: ProcessingStep) => {
    if (step.status === 'complete') {
      return (
        <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      );
    } else if (step.status === 'in_progress') {
      return (
        <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      );
    } else {
      return (
        <div className="w-5 h-5 rounded-full border-2 border-gray-300"></div>
      );
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Processing Status</h2>
        <div
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${getStatusColor(
            status.status
          )}`}
        >
          {getStatusIcon(status.status)}
          <span className="font-medium capitalize">{status.status}</span>
        </div>
      </div>

      {/* Overall Progress Bar */}
      {status.progress !== null && status.progress !== undefined && (
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span className="font-medium">Overall Progress</span>
            <span className="font-semibold">{Math.round(status.progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${status.progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Step-by-Step Progress */}
      {status.steps && status.steps.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Processing Steps</h3>
          <div className="space-y-3">
            {status.steps.map((step, index) => (
              <div
                key={index}
                className={`border rounded-lg p-4 ${
                  step.status === 'in_progress'
                    ? 'border-blue-300 bg-blue-50'
                    : step.status === 'complete'
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getStepStatusIcon(step)}
                    <span
                      className={`font-medium ${
                        step.status === 'in_progress'
                          ? 'text-blue-900'
                          : step.status === 'complete'
                          ? 'text-green-900'
                          : 'text-gray-600'
                      }`}
                    >
                      {step.name}
                    </span>
                  </div>
                  <span className="text-sm font-semibold text-gray-600">
                    {Math.round(step.progress)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      step.status === 'complete'
                        ? 'bg-green-600'
                        : step.status === 'in_progress'
                        ? 'bg-blue-600'
                        : 'bg-gray-300'
                    }`}
                    style={{ width: `${step.progress}%` }}
                  ></div>
                </div>
                {step.details && (
                  <p className="text-xs text-gray-500 mt-1 italic">{step.details}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fallback for when steps aren't available */}
      {(!status.steps || status.steps.length === 0) && status.current_step && (
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-1">Current Step:</p>
          <p className="text-lg font-medium text-gray-900">{status.current_step}</p>
        </div>
      )}

      {status.status === 'processing' && (
        <p className="text-sm text-gray-500 italic mt-4">
          Processing may take several minutes depending on video length...
        </p>
      )}
    </div>
  );
}



