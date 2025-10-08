/**
 * EventSwitcher Component
 * 
 * Dropdown component for hosts to switch between their events.
 * Shows list of events with question counts and supports pagination.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, Event } from '../services/api';

export interface EventSwitcherProps {
  currentEventId?: number;
  hostCode: string;
  className?: string;
}

export const EventSwitcher: React.FC<EventSwitcherProps> = ({
  currentEventId,
  hostCode,
  className = ''
}) => {
  const navigate = useNavigate();
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  
  const LIMIT = 20;

  // Fetch events on mount
  useEffect(() => {
    loadEvents();
  }, [hostCode]);

  const loadEvents = async () => {
    if (!hostCode) return;

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await api.events.getByHost(hostCode, { limit: LIMIT, offset: 0 });
      setEvents(response.events);
      setHasMore(response.total > response.events.length);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load events';
      setError(errorMsg);
      console.error('Failed to load events:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMoreEvents = async () => {
    if (!hostCode || isLoading) return;

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await api.events.getByHost(hostCode, {
        limit: LIMIT,
        offset: events.length
      });
      
      setEvents([...events, ...response.events]);
      setHasMore(response.total > events.length + response.events.length);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load more events';
      setError(errorMsg);
      console.error('Failed to load more events:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEventSelect = (event: Event) => {
    setIsOpen(false);
    navigate(`/host/dashboard/${event.host_code}`);
  };

  const currentEvent = events.find(e => e.id === currentEventId);

  return (
    <div className={`relative inline-block text-left ${className}`}>
      {/* Dropdown Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex justify-between items-center w-full rounded-lg border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <span className="flex items-center">
          <span className="mr-2">📋</span>
          <span className="truncate max-w-xs">
            {currentEvent ? currentEvent.title : 'Select Event'}
          </span>
        </span>
        <svg
          className={`ml-2 h-5 w-5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="origin-top-left absolute left-0 mt-2 w-96 rounded-lg shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
          <div className="py-1 max-h-96 overflow-y-auto">
            {/* Header */}
            <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
              <h3 className="text-sm font-semibold text-gray-700">Your Events</h3>
              <p className="text-xs text-gray-500 mt-1">
                {events.length} {events.length === 1 ? 'event' : 'events'} loaded
              </p>
            </div>

            {/* Loading State */}
            {isLoading && events.length === 0 && (
              <div className="px-4 py-6 text-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto mb-2"></div>
                <p className="text-sm text-gray-500">Loading events...</p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="px-4 py-3 bg-red-50 border-l-4 border-red-400">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Empty State */}
            {!isLoading && events.length === 0 && !error && (
              <div className="px-4 py-6 text-center">
                <p className="text-sm text-gray-500">No events found</p>
              </div>
            )}

            {/* Events List */}
            {events.map((event) => (
              <button
                key={event.id}
                onClick={() => handleEventSelect(event)}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0 ${
                  event.id === currentEventId ? 'bg-indigo-50' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${
                      event.id === currentEventId ? 'text-indigo-700' : 'text-gray-900'
                    }`}>
                      {event.title}
                    </p>
                    <p className="text-xs text-gray-500 truncate mt-1">
                      {event.slug}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      Created {new Date(event.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {event.question_count || 0} Q
                    </span>
                  </div>
                </div>
              </button>
            ))}

            {/* Load More Button */}
            {hasMore && (
              <div className="px-4 py-3 border-t border-gray-200">
                <button
                  onClick={loadMoreEvents}
                  disabled={isLoading}
                  className="w-full px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600 mr-2"></div>
                      Loading...
                    </span>
                  ) : (
                    'Load More Events'
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Overlay to close dropdown when clicking outside */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default EventSwitcher;
