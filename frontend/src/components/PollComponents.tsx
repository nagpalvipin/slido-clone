/**
 * Poll Components
 * 
 * Includes poll creation form, voting interface, and real-time results display.
 * Handles both single and multiple choice polls with real-time updates.
 */

import React, { useState, useEffect } from 'react';
import { api, Poll, PollOption } from '../services/api';

// Poll Creation Form Component
export interface PollCreateFormProps {
  eventId: number;
  onPollCreated?: (poll: Poll) => void;
  onCancel?: () => void;
}

export const PollCreateForm: React.FC<PollCreateFormProps> = ({
  eventId,
  onPollCreated,
  onCancel
}) => {
  const [questionText, setQuestionText] = useState('');
  const [pollType, setPollType] = useState<'single' | 'multiple'>('single');
  const [options, setOptions] = useState<Array<{ text: string; position: number }>>([
    { text: '', position: 0 },
    { text: '', position: 1 }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Add new option
  const addOption = () => {
    if (options.length < 10) {
      setOptions([...options, { text: '', position: options.length }]);
    }
  };

  // Remove option
  const removeOption = (index: number) => {
    if (options.length > 2) {
      const newOptions = options.filter((_, i) => i !== index);
      // Reorder positions
      newOptions.forEach((option, i) => {
        option.position = i;
      });
      setOptions(newOptions);
    }
  };

  // Update option text
  const updateOption = (index: number, text: string) => {
    const newOptions = [...options];
    newOptions[index].text = text;
    setOptions(newOptions);
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!questionText.trim()) {
      setError('Question text is required');
      return;
    }

    const validOptions = options.filter(opt => opt.text.trim());
    if (validOptions.length < 2) {
      setError('At least 2 options are required');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const pollData = {
        question_text: questionText.trim(),
        poll_type: pollType,
        options: validOptions.map((opt, index) => ({
          option_text: opt.text.trim(),
          position: index
        }))
      };

      const newPoll = await api.polls.create(eventId, pollData);
      
      if (onPollCreated) {
        onPollCreated(newPoll);
      }

      // Reset form
      setQuestionText('');
      setOptions([
        { text: '', position: 0 },
        { text: '', position: 1 }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create poll');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">Create New Poll</h3>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Question Text */}
        <div className="mb-6">
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
            Poll Question
          </label>
          <textarea
            id="question"
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Enter your poll question here..."
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            {questionText.length}/1000 characters
          </p>
        </div>

        {/* Poll Type */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Response Type
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setPollType('single')}
              className={`p-3 rounded-md border-2 text-sm font-medium ${
                pollType === 'single'
                  ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                  : 'border-gray-300 text-gray-700 hover:border-gray-400'
              }`}
            >
              Single Choice
              <p className="text-xs mt-1 text-gray-500">Participants can select one option</p>
            </button>
            <button
              type="button"
              onClick={() => setPollType('multiple')}
              className={`p-3 rounded-md border-2 text-sm font-medium ${
                pollType === 'multiple'
                  ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                  : 'border-gray-300 text-gray-700 hover:border-gray-400'
              }`}
            >
              Multiple Choice
              <p className="text-xs mt-1 text-gray-500">Participants can select multiple options</p>
            </button>
          </div>
        </div>

        {/* Options */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Answer Options
          </label>
          <div className="space-y-3">
            {options.map((option, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-6 text-center text-sm text-gray-500">
                  {index + 1}.
                </div>
                <input
                  type="text"
                  value={option.text}
                  onChange={(e) => updateOption(index, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder={`Option ${index + 1}`}
                  required={index < 2}
                />
                {options.length > 2 && (
                  <button
                    type="button"
                    onClick={() => removeOption(index)}
                    className="flex-shrink-0 p-1 text-red-600 hover:text-red-700"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
          
          {options.length < 10 && (
            <button
              type="button"
              onClick={addOption}
              className="mt-3 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Option
            </button>
          )}
        </div>

        {/* Actions */}
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
            disabled={isSubmitting}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
          >
            {isSubmitting ? 'Creating...' : 'Create Poll'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Poll Voting Interface Component
export interface PollVotingProps {
  poll: Poll;
  eventId: number;
  onVoteSubmitted?: () => void;
  disabled?: boolean;
}

export const PollVoting: React.FC<PollVotingProps> = ({
  poll,
  eventId,
  onVoteSubmitted,
  disabled = false
}) => {
  const [selectedOptions, setSelectedOptions] = useState<number[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle option selection
  const toggleOption = (optionId: number) => {
    if (disabled || hasVoted) return;

    if (poll.poll_type === 'single') {
      setSelectedOptions([optionId]);
    } else {
      setSelectedOptions(prev => 
        prev.includes(optionId) 
          ? prev.filter(id => id !== optionId)
          : [...prev, optionId]
      );
    }
  };

  // Submit vote
  const handleVote = async () => {
    if (selectedOptions.length === 0) {
      setError('Please select at least one option');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // Submit each selected option as a vote
      for (const optionId of selectedOptions) {
        await api.polls.vote(eventId, poll.id, { option_id: optionId });
      }

      setHasVoted(true);
      if (onVoteSubmitted) {
        onVoteSubmitted();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit vote');
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalVotes = poll.options?.reduce((sum, opt) => sum + (opt.vote_count || 0), 0) || 0;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        {poll.question_text}
      </h3>
      
      <div className="flex items-center justify-between mb-4">
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
          {poll.poll_type === 'single' ? 'Single choice' : 'Multiple choice'}
        </span>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="space-y-3 mb-6">
        {poll.options?.map((option) => {
          const percentage = totalVotes > 0 ? Math.round((option.vote_count / totalVotes) * 100) : 0;
          const isSelected = selectedOptions.includes(option.id);
          
          return (
            <div key={option.id} className="relative">
              <button
                onClick={() => toggleOption(option.id)}
                disabled={disabled || hasVoted || isSubmitting || poll.status !== 'active'}
                className={`w-full text-left p-3 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-50'
                    : hasVoted || poll.status !== 'active'
                    ? 'border-gray-200 bg-gray-50'
                    : 'border-gray-200 hover:border-indigo-300 hover:bg-indigo-50'
                } ${
                  disabled || hasVoted || poll.status !== 'active' ? 'cursor-not-allowed' : 'cursor-pointer'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className={`${isSelected ? 'text-indigo-900' : 'text-gray-900'}`}>
                    {option.option_text}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">{option.vote_count || 0} votes</span>
                    <span className="text-sm font-medium text-gray-900">{percentage}%</span>
                  </div>
                </div>
                
                {/* Vote percentage bar */}
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      isSelected ? 'bg-indigo-600' : 'bg-gray-400'
                    }`}
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </button>
            </div>
          );
        })}
      </div>

      {/* Vote Actions */}
      {poll.status === 'active' && !hasVoted && (
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-600">
            {poll.poll_type === 'single' 
              ? 'Select one option and submit your vote'
              : 'Select one or more options and submit your vote'
            }
          </p>
          <button
            onClick={handleVote}
            disabled={selectedOptions.length === 0 || isSubmitting}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Vote'}
          </button>
        </div>
      )}

      {hasVoted && (
        <div className="p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          ✓ Your vote has been submitted successfully!
        </div>
      )}

      {poll.status === 'closed' && (
        <div className="p-3 bg-gray-100 border border-gray-300 text-gray-700 rounded">
          This poll is now closed. Results are shown above.
        </div>
      )}

      {/* Results Summary */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between text-sm text-gray-500">
          <span>Total votes: {totalVotes}</span>
          <span>Poll ID: {poll.id}</span>
        </div>
      </div>
    </div>
  );
};

// Poll Results Display Component
export interface PollResultsProps {
  poll: Poll;
  showDetails?: boolean;
}

export const PollResults: React.FC<PollResultsProps> = ({
  poll,
  showDetails = true
}) => {
  const totalVotes = poll.options?.reduce((sum, opt) => sum + (opt.vote_count || 0), 0) || 0;
  
  // Sort options by vote count for results display
  const sortedOptions = poll.options ? [...poll.options].sort((a, b) => b.vote_count - a.vote_count) : [];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          {poll.question_text}
        </h3>
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
      </div>

      {showDetails && (
        <div className="mb-4 flex items-center space-x-4 text-sm text-gray-500">
          <span>{poll.poll_type === 'single' ? 'Single choice' : 'Multiple choice'}</span>
          <span>•</span>
          <span>{totalVotes} total votes</span>
          <span>•</span>
          <span>Created {new Date(poll.created_at).toLocaleString()}</span>
        </div>
      )}

      <div className="space-y-4">
        {sortedOptions.map((option, index) => {
          const percentage = totalVotes > 0 ? Math.round((option.vote_count / totalVotes) * 100) : 0;
          const isWinner = index === 0 && option.vote_count > 0;
          
          return (
            <div key={option.id} className="relative">
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center">
                  <span className={`text-sm font-medium ${isWinner ? 'text-indigo-900' : 'text-gray-900'}`}>
                    {option.option_text}
                  </span>
                  {isWinner && totalVotes > 0 && (
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                      Winner
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">{option.vote_count} votes</span>
                  <span className={`text-sm font-bold ${isWinner ? 'text-indigo-600' : 'text-gray-900'}`}>
                    {percentage}%
                  </span>
                </div>
              </div>
              
              {/* Results bar */}
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${
                    isWinner ? 'bg-indigo-600' : 'bg-gray-400'
                  }`}
                  style={{ width: `${percentage}%` }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>

      {totalVotes === 0 && (
        <div className="text-center py-6 text-gray-500">
          <p>No votes yet</p>
        </div>
      )}
    </div>
  );
};