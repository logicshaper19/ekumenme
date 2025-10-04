"""
WebSocket endpoints for farm data real-time updates
Handles real-time WebSocket communication for farm data changes
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from app.services.shared import AuthService
from app.models.organization import OrganizationFarmAccess, OrganizationMembership
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, and_
import logging
import json
import asyncio
from typing import Dict, Set, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()

# Connection management
class FarmWebSocketManager:
    def __init__(self):
        # Map of connection_id -> WebSocket
        self.connections: Dict[str, WebSocket] = {}
        # Map of connection_id -> user_id
        self.connection_users: Dict[str, str] = {}
        # Map of connection_id -> organization_id
        self.connection_orgs: Dict[str, str] = {}
        # Map of connection_id -> subscriptions
        self.connection_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        # Map of farm_siret -> set of connection_ids
        self.farm_subscribers: Dict[str, Set[str]] = defaultdict(set)
        # Map of parcelle_id -> set of connection_ids
        self.parcelle_subscribers: Dict[str, Set[str]] = defaultdict(set)
        # Map of intervention_id -> set of connection_ids
        self.intervention_subscribers: Dict[str, Set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str, org_id: str):
        """Add a new WebSocket connection"""
        self.connections[connection_id] = websocket
        self.connection_users[connection_id] = user_id
        self.connection_orgs[connection_id] = org_id
        logger.info(f"Farm WebSocket connection {connection_id} established for user {user_id}")

    async def disconnect(self, connection_id: str):
        """Remove a WebSocket connection and clean up subscriptions"""
        if connection_id in self.connections:
            # Remove from all subscription maps
            for farm_siret, subscribers in self.farm_subscribers.items():
                subscribers.discard(connection_id)
            for parcelle_id, subscribers in self.parcelle_subscribers.items():
                subscribers.discard(connection_id)
            for intervention_id, subscribers in self.intervention_subscribers.items():
                subscribers.discard(connection_id)
            
            # Clean up connection data
            self.connections.pop(connection_id, None)
            self.connection_users.pop(connection_id, None)
            self.connection_orgs.pop(connection_id, None)
            self.connection_subscriptions.pop(connection_id, None)
            
            logger.info(f"Farm WebSocket connection {connection_id} disconnected")

    async def subscribe(self, connection_id: str, subscription: Dict[str, Any]):
        """Subscribe a connection to farm data updates"""
        if connection_id not in self.connections:
            return False

        # Store subscription
        subscription_key = json.dumps(subscription, sort_keys=True)
        self.connection_subscriptions[connection_id].add(subscription_key)

        # Add to relevant subscriber maps
        if 'farm_siret' in subscription:
            self.farm_subscribers[subscription['farm_siret']].add(connection_id)
        
        if 'parcelle_id' in subscription:
            self.parcelle_subscribers[subscription['parcelle_id']].add(connection_id)
        
        if 'intervention_id' in subscription:
            self.intervention_subscribers[subscription['intervention_id']].add(connection_id)

        logger.info(f"Connection {connection_id} subscribed to: {subscription}")
        return True

    async def unsubscribe(self, connection_id: str, subscription_id: str = None):
        """Unsubscribe a connection from farm data updates"""
        if connection_id not in self.connections:
            return False

        if subscription_id:
            # Remove specific subscription
            self.connection_subscriptions[connection_id].discard(subscription_id)
        else:
            # Remove all subscriptions for this connection
            self.connection_subscriptions[connection_id].clear()

        # Remove from subscriber maps
        for farm_siret, subscribers in self.farm_subscribers.items():
            subscribers.discard(connection_id)
        for parcelle_id, subscribers in self.parcelle_subscribers.items():
            subscribers.discard(connection_id)
        for intervention_id, subscribers in self.intervention_subscribers.items():
            subscribers.discard(connection_id)

        logger.info(f"Connection {connection_id} unsubscribed")
        return True

    async def broadcast_update(self, update: Dict[str, Any]):
        """Broadcast a farm data update to relevant subscribers"""
        update_type = update.get('type')
        farm_siret = update.get('farm_siret')
        parcelle_id = update.get('parcelle_id')
        intervention_id = update.get('intervention_id')

        # Determine which connections should receive this update
        target_connections = set()

        # Add farm subscribers
        if farm_siret and farm_siret in self.farm_subscribers:
            target_connections.update(self.farm_subscribers[farm_siret])

        # Add parcelle subscribers
        if parcelle_id and parcelle_id in self.parcelle_subscribers:
            target_connections.update(self.parcelle_subscribers[parcelle_id])

        # Add intervention subscribers
        if intervention_id and intervention_id in self.intervention_subscribers:
            target_connections.update(self.intervention_subscribers[intervention_id])

        # Send update to all target connections
        if target_connections:
            message = {
                "type": "farm:data_update",
                "update": update
            }
            
            disconnected_connections = []
            for connection_id in target_connections:
                if connection_id in self.connections:
                    try:
                        await self.connections[connection_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Failed to send update to connection {connection_id}: {e}")
                        disconnected_connections.append(connection_id)
                else:
                    disconnected_connections.append(connection_id)

            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                await self.disconnect(connection_id)

        logger.info(f"Broadcasted farm update to {len(target_connections)} connections")

    async def get_user_accessible_farms(self, user_id: str, org_id: str) -> Set[str]:
        """Get all farm SIRETs accessible to a user"""
        async with AsyncSessionLocal() as db:
            query = select(OrganizationFarmAccess.farm_siret).where(
                OrganizationFarmAccess.organization_id.in_(
                    select(OrganizationMembership.organization_id)
                    .where(OrganizationMembership.user_id == user_id)
                )
            )
            result = await db.execute(query)
            return set(result.scalars().all())

# Global WebSocket manager instance
farm_ws_manager = FarmWebSocketManager()

@router.websocket("/ws")
async def farm_websocket(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for farm data real-time updates
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token
    """
    connection_id = None

    try:
        # Verify token and get user
        user = await auth_service.verify_websocket_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Extract org_id from token
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        
        if not org_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Organization not selected")
            return

        # Accept the WebSocket connection
        await websocket.accept()
        connection_id = f"farm_{user.id}_{org_id}_{int(asyncio.get_event_loop().time())}"
        
        # Register connection
        await farm_ws_manager.connect(websocket, connection_id, str(user.id), org_id)
        
        # Get user's accessible farms
        accessible_farms = await farm_ws_manager.get_user_accessible_farms(str(user.id), org_id)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "connection_id": connection_id,
            "accessible_farms": list(accessible_farms),
            "message": "Connected to farm data updates"
        })

        logger.info(f"Farm WebSocket connection {connection_id} established for user {user.id}")

        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                message_type = message_data.get("type")

                if message_type == "farm:subscribe":
                    # Handle subscription request
                    subscription = message_data.get("subscription", {})
                    await farm_ws_manager.subscribe(connection_id, subscription)
                    
                    await websocket.send_json({
                        "type": "farm:subscription_confirmed",
                        "subscription": subscription
                    })

                elif message_type == "farm:unsubscribe":
                    # Handle unsubscription request
                    subscription_id = message_data.get("subscription_id")
                    await farm_ws_manager.unsubscribe(connection_id, subscription_id)
                    
                    await websocket.send_json({
                        "type": "farm:unsubscription_confirmed",
                        "subscription_id": subscription_id
                    })

                elif message_type == "ping":
                    # Handle ping/pong for connection health
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": message_data.get("timestamp")
                    })

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        logger.info(f"Farm WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Farm WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        if connection_id:
            await farm_ws_manager.disconnect(connection_id)

# Function to broadcast farm data updates (called from other parts of the application)
async def broadcast_farm_update(update: Dict[str, Any]):
    """
    Broadcast a farm data update to all relevant WebSocket subscribers
    
    Args:
        update: Dictionary containing update information
                Expected keys: type, action, data, farm_siret, parcelle_id, intervention_id
    """
    await farm_ws_manager.broadcast_update(update)

# Example usage functions for different types of updates
async def broadcast_parcelle_update(parcelle_id: str, farm_siret: str, action: str, data: Dict[str, Any]):
    """Broadcast a parcelle update"""
    update = {
        "type": "parcelle",
        "action": action,
        "data": data,
        "parcelle_id": parcelle_id,
        "farm_siret": farm_siret,
        "timestamp": asyncio.get_event_loop().time()
    }
    await broadcast_farm_update(update)

async def broadcast_intervention_update(intervention_id: str, parcelle_id: str, farm_siret: str, action: str, data: Dict[str, Any]):
    """Broadcast an intervention update"""
    update = {
        "type": "intervention",
        "action": action,
        "data": data,
        "intervention_id": intervention_id,
        "parcelle_id": parcelle_id,
        "farm_siret": farm_siret,
        "timestamp": asyncio.get_event_loop().time()
    }
    await broadcast_farm_update(update)

async def broadcast_exploitation_update(farm_siret: str, action: str, data: Dict[str, Any]):
    """Broadcast an exploitation update"""
    update = {
        "type": "exploitation",
        "action": action,
        "data": data,
        "farm_siret": farm_siret,
        "timestamp": asyncio.get_event_loop().time()
    }
    await broadcast_farm_update(update)

async def broadcast_dashboard_update(farm_siret: str, data: Dict[str, Any]):
    """Broadcast a dashboard update"""
    update = {
        "type": "dashboard",
        "action": "updated",
        "data": data,
        "farm_siret": farm_siret,
        "timestamp": asyncio.get_event_loop().time()
    }
    await broadcast_farm_update(update)
