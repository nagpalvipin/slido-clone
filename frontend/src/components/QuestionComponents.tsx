/**
 * Question Components
 * 
 * Includes question submission form, question queue/list display, and moderation interface.
 * Handles question lifecycle from submission through moderation to display.
 */

import React, { useState } from 'react';
import { api, Question } from '../services/api';

// Question Submission Form Component
export interface QuestionSubmissionFormProps {
  eventId: number;
  onQuestionSubmitted?: (question: Question) => void;
  onCancel?: () => void;
}

export const QuestionSubmissionForm: React.FC<QuestionSubmissionFormProps> = ({
  eventId,
  onQuestionSubmitted,
  onCancel
}) => {
  const [questionText, setQuestionText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!questionText.trim()) {
      setError('Question text is required');
      return;
    }

    if (questionText.trim().length > 500) {
      setError('Question must be 500 characters or less');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const questionData = {
        question_text: questionText.trim()
      };

      const newQuestion = await api.questions.create(eventId, questionData);
      
      setSubmitted(true);
      setQuestionText('');

      if (onQuestionSubmitted) {
        onQuestionSubmitted(newQuestion);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit question');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
            <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Question Submitted!</h3>
          <p className="text-sm text-gray-600 mb-4">
            Your question has been submitted for review. It will appear in the Q&A section once approved by the host.
          </p>
          <div className="flex justify-center space-x-3">
            <button
              onClick={() => setSubmitted(false)}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Submit Another
            </button>
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Submit a Question</h3>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
            Your Question
          </label>
          <textarea
            id="question"
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="What would you like to ask?"
            required
          />
          <div className="mt-1 flex justify-between">
            <p className="text-sm text-gray-500">
              Your question will be reviewed before being published
            </p>
            <p className="text-sm text-gray-500">
              {questionText.length}/500 characters
            </p>
          </div>
        </div>

        <div className="flex justify-end space-x-3">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isSubmitting || !questionText.trim()}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Question'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Question List Component
export interface QuestionListProps {
  questions: Question[];
  eventId: number;
  allowUpvote?: boolean;
  showStatus?: boolean;
  onUpvote?: (questionId: number) => void;
}

export const QuestionList: React.FC<QuestionListProps> = ({
  questions,
  eventId,
  allowUpvote = true,
  showStatus = false,
  onUpvote
}) => {
  const [upvotingQuestions, setUpvotingQuestions] = useState<Set<number>>(new Set());

  // Handle upvote
  const handleUpvote = async (questionId: number) => {
    if (upvotingQuestions.has(questionId)) return;

    try {
      setUpvotingQuestions(prev => new Set([...prev, questionId]));
      await api.questions.upvote(eventId, questionId);
      
      if (onUpvote) {
        onUpvote(questionId);
      }
    } catch (err) {
      console.error('Failed to upvote question:', err);
    } finally {
      setUpvotingQuestions(prev => {
        const newSet = new Set(prev);
        newSet.delete(questionId);
        return newSet;
      });
    }
  };

  if (questions.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No questions yet</h3>
        <p className="mt-1 text-sm text-gray-500">
          {allowUpvote ? 'Be the first to ask a question!' : 'Questions will appear here once submitted.'}
        </p>
      </div>
    );
  }

  // Sort questions by upvote count and creation time
  const sortedQuestions = [...questions].sort((a, b) => {
    if (a.upvote_count !== b.upvote_count) {
      return b.upvote_count - a.upvote_count;
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <div className="space-y-4">
      {sortedQuestions.map((question) => (
        <div
          key={question.id}
          className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${
            showStatus && question.status === 'pending' ? 'ring-2 ring-amber-200' : ''
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-lg text-gray-900 mb-2">{question.question_text}</p>
              
              <div className="flex items-center space-x-3">
                {showStatus && (
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      question.status === 'approved'
                        ? 'bg-green-100 text-green-800'
                        : question.status === 'rejected'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {question.status}
                  </span>
                )}
                
                <span className="text-sm text-gray-500">
                  {new Date(question.created_at).toLocaleString()}
                </span>
                
                <span className="text-sm text-gray-500">
                  ID: {question.id}
                </span>
              </div>
            </div>
            
            {/* Upvote Button */}
            {allowUpvote && question.status === 'approved' && (
              <div className="flex-shrink-0 ml-4">
                <button
                  onClick={() => handleUpvote(question.id)}
                  disabled={upvotingQuestions.has(question.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                    question.upvote_count > 0
                      ? 'bg-indigo-100 text-indigo-800 hover:bg-indigo-200'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  } ${
                    upvotingQuestions.has(question.id) ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <svg
                    className={`w-4 h-4 ${upvotingQuestions.has(question.id) ? 'animate-pulse' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 15l7-7 7 7"
                    />
                  </svg>
                  <span>{question.upvote_count}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

// Question Moderation Interface Component
export interface QuestionModerationProps {
  questions: Question[];
  eventId: number;
  onQuestionModerated?: (questionId: number, status: 'approved' | 'rejected') => void;
}

export const QuestionModeration: React.FC<QuestionModerationProps> = ({
  questions,
  eventId,
  onQuestionModerated
}) => {
  const [moderatingQuestions, setModeratingQuestions] = useState<Set<number>>(new Set());

  // Handle moderation
  const handleModerate = async (questionId: number, status: 'approved' | 'rejected') => {
    if (moderatingQuestions.has(questionId)) return;

    try {
      setModeratingQuestions(prev => new Set([...prev, questionId]));
      await api.questions.moderate(eventId, questionId, status);
      
      if (onQuestionModerated) {
        onQuestionModerated(questionId, status);
      }
    } catch (err) {
      console.error('Failed to moderate question:', err);
    } finally {
      setModeratingQuestions(prev => {
        const newSet = new Set(prev);
        newSet.delete(questionId);
        return newSet;
      });
    }
  };

  // Filter questions by status
  const pendingQuestions = questions.filter(q => q.status === 'pending');
  const approvedQuestions = questions.filter(q => q.status === 'approved');
  const rejectedQuestions = questions.filter(q => q.status === 'rejected');

  return (
    <div className="space-y-8">
      {/* Pending Questions */}
      {pendingQuestions.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-amber-900 mb-4 flex items-center">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 mr-3">
              {pendingQuestions.length}
            </span>
            Pending Review
          </h3>
          
          <div className="space-y-4">
            {pendingQuestions.map((question) => (
              <div
                key={question.id}
                className="bg-white rounded-lg shadow-sm border-2 border-amber-200 p-6"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-lg text-gray-900 mb-2">{question.question_text}</p>
                    
                    <div className="flex items-center space-x-3">
                      <span className="text-sm text-gray-500">
                        {new Date(question.created_at).toLocaleString()}
                      </span>
                      <span className="text-sm text-gray-500">
                        {question.upvote_count} upvotes
                      </span>
                    </div>
                  </div>
                  
                  {/* Moderation Actions */}
                  <div className="flex-shrink-0 ml-4">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleModerate(question.id, 'approved')}
                        disabled={moderatingQuestions.has(question.id)}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                      >
                        {moderatingQuestions.has(question.id) ? 'Processing...' : 'Approve'}
                      </button>
                      <button
                        onClick={() => handleModerate(question.id, 'rejected')}
                        disabled={moderatingQuestions.has(question.id)}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                      >
                        {moderatingQuestions.has(question.id) ? 'Processing...' : 'Reject'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Approved Questions */}
      {approvedQuestions.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-green-900 mb-4 flex items-center">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mr-3">
              {approvedQuestions.length}
            </span>
            Approved Questions
          </h3>
          
          <QuestionList 
            questions={approvedQuestions} 
            eventId={eventId} 
            allowUpvote={false}
            showStatus={false}
          />
        </div>
      )}

      {/* Rejected Questions */}
      {rejectedQuestions.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-red-900 mb-4 flex items-center">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 mr-3">
              {rejectedQuestions.length}
            </span>
            Rejected Questions
          </h3>
          
          <QuestionList 
            questions={rejectedQuestions} 
            eventId={eventId} 
            allowUpvote={false}
            showStatus={false}
          />
        </div>
      )}

      {questions.length === 0 && (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No questions yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Questions submitted by attendees will appear here for moderation.
          </p>
        </div>
      )}
    </div>
  );
};