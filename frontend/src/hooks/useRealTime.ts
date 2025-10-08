/**
 * Real-time State Management Hooks
 * 
 * React hooks for managing real-time data updates through WebSocket connections.
 * Provides reactive state management for events, polls, and questions.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { WebSocketService, WebSocketMessage, createWebSocketService } from '../services/websocket';
import { api, Poll, Question, Event } from '../services/api';

// Real-time state interfaces
export interface UseEventStateResult {
  event: Event | null;
  isLoading: boolean;
  error: string | null;
  connected: boolean;
  refreshEvent: () => void;
}

export interface UsePollsStateResult {
  polls: Poll[];
  isLoading: boolean;
  error: string | null;
  connected: boolean;
  refreshPolls: () => void;
}

export interface UseQuestionsStateResult {
  questions: Question[];
  isLoading: boolean;
  error: string | null;
  connected: boolean;
  refreshQuestions: () => void;
}

export interface UseRealTimeConnectionResult {
  connected: boolean;
  reconnecting: boolean;
  error: string | null;
  connect: (eventSlug: string) => void;
  disconnect: () => void;
}

/**
 * Hook for managing real-time WebSocket connection
 */
export function useRealTimeConnection(): UseRealTimeConnectionResult {
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocketService | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback((eventSlug: string) => {
    // Cleanup existing connection
    if (wsRef.current) {
      wsRef.current.disconnect();
    }

    try {
      setError(null);
      setReconnecting(true);
      
      const ws = createWebSocketService(eventSlug);
      wsRef.current = ws;

      // Handle connection state changes
      ws.onConnectionChange((isConnected) => {
        setConnected(isConnected);
        setReconnecting(false);
        
        if (isConnected) {
          setError(null);
        } else if (ws.connected === false) {
          // Connection lost, show reconnecting
          setReconnecting(true);
        }
      });

      // Handle WebSocket errors
      ws.on('error', (message) => {
        setError(message.data?.error || 'Connection error');
        setReconnecting(false);
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
      setReconnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
    }
    setConnected(false);
    setReconnecting(false);
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    connected,
    reconnecting,
    error,
    connect,
    disconnect
  };
}

/**
 * Hook for managing real-time event state
 */
export function useEventState(eventSlug: string): UseEventStateResult {
  const [event, setEvent] = useState<Event | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { connected, connect } = useRealTimeConnection();

  // Load initial event data
  const loadEvent = useCallback(async () => {
    if (!eventSlug) return;
    
    try {
      setIsLoading(true);
      setError(null);
      const eventData = await api.events.get(eventSlug);
      setEvent(eventData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load event';
      setError(errorMessage);
      console.error('Failed to load event:', err);
    } finally {
      setIsLoading(false);
    }
  }, [eventSlug]);

  // Connect to WebSocket and load initial data
  useEffect(() => {
    if (eventSlug && eventSlug.trim()) {
      console.log('[useEventState] Connecting with eventSlug:', eventSlug);
      loadEvent();
      connect(eventSlug);
    } else if (!eventSlug || !eventSlug.trim()) {
      console.log('[useEventState] Skipping connection, invalid eventSlug:', eventSlug);
    }
  }, [eventSlug, loadEvent, connect]);

  const refreshEvent = useCallback(() => {
    loadEvent();
  }, [loadEvent]);

  return {
    event,
    isLoading,
    error,
    connected,
    refreshEvent
  };
}

/**
 * Hook for managing real-time polls state
 */
export function usePollsState(eventSlug: string): UsePollsStateResult {
  const [polls, setPolls] = useState<Poll[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { connected, connect } = useRealTimeConnection();
  const wsRef = useRef<WebSocketService | null>(null);

  // Load initial polls data
  const loadPolls = useCallback(async () => {
    if (!eventSlug) return;
    
    try {
      setIsLoading(true);
      setError(null);
      const pollsData = await api.polls.getByEvent(eventSlug);
      setPolls(pollsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load polls';
      setError(errorMessage);
      console.error('Failed to load polls:', err);
    } finally {
      setIsLoading(false);
    }
  }, [eventSlug]);

  // Handle real-time poll updates
  useEffect(() => {
    if (!connected || !eventSlug) return;

    const ws = createWebSocketService(eventSlug);
    wsRef.current = ws;

    // Handle poll creation
    const unsubscribeCreated = ws.on('poll_created', (message: any) => {
      // Backend sends: { type: "poll_created", poll: {...}, timestamp: ... }
      const pollData = message.poll || message.data?.poll;
      if (pollData) {
        setPolls((currentPolls: Poll[]) => [...currentPolls, pollData]);
      }
    });

    // Handle poll updates
    const unsubscribeUpdated = ws.on('poll_updated', (message: any) => {
      // Backend sends: { type: "poll_updated", poll: {...}, timestamp: ... }
      const pollData = message.poll || message.data?.poll;
      if (pollData) {
        setPolls((currentPolls: Poll[]) =>
          currentPolls.map((poll: Poll) =>
            poll.id === pollData.id ? pollData : poll
          )
        );
      }
    });

    // Handle vote updates
    const unsubscribeVotes = ws.on('vote_updated', (message: any) => {
      // Backend sends: { type: "vote_updated", poll_id: X, results: {...}, timestamp: ... }
      const pollId = message.poll_id || message.data?.poll_id;
      const results = message.results || message.data?.results;
      
      if (pollId !== undefined && results) {
        setPolls((currentPolls: Poll[]) =>
          currentPolls.map((poll: Poll) => {
            if (poll.id === pollId) {
              return {
                ...poll,
                options: poll.options.map((option: any) => ({
                  ...option,
                  vote_count: results[option.id] || 0
                }))
              };
            }
            return poll;
          })
        );
      }
    });

    return () => {
      unsubscribeCreated();
      unsubscribeUpdated();
      unsubscribeVotes();
      ws.disconnect();
    };
  }, [connected, eventSlug]);

  // Connect and load initial data
  useEffect(() => {
    if (eventSlug && eventSlug.trim()) {
      console.log('[usePollsState] Connecting with eventSlug:', eventSlug);
      loadPolls();
      connect(eventSlug);
    } else if (!eventSlug || !eventSlug.trim()) {
      console.log('[usePollsState] Skipping connection, invalid eventSlug:', eventSlug);
    }
  }, [eventSlug, loadPolls, connect]);

  const refreshPolls = useCallback(() => {
    loadPolls();
  }, [loadPolls]);

  return {
    polls,
    isLoading,
    error,
    connected,
    refreshPolls
  };
}

/**
 * Hook for managing real-time questions state
 */
export function useQuestionsState(eventSlug: string): UseQuestionsStateResult {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { connected, connect } = useRealTimeConnection();
  const wsRef = useRef<WebSocketService | null>(null);

  // Load initial questions data
  const loadQuestions = useCallback(async () => {
    if (!eventSlug) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      // Check if we're in a host context (has host code) or attendee context
      const hostCode = localStorage.getItem('hostCode');
      
      let questionsData: Question[];
      if (hostCode) {
        // Host view: get all questions (requires auth)
        questionsData = await api.questions.getByEvent(eventSlug);
      } else {
        // Attendee view: get all questions (public, no filtering needed)
        questionsData = await api.questions.getPublicBySlug(eventSlug);
      }
      
      setQuestions(questionsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load questions';
      setError(errorMessage);
      console.error('Failed to load questions:', err);
    } finally {
      setIsLoading(false);
    }
  }, [eventSlug]);

  // Handle real-time question updates
  useEffect(() => {
    if (!connected || !eventSlug) return;

    const ws = createWebSocketService(eventSlug);
    wsRef.current = ws;

    // Handle question submission (creation or moderation)
    const unsubscribeSubmitted = ws.on('question_submitted', (message: any) => {
      // Backend sends: { type: "question_submitted", question: {...}, timestamp: ... }
      const questionData = message.question || message.data?.question;
      if (questionData) {
        console.log('[useQuestionsState] Received question_submitted:', questionData);
        setQuestions((currentQuestions: Question[]) => {
          const existingIndex = currentQuestions.findIndex(q => q.id === questionData.id);
          if (existingIndex >= 0) {
            // Update existing question
            const updated = [...currentQuestions];
            updated[existingIndex] = questionData;
            return updated;
          } else {
            // Add new question
            return [...currentQuestions, questionData];
          }
        });
      }
    });

    // Handle question upvotes
    const unsubscribeUpvoted = ws.on('question_upvoted', (message: any) => {
      // Backend sends: { type: "question_upvoted", question_id: X, upvote_count: Y, timestamp: ... }
      const questionId = message.question_id || message.data?.question_id;
      const upvoteCount = message.upvote_count ?? message.data?.upvote_count;
      
      if (questionId !== undefined && upvoteCount !== undefined) {
        console.log('[useQuestionsState] Received question_upvoted:', { questionId, upvoteCount });
        setQuestions((currentQuestions: Question[]) =>
          currentQuestions.map((question: Question) =>
            question.id === questionId 
              ? { ...question, upvote_count: upvoteCount }
              : question
          )
        );
      }
    });

    return () => {
      unsubscribeSubmitted();
      unsubscribeUpvoted();
      ws.disconnect();
    };
  }, [connected, eventSlug]);

  // Connect and load initial data
  useEffect(() => {
    if (eventSlug && eventSlug.trim()) {
      console.log('[useQuestionsState] Connecting with eventSlug:', eventSlug);
      loadQuestions();
      connect(eventSlug);
    } else if (!eventSlug || !eventSlug.trim()) {
      console.log('[useQuestionsState] Skipping connection, invalid eventSlug:', eventSlug);
    }
  }, [eventSlug, loadQuestions, connect]);

  const refreshQuestions = useCallback(() => {
    loadQuestions();
  }, [loadQuestions]);

  return {
    questions,
    isLoading,
    error,
    connected,
    refreshQuestions
  };
}

/**
 * Hook for optimistic updates with real-time sync
 */
export function useOptimisticState<T>(
  initialState: T,
  key: string
): [T, (newState: T) => void, (realState: T) => void] {
  const [optimisticState, setOptimisticState] = useState<T>(initialState);
  const [realState, setRealState] = useState<T>(initialState);
  const pendingUpdatesRef = useRef<Set<string>>(new Set());

  // Apply optimistic update
  const applyOptimisticUpdate = useCallback((newState: T) => {
    const updateId = `${key}-${Date.now()}`;
    pendingUpdatesRef.current.add(updateId);
    setOptimisticState(newState);

    // Clear optimistic update after timeout (fallback)
    setTimeout(() => {
      pendingUpdatesRef.current.delete(updateId);
    }, 10000);
  }, [key]);

  // Apply real update from server
  const applyRealUpdate = useCallback((newState: T) => {
    setRealState(newState);
    
    // If no pending optimistic updates, use real state
    if (pendingUpdatesRef.current.size === 0) {
      setOptimisticState(newState);
    }
  }, []);

  // Use real state when no optimistic updates pending
  useEffect(() => {
    if (pendingUpdatesRef.current.size === 0) {
      setOptimisticState(realState);
    }
  }, [realState]);

  return [optimisticState, applyOptimisticUpdate, applyRealUpdate];
}

/**
 * Hook for debounced real-time updates
 */
export function useDebouncedRealTime<T>(
  value: T,
  delay: number = 500
): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}