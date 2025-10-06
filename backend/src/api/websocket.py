"""
WebSocket API for real-time updates.

Handles real-time poll results and question updates with <100ms requirement.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Set
import json
import asyncio
import logging

from src.core.database import get_db
from src.services.event_service import EventService

router = APIRouter(tags=["websocket"])

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Dictionary mapping event_id to set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, event_id: int):
        """Connect a client to an event room."""
        await websocket.accept()
        
        if event_id not in self.active_connections:
            self.active_connections[event_id] = set()
        
        self.active_connections[event_id].add(websocket)
        logger.info(f"Client connected to event {event_id}. Total: {len(self.active_connections[event_id])}")
    
    def disconnect(self, websocket: WebSocket, event_id: int):
        """Disconnect a client from an event room."""
        if event_id in self.active_connections:
            self.active_connections[event_id].discard(websocket)
            
            # Clean up empty event rooms
            if not self.active_connections[event_id]:
                del self.active_connections[event_id]
            
            logger.info(f"Client disconnected from event {event_id}")
    
    async def broadcast_to_event(self, event_id: int, message: dict):
        """Broadcast message to all clients in an event room."""
        if event_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected_clients = []
        
        # Broadcast to all connected clients
        for websocket in self.active_connections[event_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected_clients.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            self.active_connections[event_id].discard(websocket)
    
    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Send message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/events/{event_slug}")
async def websocket_endpoint(websocket: WebSocket, event_slug: str):
    """WebSocket endpoint for real-time event updates."""
    event_id = None
    
    try:
        # Get database session
        db = next(get_db())
        
        # Verify event exists
        event_service = EventService(db)
        event = event_service.get_event_by_slug(event_slug)
        
        if not event:
            await websocket.close(code=4004, reason="Event not found")
            return
        
        event_id = event.id
        
        # Connect client
        await manager.connect(websocket, event_id)
        
        # Send connection confirmation
        await manager.send_to_client(websocket, {
            "type": "connected",
            "event_id": event_id,
            "message": "Connected to event successfully"
        })
        
        # Listen for client messages
        while True:
            try:
                # Wait for message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "join":
                    # Client joining event room
                    await manager.send_to_client(websocket, {
                        "type": "joined",
                        "event_id": event_id,
                        "status": "success"
                    })
                
                elif message.get("type") == "ping":
                    # Keepalive ping
                    await manager.send_to_client(websocket, {
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    })
                
                else:
                    # Unknown message type
                    await manager.send_to_client(websocket, {
                        "type": "error",
                        "message": f"Unknown message type: {message.get('type')}"
                    })
                    
            except json.JSONDecodeError:
                await manager.send_to_client(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        if event_id:
            manager.disconnect(websocket, event_id)


# Helper functions for broadcasting events (to be called by API endpoints)
async def broadcast_poll_created(event_id: int, poll_data: dict):
    """Broadcast poll created event to all clients."""
    message = {
        "type": "poll_created",
        "poll": poll_data,
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.broadcast_to_event(event_id, message)


async def broadcast_poll_status_updated(event_id: int, poll_id: int, status: str):
    """Broadcast poll status update to all clients."""
    message = {
        "type": "poll_status_updated", 
        "poll_id": poll_id,
        "status": status,
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.broadcast_to_event(event_id, message)


async def broadcast_vote_updated(event_id: int, poll_id: int, results: dict):
    """Broadcast vote update to all clients."""
    message = {
        "type": "vote_updated",
        "poll_id": poll_id,
        "results": results,
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.broadcast_to_event(event_id, message)


async def broadcast_question_submitted(event_id: int, question_data: dict):
    """Broadcast question submission to all clients."""
    message = {
        "type": "question_submitted",
        "question": question_data,
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.broadcast_to_event(event_id, message)


async def broadcast_question_upvoted(event_id: int, question_id: int, upvote_count: int):
    """Broadcast question upvote to all clients."""
    message = {
        "type": "question_upvoted",
        "question_id": question_id,
        "upvote_count": upvote_count,
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.broadcast_to_event(event_id, message)


# Export the manager for use by other modules
__all__ = ["manager", "broadcast_poll_created", "broadcast_poll_status_updated", 
           "broadcast_vote_updated", "broadcast_question_submitted", "broadcast_question_upvoted"]