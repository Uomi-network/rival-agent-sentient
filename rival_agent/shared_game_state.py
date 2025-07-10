"""
Shared game state manager for multi-modal uomi detection.
This module provides a centralized way to manage game state across
different applications (chat, Twitter bot, etc.).
"""

import json
import os
import time
import fcntl
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager


class SharedGameState:
    """
    Thread-safe shared game state manager that uses file-based persistence
    with file locking to coordinate between multiple processes.
    Compatible with both Python and Node.js applications.
    """
    
    def __init__(self, state_file: str = "shared_game_state.json", legacy_winners_file: str = "winners.txt"):
        self.state_file = state_file
        self.legacy_winners_file = legacy_winners_file
        self.lock = threading.Lock()
        self._ensure_state_file_exists()
        # Check for legacy winners file on init
        self._migrate_legacy_winners()
    
    def _ensure_state_file_exists(self):
        """Ensure the state file exists with default values"""
        if not os.path.exists(self.state_file):
            default_state = {
                "game_blocked": False,
                "winner": None,
                "last_updated": datetime.now().isoformat(),
                "blocked_by": None,  # "chat", "twitter", etc.
                "version": 1,
                "cross_platform": True  # Flag to indicate this is cross-platform compatible
            }
            with open(self.state_file, 'w') as f:
                json.dump(default_state, f, indent=2)
    
    def _migrate_legacy_winners(self):
        """Migrate from legacy winners.txt file if it exists"""
        if os.path.exists(self.legacy_winners_file):
            try:
                with open(self.legacy_winners_file, 'r') as f:
                    content = f.read().strip()
                
                if content:
                    lines = content.split('\n')
                    if len(lines) > 0:
                        # Parse the first line: commentId,userId,timestamp
                        first_line = lines[0].split(',')
                        if len(first_line) >= 3:
                            comment_id = first_line[0]
                            user_id = first_line[2]
                            
                            # Check if game is not already blocked
                            if not self.is_game_blocked():
                                # Block the game with legacy data
                                self.block_game(
                                    response=f"Legacy winner from Twitter (Comment ID: {comment_id})",
                                    blocked_by="twitter",
                                    comment_id=comment_id,
                                    user_id=user_id
                                )
                            
                            # Check if prize was already sent (second line exists)
                            if len(lines) > 1:
                                second_line = lines[1].split(',')
                                if len(second_line) >= 2:
                                    wallet_address = second_line[1]
                                    self.set_winner_wallet(wallet_address)
                                    self.mark_prize_sent(tx_hash="legacy_twitter", amount=0)
                
                # Backup the legacy file
                os.rename(self.legacy_winners_file, f"{self.legacy_winners_file}.backup")
                
            except Exception as e:
                # Don't let migration errors break the system
                pass
    
    @contextmanager
    def _file_lock(self, file_handle):
        """Context manager for file locking"""
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
    
    def _read_state(self) -> Dict[str, Any]:
        """Read current state from file with locking"""
        try:
            with open(self.state_file, 'r') as f:
                with self._file_lock(f):
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file is corrupted or missing, reset to default
            self._ensure_state_file_exists()
            return self._read_state()
    
    def _write_state(self, state: Dict[str, Any]):
        """Write state to file with locking"""
        state["last_updated"] = datetime.now().isoformat()
        state["version"] = state.get("version", 1) + 1
        
        with open(self.state_file, 'w') as f:
            with self._file_lock(f):
                json.dump(state, f, indent=2)
    
    def is_game_blocked(self) -> bool:
        """Check if the game is currently blocked"""
        with self.lock:
            state = self._read_state()
            return state.get("game_blocked", False)
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get complete game state"""
        with self.lock:
            return self._read_state()
    
    def block_game(self, response: str, blocked_by: str = "unknown", comment_id: str = None, user_id: str = None) -> bool:
        """
        Block the game when 'uomi' is detected
        
        Args:
            response: The response that contained 'uomi'
            blocked_by: Which system blocked the game ('chat', 'twitter', etc.)
            comment_id: Twitter comment ID (for Twitter wins)
            user_id: Twitter user ID (for Twitter wins)
        
        Returns:
            bool: True if game was blocked, False if already blocked
        """
        with self.lock:
            state = self._read_state()
            
            # If already blocked, don't block again
            if state.get("game_blocked", False):
                return False
            
            # Block the game
            state["game_blocked"] = True
            state["blocked_by"] = blocked_by
            state["winner"] = {
                "detected_at": datetime.now().isoformat(),
                "winning_response": response,
                "wallet_address": None,
                "prize_sent": False,
                "blocked_by": blocked_by
            }
            
            # Add Twitter-specific fields if provided
            if comment_id:
                state["winner"]["comment_id"] = comment_id
            if user_id:
                state["winner"]["user_id"] = user_id
            
            self._write_state(state)
            self._log_event("GAME_BLOCKED", {
                "reason": "uomi_detected",
                "response": response,
                "blocked_by": blocked_by,
                "comment_id": comment_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Create legacy winners.txt file for Node.js compatibility
            if blocked_by == "twitter" and comment_id and user_id:
                self._create_legacy_winners_file(comment_id, user_id)
            
            return True
    
    def set_winner_wallet(self, wallet_address: str) -> bool:
        """Set the winner's wallet address"""
        with self.lock:
            state = self._read_state()
            
            if not state.get("game_blocked", False) or not state.get("winner"):
                return False
            
            # Validate wallet address format
            import re
            if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
                return False
            
            state["winner"]["wallet_address"] = wallet_address
            self._write_state(state)
            
            self._log_event("WALLET_PROVIDED", {
                "wallet_address": wallet_address,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update legacy winners.txt file
            self._update_legacy_winners_file(wallet_address)
            
            return True
    
    def mark_prize_sent(self, tx_hash: str = None, amount: int = None) -> bool:
        """Mark that the prize has been sent"""
        with self.lock:
            state = self._read_state()
            
            if not state.get("game_blocked", False) or not state.get("winner"):
                return False
            
            state["winner"]["prize_sent"] = True
            state["winner"]["prize_tx_hash"] = tx_hash
            state["winner"]["prize_amount"] = amount
            state["winner"]["prize_sent_at"] = datetime.now().isoformat()
            
            self._write_state(state)
            
            # Update legacy winners.txt file if wallet address is available
            wallet_address = state["winner"].get("wallet_address")
            if wallet_address:
                self._update_legacy_winners_file(wallet_address)
            
            self._log_event("PRIZE_SENT", {
                "recipient": state["winner"]["wallet_address"],
                "amount": amount,
                "tx_hash": tx_hash,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
    
    def reset_game(self) -> bool:
        """Reset the game state (for testing or new game)"""
        with self.lock:
            state = {
                "game_blocked": False,
                "winner": None,
                "last_updated": datetime.now().isoformat(),
                "blocked_by": None,
                "version": 1
            }
            
            self._write_state(state)
            
            self._log_event("GAME_RESET", {
                "timestamp": datetime.now().isoformat()
            })
            
            return True
    
    def get_blocked_message(self) -> str:
        """Get the message to return when game is blocked"""
        return ("The game has been stopped because a winning condition was met. "
                "Please provide your wallet address to receive your prize.")
    
    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log events to a separate log file"""
        log_file = "shared_game_events.log"
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details
        }
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # Don't let logging errors break the main functionality
            pass
    
    def get_winner_info(self) -> Optional[Dict[str, Any]]:
        """Get winner information if game is blocked"""
        with self.lock:
            state = self._read_state()
            return state.get("winner")
    
    def is_prize_sent(self) -> bool:
        """Check if prize has been sent"""
        winner = self.get_winner_info()
        return winner and winner.get("prize_sent", False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the game state"""
        with self.lock:
            state = self._read_state()
            return {
                "game_blocked": state.get("game_blocked", False),
                "blocked_by": state.get("blocked_by"),
                "last_updated": state.get("last_updated"),
                "version": state.get("version", 1),
                "winner_has_wallet": bool(state.get("winner", {}).get("wallet_address")),
                "prize_sent": bool(state.get("winner", {}).get("prize_sent", False)),
                "state_file": self.state_file
            }
    
    def _create_legacy_winners_file(self, comment_id: str, user_id: str):
        """Create legacy winners.txt file for Node.js compatibility"""
        try:
            timestamp = datetime.now().isoformat()
            with open(self.legacy_winners_file, 'w') as f:
                f.write(f"{comment_id},{timestamp},{user_id}\n")
        except Exception as e:
            # Don't let legacy file creation errors break the system
            pass
    
    def _update_legacy_winners_file(self, wallet_address: str):
        """Update legacy winners.txt file when prize is sent"""
        try:
            if os.path.exists(self.legacy_winners_file):
                with open(self.legacy_winners_file, 'r') as f:
                    content = f.read().strip()
                
                if content and len(content.split('\n')) == 1:
                    # Only one line exists, append the wallet info
                    with open(self.legacy_winners_file, 'a') as f:
                        f.write(f"\n{content.split(',')[0]},{wallet_address}")
        except Exception as e:
            # Don't let legacy file update errors break the system
            pass


# Global shared instance
_shared_game_state = None

def get_shared_game_state(state_file: str = "shared_game_state.json") -> SharedGameState:
    """Get or create the global shared game state instance"""
    global _shared_game_state
    if _shared_game_state is None:
        _shared_game_state = SharedGameState(state_file)
    return _shared_game_state
