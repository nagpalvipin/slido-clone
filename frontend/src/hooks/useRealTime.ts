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
    if (eventSlug) {
      loadEvent();
      connect(eventSlug);
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
    const unsubscribeCreated = ws.on('poll_created', (message: WebSocketMessage) => {
      if (message.data?.poll) {
        setPolls((currentPolls: Poll[]) => [...currentPolls, message.data.poll]);
      }
    });

    // Handle poll updates
    const unsubscribeUpdated = ws.on('poll_updated', (message: WebSocketMessage) => {
      if (message.data?.poll) {
        setPolls((currentPolls: Poll[]) =>
          currentPolls.map((poll: Poll) =>
            poll.id === message.data.poll.id ? message.data.poll : poll
          )
        );
      }
    });

    // Handle vote updates
    const unsubscribeVotes = ws.on('vote_updated', (message: WebSocketMessage) => {
      if (message.data?.poll_id && message.data?.results) {
        setPolls((currentPolls: Poll[]) =>
          currentPolls.map((poll: Poll) => {
            if (poll.id === message.data.poll_id) {
              return {
                ...poll,
                options: poll.options.map((option: any) => ({
                  ...option,
                  vote_count: message.data.results[option.id] || 0
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
    if (eventSlug) {
      loadPolls();
      connect(eventSlug);
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
      const questionsData = await api.questions.getByEvent(eventSlug);
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

    // Handle question creation
    const unsubscribeCreated = ws.on('question_created', (message: WebSocketMessage) => {
      if (message.data?.question) {
        setQuestions((currentQuestions: Question[]) => [...currentQuestions, message.data.question]);
      }
    });

    // Handle question updates (moderation, votes)
    const unsubscribeUpdated = ws.on('question_updated', (message: WebSocketMessage) => {
      if (message.data?.question) {
        setQuestions((currentQuestions: Question[]) =>
          currentQuestions.map((question: Question) =>
            question.id === message.data.question.id ? message.data.question : question
          )
        );
      }
    });

    return () => {
      unsubscribeCreated();
      unsubscribeUpdated();
      ws.disconnect();
    };
  }, [connected, eventSlug]);

  // Connect and load initial data
  useEffect(() => {
    if (eventSlug) {
      loadQuestions();
      connect(eventSlug);
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