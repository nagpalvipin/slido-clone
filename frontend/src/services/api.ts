/**
 * API Client Service for Slido Clone
 * 
 * Handles all HTTP requests to the backend API with proper error handling,
 * authentication, and TypeScript types.
 */

// Base API URL - will be configured via environment variable
// API Configuration
const API_BASE_URL = (typeof window !== 'undefined' && (window as any).VITE_API_URL) || 'http://localhost:8001/api/v1';

// Types for API requests and responses
export interface Event {
  id: number;
  title: string;
  slug: string;
  description?: string;
  created_at: string;
  is_active: boolean;
}

export interface EventCreateResponse extends Event {
  short_code: string;
  host_code: string;
  attendee_count: number;
}

export interface EventHostView extends EventCreateResponse {
  polls: Poll[];
  questions: Question[];
}

export interface Poll {
  id: number;
  question_text: string;
  poll_type: 'single' | 'multiple';
  status: 'draft' | 'active' | 'closed';
  created_at: string;
  options: PollOption[];
}

export interface PollOption {
  id: number;
  option_text: string;
  position: number;
  vote_count: number;
}

export interface Question {
  id: number;
  question_text: string;
  status: 'pending' | 'approved' | 'rejected';
  upvote_count: number;
  created_at: string;
}

export interface VoteResponse {
  vote_recorded: boolean;
  poll_id: number;
  option_id: number;
}

export interface CreateEventRequest {
  title: string;
  slug: string;
  description?: string;
}

export interface CreatePollRequest {
  question_text: string;
  poll_type: 'single' | 'multiple';
  options: Array<{
    option_text: string;
    position: number;
  }>;
}

export interface CreateQuestionRequest {
  question_text: string;
}

export interface UpdatePollStatusRequest {
  status: 'draft' | 'active' | 'closed';
}

export interface VoteRequest {
  option_id: number;
}

// Error types
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

/**
 * Main API client class
 */
export class ApiClient {
  private baseUrl: string;
  private hostCode?: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Set host authentication code
  setHostCode(hostCode: string) {
    this.hostCode = hostCode;
  }

  // Get current host code
  getHostCode(): string | undefined {
    return this.hostCode;
  }

  /**
   * Clear authentication
   */
  clearAuth(): void {
    this.hostCode = undefined;
  }

  /**
   * Generic GET request helper
   */
  async get<T = any>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'GET' });
  }

  // Generic request method with error handling
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Add host authentication if available
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.hostCode) {
      headers['Authorization'] = `Host ${this.hostCode}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Parse response
      let data: any;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      // Handle HTTP errors
      if (!response.ok) {
        throw new ApiError(
          data?.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          data
        );
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      // Network or other errors
      throw new NetworkError(
        error instanceof Error ? error.message : 'Network request failed'
      );
    }
  }

  // Event API methods
  async createEvent(eventData: CreateEventRequest): Promise<EventCreateResponse> {
    return this.request<EventCreateResponse>('/events/', {
      method: 'POST',
      body: JSON.stringify(eventData),
    });
  }

  async getEvent(slug: string): Promise<Event> {
    return this.request<Event>(`/events/${slug}`);
  }

  async getHostView(slug: string, hostCode: string): Promise<EventHostView> {
    return this.request<EventHostView>(`/events/${slug}/host`, {
      headers: { Authorization: `Host ${hostCode}` }
    });
  }

  // Poll API methods
  async createPoll(eventId: number, pollData: CreatePollRequest): Promise<Poll> {
    return this.request<Poll>(`/events/${eventId}/polls`, {
      method: 'POST',
      body: JSON.stringify(pollData),
    });
  }

  async updatePollStatus(
    eventId: number, 
    pollId: number, 
    statusData: UpdatePollStatusRequest
  ): Promise<Poll> {
    return this.request<Poll>(`/events/${eventId}/polls/${pollId}/status`, {
      method: 'PUT',
      body: JSON.stringify(statusData),
    });
  }

  async voteOnPoll(
    eventId: number, 
    pollId: number, 
    voteData: VoteRequest
  ): Promise<VoteResponse> {
    return this.request<VoteResponse>(`/events/${eventId}/polls/${pollId}/vote`, {
      method: 'POST',
      body: JSON.stringify(voteData),
    });
  }

  // Question API methods (to be implemented when backend is ready)
  async createQuestion(eventId: number, questionData: CreateQuestionRequest): Promise<Question> {
    return this.request<Question>(`/events/${eventId}/questions`, {
      method: 'POST',
      body: JSON.stringify(questionData),
    });
  }

  async upvoteQuestion(eventId: number, questionId: number): Promise<void> {
    return this.request<void>(`/events/${eventId}/questions/${questionId}/upvote`, {
      method: 'POST',
    });
  }

  async moderateQuestion(
    eventId: number, 
    questionId: number, 
    status: 'approved' | 'rejected'
  ): Promise<Question> {
    return this.request<Question>(`/events/${eventId}/questions/${questionId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }
}

// Default API client instance
export const apiClient = new ApiClient();

// Utility functions for common operations
export const api = {
  events: {
    create: (data: CreateEventRequest) => apiClient.createEvent(data),
    get: (slug: string) => apiClient.getEvent(slug),
    getHostView: (slug: string, hostCode: string) => apiClient.getHostView(slug, hostCode),
  },
  polls: {
    create: (eventId: number, data: CreatePollRequest) => apiClient.createPoll(eventId, data),
    updateStatus: (eventId: number, pollId: number, status: UpdatePollStatusRequest) => 
      apiClient.updatePollStatus(eventId, pollId, status),
    vote: (eventId: number, pollId: number, vote: VoteRequest) => 
      apiClient.voteOnPoll(eventId, pollId, vote),
    getByEvent: async (eventSlug: string): Promise<Poll[]> => {
      // Get polls from host view (includes polls data)
      const hostView = await apiClient.getHostView(eventSlug, apiClient.getHostCode() || 'default');
      return hostView.polls;
    },
  },
  questions: {
    create: (eventId: number, data: CreateQuestionRequest) => apiClient.createQuestion(eventId, data),
    upvote: (eventId: number, questionId: number) => apiClient.upvoteQuestion(eventId, questionId),
    moderate: (eventId: number, questionId: number, status: 'approved' | 'rejected') => 
      apiClient.moderateQuestion(eventId, questionId, status),
    getByEvent: async (eventSlug: string): Promise<Question[]> => {
      // Get questions from host view (includes questions data)
      try {
        const hostView = await apiClient.getHostView(eventSlug, apiClient.getHostCode() || 'default');
        return hostView.questions;
      } catch (error) {
        // Fallback: try to get event first to get ID, then get questions
        const event = await apiClient.getEvent(eventSlug);
        return await apiClient.get<Question[]>(`/api/v1/events/${event.id}/questions`);
      }
    },
  },
  auth: {
    setHostCode: (hostCode: string) => apiClient.setHostCode(hostCode),
    clearAuth: () => apiClient.clearAuth(),
  }
};