#!/usr/bin/env python3
"""
Test script for the streaming voice assistant
Tests the WebSocket endpoints and voice processing functionality
"""

import asyncio
import websockets
import json
import base64
import os
from pathlib import Path

async def test_voice_websocket():
    """Test the voice WebSocket endpoint"""
    
    # Test connection
    uri = "ws://localhost:8000/api/v1/voice/ws/voice?token=test_token"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to voice WebSocket")
            
            # Test connection message
            connection_msg = await websocket.recv()
            print(f"📨 Connection message: {connection_msg}")
            
            # Test ping
            ping_msg = {
                "type": "ping",
                "timestamp": 1234567890
            }
            await websocket.send(json.dumps(ping_msg))
            print("📤 Sent ping message")
            
            # Wait for pong
            pong_msg = await websocket.recv()
            print(f"📨 Pong message: {pong_msg}")
            
            # Test start voice input
            start_msg = {
                "type": "start_voice_input",
                "timestamp": 1234567890
            }
            await websocket.send(json.dumps(start_msg))
            print("📤 Sent start voice input message")
            
            # Wait for response
            response = await websocket.recv()
            print(f"📨 Start response: {response}")
            
            print("✅ Voice WebSocket test completed successfully")
            
    except Exception as e:
        print(f"❌ Voice WebSocket test failed: {e}")

async def test_voice_journal_websocket():
    """Test the voice journal WebSocket endpoint"""
    
    uri = "ws://localhost:8000/api/v1/voice/ws/voice/journal?token=test_token"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to voice journal WebSocket")
            
            # Test connection message
            connection_msg = await websocket.recv()
            print(f"📨 Connection message: {connection_msg}")
            
            print("✅ Voice journal WebSocket test completed successfully")
            
    except Exception as e:
        print(f"❌ Voice journal WebSocket test failed: {e}")

async def test_voice_service():
    """Test the voice service functionality"""
    try:
        from app.services.infrastructure.voice_service import VoiceService
        
        voice_service = VoiceService()
        print("✅ Voice service initialized")
        
        # Test transcription with mock audio
        mock_audio = b"mock audio data"
        result = await voice_service.transcribe_audio_bytes(mock_audio)
        print(f"✅ Transcription test: {result.text}")
        
        # Test TTS
        tts_result = await voice_service.synthesize_speech("Test de synthèse vocale")
        print(f"✅ TTS test: {len(tts_result)} bytes generated")
        
    except Exception as e:
        print(f"❌ Voice service test failed: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting voice assistant tests...\n")
    
    print("1. Testing Voice Service...")
    await test_voice_service()
    print()
    
    print("2. Testing Voice WebSocket...")
    await test_voice_websocket()
    print()
    
    print("3. Testing Voice Journal WebSocket...")
    await test_voice_journal_websocket()
    print()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
