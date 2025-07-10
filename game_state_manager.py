#!/usr/bin/env python3
"""
Utility script for managing the shared game state across multiple applications.
This can be used by both the chat system and the Twitter bot.
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add the rival_agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rival_agent.shared_game_state import get_shared_game_state


def show_status():
    """Show current game status"""
    game_state = get_shared_game_state()
    
    print("🎮 Shared Game State Status")
    print("=" * 40)
    
    state = game_state.get_game_state()
    stats = game_state.get_stats()
    
    print(f"Game Blocked: {state.get('game_blocked', False)}")
    print(f"Blocked By: {state.get('blocked_by', 'N/A')}")
    print(f"Last Updated: {state.get('last_updated', 'N/A')}")
    print(f"State Version: {stats.get('version', 'N/A')}")
    
    if state.get('winner'):
        winner = state['winner']
        print(f"\n👑 Winner Information:")
        print(f"  Detected At: {winner.get('detected_at', 'N/A')}")
        print(f"  Blocked By: {winner.get('blocked_by', 'N/A')}")
        print(f"  Wallet Address: {winner.get('wallet_address', 'Not provided')}")
        print(f"  Prize Sent: {winner.get('prize_sent', False)}")
        if winner.get('prize_sent'):
            print(f"  Prize Amount: {winner.get('prize_amount', 'N/A')} wei")
            print(f"  Prize TX Hash: {winner.get('prize_tx_hash', 'N/A')}")
    
    print(f"\n📊 Statistics:")
    print(f"  State File: {stats.get('state_file', 'N/A')}")
    print(f"  Winner Has Wallet: {stats.get('winner_has_wallet', False)}")


def reset_game():
    """Reset the game state"""
    game_state = get_shared_game_state()
    
    print("🔄 Resetting game state...")
    success = game_state.reset_game()
    
    if success:
        print("✅ Game state reset successfully!")
    else:
        print("❌ Failed to reset game state")


def set_wallet(wallet_address: str):
    """Set winner wallet address"""
    game_state = get_shared_game_state()
    
    print(f"💳 Setting wallet address: {wallet_address}")
    success = game_state.set_winner_wallet(wallet_address)
    
    if success:
        print("✅ Wallet address set successfully!")
    else:
        print("❌ Failed to set wallet address")


def test_uomi_detection():
    """Test the uomi detection and blocking functionality"""
    game_state = get_shared_game_state()
    
    print("🧪 Testing uomi detection...")
    
    # Test blocking
    test_response = "I think the answer is uomi!"
    blocked = game_state.block_game(test_response, "test")
    
    if blocked:
        print("✅ Game blocked successfully!")
        print(f"Test response: {test_response}")
    else:
        print("⚠️  Game was already blocked")
    
    # Show status after test
    show_status()


def show_logs():
    """Show recent game event logs"""
    log_file = "shared_game_events.log"
    
    print("📋 Recent Game Events")
    print("=" * 30)
    
    if not os.path.exists(log_file):
        print("No log file found")
        return
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Show last 10 events
        for line in lines[-10:]:
            try:
                event = json.loads(line.strip())
                timestamp = event.get('timestamp', 'N/A')
                event_type = event.get('event_type', 'N/A')
                details = event.get('details', {})
                
                print(f"{timestamp} - {event_type}")
                if event_type == "GAME_BLOCKED":
                    print(f"  Blocked by: {details.get('blocked_by', 'N/A')}")
                    print(f"  Response: {details.get('response', 'N/A')[:50]}...")
                elif event_type == "WALLET_PROVIDED":
                    print(f"  Wallet: {details.get('wallet_address', 'N/A')}")
                elif event_type == "PRIZE_SENT":
                    print(f"  Recipient: {details.get('recipient', 'N/A')}")
                    print(f"  Amount: {details.get('amount', 'N/A')} wei")
                    print(f"  TX Hash: {details.get('tx_hash', 'N/A')}")
                print()
            except json.JSONDecodeError:
                continue
                
    except Exception as e:
        print(f"Error reading log file: {e}")


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python game_state_manager.py <command> [args]")
        print("Commands:")
        print("  status       - Show current game status")
        print("  reset        - Reset game state")
        print("  set-wallet <address>  - Set winner wallet address")
        print("  test         - Test uomi detection")
        print("  logs         - Show recent logs")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "reset":
        reset_game()
    elif command == "set-wallet":
        if len(sys.argv) < 3:
            print("Usage: python game_state_manager.py set-wallet <wallet_address>")
            return
        set_wallet(sys.argv[2])
    elif command == "test":
        test_uomi_detection()
    elif command == "logs":
        show_logs()
    else:
        print(f"Unknown command: {command}")
        print("Use 'python game_state_manager.py' to see available commands")


if __name__ == "__main__":
    main()
