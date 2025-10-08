/**
 * WebSocket Service for Real-time Communication
 * 
 * Handles WebSocket connections with automatic reconnection,
 * event routing, and connection state management.
 */

export type WebSocketEventType = 
  | 'connected' 
  | 'poll_created' 
  | 'poll_updated' 
  | 'vote_updated' 
  | 'question_created' 
  | 'question_updated'
  | 'question_submitted'
  | 'question_upvoted'
  | 'error';

export interface WebSocketMessage {
  type: WebSocketEventType;
  data?: any;
  event_id?: number;
  poll_id?: number;
  question_id?: number;
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export type WebSocketEventHandler = (message: WebSocketMessage) => void;
export type ConnectionStateHandler = (connected: boolean) => void;

/**
 * WebSocket service with automatic reconnection and event handling
 */
export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private eventHandlers: Map<WebSocketEventType, Set<WebSocketEventHandler>> = new Map();
  private connectionHandlers: Set<ConnectionStateHandler> = new Set();
  private reconnectAttempts = 0;
  private reconnectTimeout: number | null = null;
  private heartbeatTimeout: number | null = null;
  private isConnected = false;
  private shouldReconnect = true;
  private eventSlug: string | null = null;

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...config
    };
  }

  /**
   * Connect to WebSocket for specific event
   */
  connect(eventSlug: string): void {
    this.eventSlug = eventSlug;
    this.shouldReconnect = true;
    this.createConnection();
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.cleanup();
  }

  /**
   * Check if WebSocket is connected
   */
  get connected(): boolean {
    return this.isConnected;
  }

  /**
   * Subscribe to WebSocket events
   */
  on(eventType: WebSocketEventType, handler: WebSocketEventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionChange(handler: ConnectionStateHandler): () => void {
    this.connectionHandlers.add(handler);

    // Return unsubscribe function
    return () => {
      this.connectionHandlers.delete(handler);
    };
  }

  /**
   * Send message to WebSocket
   */
  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }

  /**
   * Create WebSocket connection
   */
  private createConnection(): void {
    if (!this.eventSlug) {
      console.error('Cannot connect: no event slug provided');
      return;
    }

    try {
      this.cleanup();
      
      const wsUrl = `${this.config.url}/events/${this.eventSlug}`;
      console.log('Connecting to WebSocket:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.notifyConnectionState(true);
      this.startHeartbeat();

      // Send join message
      this.send({
        type: 'join',
        event_slug: this.eventSlug
      });
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.isConnected = false;
      this.notifyConnectionState(false);
      this.stopHeartbeat();

      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emitEvent({
        type: 'error',
        data: { error: 'WebSocket connection error' }
      });
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    console.log('WebSocket message received:', message);
    this.emitEvent(message);
  }

  /**
   * Emit event to registered handlers
   */
  private emitEvent(message: WebSocketMessage): void {
    const handlers = this.eventHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in WebSocket event handler:', error);
        }
      });
    }
  }

  /**
   * Notify connection state handlers
   */
  private notifyConnectionState(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('Error in connection state handler:', error);
      }
    });
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (!this.shouldReconnect || this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached or reconnection disabled');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectInterval * Math.min(this.reconnectAttempts, 5); // Exponential backoff with cap

    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);

    this.reconnectTimeout = window.setTimeout(() => {
      this.createConnection();
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimeout = window.setInterval(() => {
      this.send({ type: 'ping' });
    }, this.config.heartbeatInterval);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimeout) {
      window.clearInterval(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  /**
   * Clean up WebSocket connection and timers
   */
  private cleanup(): void {
    this.stopHeartbeat();

    if (this.reconnectTimeout) {
      window.clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close();
      }
      
      this.ws = null;
    }

    this.isConnected = false;
  }
}

// WebSocket service factory
export function createWebSocketService(eventSlug: string): WebSocketService {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = window.location.hostname;
  
  // For development, use localhost:8001
  const wsUrl = `${wsProtocol}//${wsHost}:8001/ws`;

  const service = new WebSocketService({ url: wsUrl });
  service.connect(eventSlug);
  return service;
}

// Default WebSocket service instance
let defaultWebSocketService: WebSocketService | null = null;

export const websocket = {
  /**
   * Connect to event WebSocket
   */
  connect: (eventSlug: string): WebSocketService => {
    if (defaultWebSocketService) {
      defaultWebSocketService.disconnect();
    }
    
    defaultWebSocketService = createWebSocketService(eventSlug);
    return defaultWebSocketService;
  },

  /**
   * Get current WebSocket service
   */
  current: (): WebSocketService | null => defaultWebSocketService,

  /**
   * Disconnect current WebSocket
   */
  disconnect: (): void => {
    if (defaultWebSocketService) {
      defaultWebSocketService.disconnect();
      defaultWebSocketService = null;
    }
  }
};