/**
 * Attendee Interface Layout
 * 
 * Clean interface for event attendees to view polls, vote, and submit questions.
 * Focused on participation rather than management.
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useEventState, usePollsState, useQuestionsState } from '../hooks/useRealTime';
import { api } from '../services/api';

export interface AttendeeInterfaceProps {
  eventSlug?: string;
}

export const AttendeeInterface: React.FC<AttendeeInterfaceProps> = ({ eventSlug: propEventSlug }) => {
  const { eventSlug: paramEventSlug } = useParams<{ eventSlug: string }>();
  const eventSlug = propEventSlug || paramEventSlug;

  const [activeTab, setActiveTab] = useState<'polls' | 'questions'>('polls');
  const [showQuestionForm, setShowQuestionForm] = useState(false);
  const [highlightedQuestions, setHighlightedQuestions] = useState<Set<number>>(new Set());

  // Real-time state hooks
  const { event, isLoading: eventLoading, error: eventError, connected } = useEventState(eventSlug || '');
  const { polls, isLoading: pollsLoading } = usePollsState(eventSlug || '');
  const { questions, isLoading: questionsLoading } = useQuestionsState(eventSlug || '');

  // Filter active polls for attendees (all questions are now public)
  const activePolls = polls.filter(poll => poll.status === 'active');

  // Detect new questions and trigger highlight animation
  useEffect(() => {
    const newQuestionIds = questions
      .filter(q => {
        // Check if question is less than 5 seconds old
        const createdAt = new Date(q.created_at).getTime();
        const now = Date.now();
        return (now - createdAt) < 5000;
      })
      .map(q => q.id);

    if (newQuestionIds.length > 0) {
      setHighlightedQuestions(new Set(newQuestionIds));
      
      // Remove highlight after 2 seconds
      setTimeout(() => {
        setHighlightedQuestions(new Set());
      }, 2000);
    }
  }, [questions]);

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

  if (eventError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-red-900 mb-4">Event Not Found</h1>
          <p className="text-gray-600 mb-4">{eventError}</p>
          <p className="text-sm text-gray-500">
            Please check the event link and try again.
          </p>
        </div>
      </div>
    );
  }

  if (!event || !event.is_active) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Event Unavailable</h1>
          <p className="text-gray-600 mb-4">
            {!event ? 'The requested event could not be found.' : 'This event is currently not active.'}
          </p>
          <p className="text-sm text-gray-500">
            Please contact the event organizer for more information.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Event Info */}
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-semibold text-gray-900">{event.title}</h1>
              </div>
              <div className="ml-4 flex items-center">
                <div className={`h-2 w-2 rounded-full mr-2 ${connected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span className="text-sm text-gray-500">
                  {connected ? 'Live' : 'Connecting...'}
                </span>
              </div>
            </div>

            {/* Event Code */}
            <div className="flex items-center">
              <span className="text-sm text-gray-500 mr-2">Event Code:</span>
              <span className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-indigo-100 text-indigo-800">
                {event.slug}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('polls')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'polls'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Live Polls
              {activePolls.length > 0 && (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  {activePolls.length}
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
              Q&A
              {questions.length > 0 && (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  {questions.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {activeTab === 'polls' && (
            <div>
              {/* Polls Section */}
              <div className="mb-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Live Polls</h2>
                
                {pollsLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading polls...</p>
                  </div>
                ) : activePolls.length === 0 ? (
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
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No active polls</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Check back soon for new polls from the host.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {activePolls.map((poll) => (
                      <div
                        key={poll.id}
                        className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
                      >
                        <h3 className="text-lg font-medium text-gray-900 mb-4">
                          {poll.question_text}
                        </h3>
                        
                        <div className="space-y-3">
                          {poll.options?.map((option) => {
                            const totalVotes = poll.options?.reduce((sum, opt) => sum + (opt.vote_count || 0), 0) || 0;
                            const percentage = totalVotes > 0 ? Math.round((option.vote_count / totalVotes) * 100) : 0;
                            
                            return (
                              <div key={option.id} className="relative">
                                <button
                                  className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                  // onClick={() => handleVote(poll.id, option.id)}
                                >
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-900">{option.option_text}</span>
                                    <div className="flex items-center space-x-2">
                                      <span className="text-sm text-gray-500">{option.vote_count || 0} votes</span>
                                      <span className="text-sm font-medium text-gray-900">{percentage}%</span>
                                    </div>
                                  </div>
                                  
                                  {/* Vote percentage bar */}
                                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                                    <div
                                      className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                                      style={{ width: `${percentage}%` }}
                                    ></div>
                                  </div>
                                </button>
                              </div>
                            );
                          })}
                        </div>
                        
                        <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                          <span>{poll.poll_type === 'single' ? 'Single choice' : 'Multiple choice'}</span>
                          <span>
                            {poll.options?.reduce((sum, opt) => sum + (opt.vote_count || 0), 0) || 0} total votes
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'questions' && (
            <div>
              {/* Questions Section */}
              <div className="mb-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-medium text-gray-900">Questions & Answers</h2>
                  <button
                    onClick={() => setShowQuestionForm(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Ask Question
                  </button>
                </div>
                <p className="mt-2 text-sm text-gray-700">
                  Ask questions and upvote others' questions. Popular questions will be highlighted.
                </p>
              </div>

              {/* Question Form */}
              {showQuestionForm && (
                <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Submit a Question</h3>
                  <form
                    onSubmit={async (e) => {
                      e.preventDefault();
                      const formData = new FormData(e.currentTarget);
                      const questionText = formData.get('questionText') as string;
                      
                      if (!questionText?.trim() || !event) return;
                      
                      try {
                        const newQuestion = await api.questions.create(event.id, {
                          question_text: questionText.trim()
                        });
                        
                        // Trigger highlight animation for the new question
                        setHighlightedQuestions(new Set([newQuestion.id]));
                        setTimeout(() => {
                          setHighlightedQuestions(new Set());
                        }, 2000);
                        
                        setShowQuestionForm(false);
                        // The real-time hooks will automatically update the questions list
                      } catch (error) {
                        console.error('Failed to submit question:', error);
                        // You could add error state here for user feedback
                      }
                    }}
                  >
                    <div className="mb-4">
                      <textarea
                        name="questionText"
                        className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                        rows={3}
                        placeholder="Type your question here..."
                        maxLength={500}
                        required
                      />
                      <p className="mt-1 text-xs text-gray-500">Maximum 500 characters</p>
                    </div>
                    <div className="flex justify-end space-x-3">
                      <button
                        type="button"
                        onClick={() => setShowQuestionForm(false)}
                        className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        Submit Question
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Questions List */}
              {questionsLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading questions...</p>
                </div>
              ) : questions.length === 0 ? (
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
                    Be the first to ask a question!
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {questions
                    .sort((a, b) => b.upvote_count - a.upvote_count) // Sort by upvotes
                    .map((question) => (
                      <div
                        key={question.id}
                        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 transition-all ${
                          highlightedQuestions.has(question.id) ? 'question-highlight' : ''
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="text-lg text-gray-900">{question.question_text}</p>
                            <div className="mt-2 flex items-center space-x-2">
                              <span className="text-sm text-gray-500">
                                {new Date(question.created_at).toLocaleString()}
                              </span>
                            </div>
                          </div>
                          
                          {/* Upvote Button */}
                          <div className="flex-shrink-0 ml-4">
                            <button
                              className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                              onClick={async () => {
                                if (!event) return;
                                try {
                                  await api.questions.upvote(event.id, question.id);
                                  // The real-time hooks will automatically update the question
                                } catch (error) {
                                  console.error('Failed to upvote question:', error);
                                }
                              }}
                            >
                              <svg
                                className="w-4 h-4"
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