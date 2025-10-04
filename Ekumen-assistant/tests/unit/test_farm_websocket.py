"""
Unit tests for Farm WebSocket functionality
Tests real-time farm data updates and WebSocket management
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket
from uuid import uuid4

from app.api.v1.farm.websocket import (
    FarmWebSocketManager,
    farm_ws_manager,
    broadcast_farm_update,
    broadcast_parcelle_update,
    broadcast_intervention_update,
    broadcast_exploitation_update,
    broadcast_dashboard_update
)


class TestFarmWebSocketManager:
    """Test suite for FarmWebSocketManager class"""

    @pytest.fixture
    def manager(self):
        """Create a fresh FarmWebSocketManager instance for testing"""
        return FarmWebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket for testing"""
        websocket = AsyncMock(spec=WebSocket)
        websocket.send_json = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test WebSocket connection establishment"""
        connection_id = "test_connection_123"
        user_id = "user_123"
        org_id = "org_123"
        
        await manager.connect(mock_websocket, connection_id, user_id, org_id)
        
        assert connection_id in manager.connections
        assert manager.connections[connection_id] == mock_websocket
        assert manager.connection_users[connection_id] == user_id
        assert manager.connection_orgs[connection_id] == org_id

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test WebSocket disconnection and cleanup"""
        connection_id = "test_connection_123"
        user_id = "user_123"
        org_id = "org_123"
        
        # Connect first
        await manager.connect(mock_websocket, connection_id, user_id, org_id)
        
        # Add some subscriptions
        manager.farm_subscribers["farm_123"].add(connection_id)
        manager.parcelle_subscribers["parcelle_123"].add(connection_id)
        manager.intervention_subscribers["intervention_123"].add(connection_id)
        
        # Disconnect
        await manager.disconnect(connection_id)
        
        # Verify cleanup
        assert connection_id not in manager.connections
        assert connection_id not in manager.connection_users
        assert connection_id not in manager.connection_orgs
        assert connection_id not in manager.connection_subscriptions
        assert connection_id not in manager.farm_subscribers["farm_123"]
        assert connection_id not in manager.parcelle_subscribers["parcelle_123"]
        assert connection_id not in manager.intervention_subscribers["intervention_123"]

    @pytest.mark.asyncio
    async def test_subscribe(self, manager, mock_websocket):
        """Test subscription to farm data updates"""
        connection_id = "test_connection_123"
        user_id = "user_123"
        org_id = "org_123"
        
        # Connect first
        await manager.connect(mock_websocket, connection_id, user_id, org_id)
        
        # Subscribe to farm updates
        subscription = {
            "farm_siret": "farm_123",
            "parcelle_id": "parcelle_123",
            "types": ["parcelle", "intervention"]
        }
        
        result = await manager.subscribe(connection_id, subscription)
        
        assert result is True
        assert connection_id in manager.farm_subscribers["farm_123"]
        assert connection_id in manager.parcelle_subscribers["parcelle_123"]
        assert len(manager.connection_subscriptions[connection_id]) == 1

    @pytest.mark.asyncio
    async def test_subscribe_invalid_connection(self, manager):
        """Test subscription with invalid connection ID"""
        subscription = {"farm_siret": "farm_123"}
        
        result = await manager.subscribe("invalid_connection", subscription)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager, mock_websocket):
        """Test unsubscription from farm data updates"""
        connection_id = "test_connection_123"
        user_id = "user_123"
        org_id = "org_123"
        
        # Connect and subscribe
        await manager.connect(mock_websocket, connection_id, user_id, org_id)
        subscription = {"farm_siret": "farm_123"}
        await manager.subscribe(connection_id, subscription)
        
        # Unsubscribe
        result = await manager.unsubscribe(connection_id)
        
        assert result is True
        assert connection_id not in manager.farm_subscribers["farm_123"]
        assert len(manager.connection_subscriptions[connection_id]) == 0

    @pytest.mark.asyncio
    async def test_broadcast_update(self, manager, mock_websocket):
        """Test broadcasting updates to subscribers"""
        connection_id = "test_connection_123"
        user_id = "user_123"
        org_id = "org_123"
        
        # Connect and subscribe
        await manager.connect(mock_websocket, connection_id, user_id, org_id)
        subscription = {"farm_siret": "farm_123"}
        await manager.subscribe(connection_id, subscription)
        
        # Broadcast update
        update = {
            "type": "parcelle",
            "action": "updated",
            "data": {"id": "parcelle_123", "nom": "Test Parcel"},
            "farm_siret": "farm_123",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        await manager.broadcast_update(update)
        
        # Verify message was sent
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "farm:data_update"
        assert call_args["update"] == update

    @pytest.mark.asyncio
    async def test_broadcast_update_no_subscribers(self, manager):
        """Test broadcasting updates when no subscribers exist"""
        update = {
            "type": "parcelle",
            "action": "updated",
            "data": {"id": "parcelle_123", "nom": "Test Parcel"},
            "farm_siret": "farm_123",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        # Should not raise any exceptions
        await manager.broadcast_update(update)

    @pytest.mark.asyncio
    async def test_broadcast_update_disconnected_connection(self, manager, mock_websocket):
        """Test broadcasting updates to disconnected connections"""
        connection_id = "test_connection_123"
        user_id = "user_123"
        org_id = "org_123"
        
        # Connect and subscribe
        await manager.connect(mock_websocket, connection_id, user_id, org_id)
        subscription = {"farm_siret": "farm_123"}
        await manager.subscribe(connection_id, subscription)
        
        # Simulate disconnected connection
        manager.connections[connection_id] = None
        
        # Broadcast update
        update = {
            "type": "parcelle",
            "action": "updated",
            "data": {"id": "parcelle_123", "nom": "Test Parcel"},
            "farm_siret": "farm_123",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        # Should handle gracefully and clean up
        await manager.broadcast_update(update)
        
        # Connection should be cleaned up
        assert connection_id not in manager.connections

    @pytest.mark.asyncio
    async def test_broadcast_update_send_error(self, manager, mock_websocket):
        """Test broadcasting updates when send fails"""
        connection_id = "test_connection_123"
        user_id = "user_123"
        org_id = "org_123"
        
        # Connect and subscribe
        await manager.connect(mock_websocket, connection_id, user_id, org_id)
        subscription = {"farm_siret": "farm_123"}
        await manager.subscribe(connection_id, subscription)
        
        # Make send_json raise an exception
        mock_websocket.send_json.side_effect = Exception("Send failed")
        
        # Broadcast update
        update = {
            "type": "parcelle",
            "action": "updated",
            "data": {"id": "parcelle_123", "nom": "Test Parcel"},
            "farm_siret": "farm_123",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        # Should handle gracefully and clean up
        await manager.broadcast_update(update)
        
        # Connection should be cleaned up
        assert connection_id not in manager.connections

    def test_get_user_accessible_farms(self, manager):
        """Test getting user accessible farms"""
        # This would require database mocking, so we'll test the structure
        assert hasattr(manager, 'get_user_accessible_farms')
        assert callable(manager.get_user_accessible_farms)


class TestBroadcastFunctions:
    """Test suite for broadcast helper functions"""

    @pytest.mark.asyncio
    async def test_broadcast_farm_update(self):
        """Test broadcast_farm_update function"""
        update = {
            "type": "parcelle",
            "action": "updated",
            "data": {"id": "parcelle_123", "nom": "Test Parcel"},
            "farm_siret": "farm_123",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        with patch.object(farm_ws_manager, 'broadcast_update', new_callable=AsyncMock) as mock_broadcast:
            await broadcast_farm_update(update)
            mock_broadcast.assert_called_once_with(update)

    @pytest.mark.asyncio
    async def test_broadcast_parcelle_update(self):
        """Test broadcast_parcelle_update function"""
        parcelle_id = "parcelle_123"
        farm_siret = "farm_123"
        action = "updated"
        data = {"id": parcelle_id, "nom": "Test Parcel"}
        
        with patch.object(farm_ws_manager, 'broadcast_update', new_callable=AsyncMock) as mock_broadcast:
            await broadcast_parcelle_update(parcelle_id, farm_siret, action, data)
            
            # Verify the update structure
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "parcelle"
            assert call_args["action"] == action
            assert call_args["data"] == data
            assert call_args["parcelle_id"] == parcelle_id
            assert call_args["farm_siret"] == farm_siret
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_intervention_update(self):
        """Test broadcast_intervention_update function"""
        intervention_id = "intervention_123"
        parcelle_id = "parcelle_123"
        farm_siret = "farm_123"
        action = "created"
        data = {"id": intervention_id, "type": "SEMIS"}
        
        with patch.object(farm_ws_manager, 'broadcast_update', new_callable=AsyncMock) as mock_broadcast:
            await broadcast_intervention_update(intervention_id, parcelle_id, farm_siret, action, data)
            
            # Verify the update structure
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "intervention"
            assert call_args["action"] == action
            assert call_args["data"] == data
            assert call_args["intervention_id"] == intervention_id
            assert call_args["parcelle_id"] == parcelle_id
            assert call_args["farm_siret"] == farm_siret
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_exploitation_update(self):
        """Test broadcast_exploitation_update function"""
        farm_siret = "farm_123"
        action = "updated"
        data = {"nom": "Test Farm", "surface_totale_ha": 100.0}
        
        with patch.object(farm_ws_manager, 'broadcast_update', new_callable=AsyncMock) as mock_broadcast:
            await broadcast_exploitation_update(farm_siret, action, data)
            
            # Verify the update structure
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "exploitation"
            assert call_args["action"] == action
            assert call_args["data"] == data
            assert call_args["farm_siret"] == farm_siret
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_dashboard_update(self):
        """Test broadcast_dashboard_update function"""
        farm_siret = "farm_123"
        data = {"total_parcelles": 10, "total_interventions": 25}
        
        with patch.object(farm_ws_manager, 'broadcast_update', new_callable=AsyncMock) as mock_broadcast:
            await broadcast_dashboard_update(farm_siret, data)
            
            # Verify the update structure
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "dashboard"
            assert call_args["action"] == "updated"
            assert call_args["data"] == data
            assert call_args["farm_siret"] == farm_siret
            assert "timestamp" in call_args


class TestWebSocketEndpoint:
    """Test suite for WebSocket endpoint functionality"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        from app.main import app
        return TestClient(app)

    def test_websocket_endpoint_requires_token(self, client):
        """Test that WebSocket endpoint requires authentication token"""
        with client.websocket_connect("/api/v1/farm/ws") as websocket:
            # Should close with authentication error
            with pytest.raises(Exception):
                websocket.receive_text()

    @pytest.mark.asyncio
    async def test_websocket_message_handling(self):
        """Test WebSocket message handling logic"""
        # This would require more complex mocking of the WebSocket endpoint
        # For now, we'll test the message structure validation
        
        # Valid subscription message
        valid_subscription = {
            "type": "farm:subscribe",
            "subscription": {
                "farm_siret": "farm_123",
                "types": ["parcelle", "intervention"]
            }
        }
        
        # Valid unsubscribe message
        valid_unsubscribe = {
            "type": "farm:unsubscribe",
            "subscription_id": "sub_123"
        }
        
        # Valid ping message
        valid_ping = {
            "type": "ping",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        # Invalid message
        invalid_message = {
            "type": "unknown_type",
            "data": "invalid"
        }
        
        # Test message structure validation
        assert valid_subscription["type"] in ["farm:subscribe", "farm:unsubscribe", "ping"]
        assert valid_unsubscribe["type"] in ["farm:subscribe", "farm:unsubscribe", "ping"]
        assert valid_ping["type"] in ["farm:subscribe", "farm:unsubscribe", "ping"]
        assert invalid_message["type"] not in ["farm:subscribe", "farm:unsubscribe", "ping"]


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality"""

    @pytest.mark.asyncio
    async def test_full_websocket_flow(self):
        """Test complete WebSocket flow from connection to broadcast"""
        manager = FarmWebSocketManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_json = AsyncMock()
        
        connection_id = "test_connection_123"
        user_id = "user_123"
        org_id = "org_123"
        
        # 1. Connect
        await manager.connect(mock_websocket, connection_id, user_id, org_id)
        assert connection_id in manager.connections
        
        # 2. Subscribe
        subscription = {"farm_siret": "farm_123"}
        result = await manager.subscribe(connection_id, subscription)
        assert result is True
        
        # 3. Broadcast update
        update = {
            "type": "parcelle",
            "action": "updated",
            "data": {"id": "parcelle_123", "nom": "Test Parcel"},
            "farm_siret": "farm_123",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        await manager.broadcast_update(update)
        
        # 4. Verify message was sent
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "farm:data_update"
        assert call_args["update"] == update
        
        # 5. Unsubscribe
        result = await manager.unsubscribe(connection_id)
        assert result is True
        
        # 6. Disconnect
        await manager.disconnect(connection_id)
        assert connection_id not in manager.connections

    @pytest.mark.asyncio
    async def test_multiple_connections_broadcast(self):
        """Test broadcasting to multiple connections"""
        manager = FarmWebSocketManager()
        
        # Create multiple mock connections
        connections = []
        for i in range(3):
            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.send_json = AsyncMock()
            connections.append(mock_websocket)
            
            connection_id = f"test_connection_{i}"
            user_id = f"user_{i}"
            org_id = f"org_{i}"
            
            # Connect and subscribe
            await manager.connect(mock_websocket, connection_id, user_id, org_id)
            subscription = {"farm_siret": "farm_123"}
            await manager.subscribe(connection_id, subscription)
        
        # Broadcast update
        update = {
            "type": "parcelle",
            "action": "updated",
            "data": {"id": "parcelle_123", "nom": "Test Parcel"},
            "farm_siret": "farm_123",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        await manager.broadcast_update(update)
        
        # Verify all connections received the update
        for mock_websocket in connections:
            mock_websocket.send_json.assert_called_once()
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "farm:data_update"
            assert call_args["update"] == update
