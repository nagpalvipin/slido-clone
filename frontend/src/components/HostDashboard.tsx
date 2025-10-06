/**
 * Host Dashboard Layout
 * 
 * Main interface for event hosts to manage polls and questions.
 * Includes event information, navigation, and real-time content areas.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useEventState, usePollsState, useQuestionsState } from '../hooks/useRealTime';
import { api } from '../services/api';

export interface HostDashboardProps {
  eventSlug?: string;
}

export const HostDashboard: React.FC<HostDashboardProps> = ({ eventSlug: propEventSlug }) => {
  const { eventSlug: paramEventSlug } = useParams<{ eventSlug: string }>();
  const navigate = useNavigate();
  const eventSlug = propEventSlug || paramEventSlug;

  const [activeTab, setActiveTab] = useState<'polls' | 'questions'>('polls');
  const [authError, setAuthError] = useState<string | null>(null);

  // Real-time state hooks
  const { event, isLoading: eventLoading, error: eventError, connected } = useEventState(eventSlug || '');
  const { polls, isLoading: pollsLoading, error: pollsError } = usePollsState(eventSlug || '');
  const { questions, isLoading: questionsLoading, error: questionsError } = useQuestionsState(eventSlug || '');

  // Authentication check
  useEffect(() => {
    const hostCode = localStorage.getItem('hostCode');
    if (!hostCode && eventSlug) {
      // Redirect to authentication
      navigate(`/host/${eventSlug}/auth`);
    } else if (hostCode) {
      api.auth.setHostCode(hostCode);
    }
  }, [eventSlug, navigate]);

  if (!eventSlug) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Invalid Event</h1>
          <p className="text-gray-600">No event slug provided.</p>
        </div>
      </div>
    );
  }

  if (eventLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading event...</p>
        </div>
      </div>
    );
  }

  if (eventError || authError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-red-900 mb-4">Access Error</h1>
          <p className="text-gray-600 mb-4">{eventError || authError}</p>
          <button
            onClick={() => navigate(`/host/${eventSlug}/auth`)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md"
          >
            Authenticate as Host
          </button>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Event Not Found</h1>
          <p className="text-gray-600">The requested event could not be found.</p>
        </div>
      </div>
    );
  }

  const activePollsCount = polls.filter(poll => poll.status === 'active').length;
  const totalQuestionsCount = questions.length;
  const pendingQuestionsCount = questions.filter(q => q.status === 'pending').length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Event Info */}
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-semibold text-gray-900">{event.title}</h1>
              </div>
              <div className="ml-6 flex items-center space-x-4">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {event.slug}
                </span>
                <div className="flex items-center">
                  <div className={`h-2 w-2 rounded-full mr-2 ${connected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  <span className="text-sm text-gray-500">
                    {connected ? 'Live' : 'Connecting...'}
                  </span>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="flex items-center space-x-6">
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">{activePollsCount}</div>
                <div className="text-xs text-gray-500">Active Polls</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">{totalQuestionsCount}</div>
                <div className="text-xs text-gray-500">Questions</div>
              </div>
              {pendingQuestionsCount > 0 && (
                <div className="text-center">
                  <div className="text-lg font-semibold text-amber-600">{pendingQuestionsCount}</div>
                  <div className="text-xs text-amber-600">Pending</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('polls')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'polls'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Polls
              {activePollsCount > 0 && (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  {activePollsCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('questions')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'questions'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Questions
              {pendingQuestionsCount > 0 && (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                  {pendingQuestionsCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {activeTab === 'polls' && (
            <div>
              {/* Poll Management Section */}
              <div className="mb-6">
                <div className="sm:flex sm:items-center">
                  <div className="sm:flex-auto">
                    <h2 className="text-lg font-medium text-gray-900">Poll Management</h2>
                    <p className="mt-2 text-sm text-gray-700">
                      Create and manage polls for your event. Polls will update in real-time for all attendees.
                    </p>
                  </div>
                  <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                    <button
                      type="button"
                      className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
                    >
                      Create New Poll
                    </button>
                  </div>
                </div>
              </div>

              {/* Polls List */}
              {pollsLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading polls...</p>
                </div>
              ) : pollsError ? (
                <div className="text-center py-8">
                  <p className="text-red-600">Error loading polls: {pollsError}</p>
                </div>
              ) : polls.length === 0 ? (
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
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No polls yet</h3>
                  <p className="mt-1 text-sm text-gray-500">Get started by creating your first poll.</p>
                  <div className="mt-6">
                    <button
                      type="button"
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Create Poll
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {polls.map((poll) => (
                    <div
                      key={poll.id}
                      className="bg-white overflow-hidden shadow rounded-lg"
                    >
                      <div className="px-4 py-5 sm:p-6">
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-medium text-gray-900 truncate">
                              {poll.question_text}
                            </h3>
                            <div className="mt-1 flex items-center space-x-2">
                              <span
                                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  poll.status === 'active'
                                    ? 'bg-green-100 text-green-800'
                                    : poll.status === 'closed'
                                    ? 'bg-gray-100 text-gray-800'
                                    : 'bg-yellow-100 text-yellow-800'
                                }`}
                              >
                                {poll.status}
                              </span>
                              <span className="text-sm text-gray-500">
                                {poll.poll_type} choice
                              </span>
                              <span className="text-sm text-gray-500">
                                {poll.options?.reduce((sum, opt) => sum + (opt.vote_count || 0), 0) || 0} votes
                              </span>
                            </div>
                          </div>
                          <div className="flex-shrink-0 flex space-x-2">
                            {poll.status === 'draft' && (
                              <button className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm">
                                Activate
                              </button>
                            )}
                            {poll.status === 'active' && (
                              <button className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm">
                                Close
                              </button>
                            )}
                            <button className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm">
                              View Results
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'questions' && (
            <div>
              {/* Questions Management Section */}
              <div className="mb-6">
                <div className="sm:flex sm:items-center">
                  <div className="sm:flex-auto">
                    <h2 className="text-lg font-medium text-gray-900">Question Management</h2>
                    <p className="mt-2 text-sm text-gray-700">
                      Review and moderate questions from attendees. Approved questions will be visible to all participants.
                    </p>
                  </div>
                  {pendingQuestionsCount > 0 && (
                    <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                      <span className="inline-flex items-center rounded-md bg-amber-100 px-3 py-2 text-sm font-medium text-amber-800">
                        {pendingQuestionsCount} pending review
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Questions List */}
              {questionsLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading questions...</p>
                </div>
              ) : questionsError ? (
                <div className="text-center py-8">
                  <p className="text-red-600">Error loading questions: {questionsError}</p>
                </div>
              ) : questions.length === 0 ? (
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
              ) : (
                <div className="space-y-4">
                  {questions.map((question) => (
                    <div
                      key={question.id}
                      className={`bg-white overflow-hidden shadow rounded-lg ${
                        question.status === 'pending' ? 'ring-2 ring-amber-200' : ''
                      }`}
                    >
                      <div className="px-4 py-5 sm:p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="text-lg text-gray-900">{question.question_text}</p>
                            <div className="mt-2 flex items-center space-x-2">
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
                              <span className="text-sm text-gray-500">
                                {question.upvote_count} upvotes
                              </span>
                              <span className="text-sm text-gray-500">
                                {new Date(question.created_at).toLocaleString()}
                              </span>
                            </div>
                          </div>
                          {question.status === 'pending' && (
                            <div className="flex-shrink-0 flex space-x-2">
                              <button className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm">
                                Approve
                              </button>
                              <button className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm">
                                Reject
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};