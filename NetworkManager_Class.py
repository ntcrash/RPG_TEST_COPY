"""
Enhanced NetworkManager for Magitech RPG
Handles all client-server communication with improved synchronization
"""

import requests
import time
import threading
import json
from typing import Optional, Dict, List, Any


class NetworkManager:
    def __init__(self, server_url="http://localhost:8000", debug=True):
        self.server_url = server_url
        self.user_id = None
        self.username = None
        self.session_id = None
        self.character_id = None
        self.character_data = {}

        # Sync management
        self.last_update = 0
        self.last_sync = 0
        self.last_position = [0, 0]
        self.other_players = {}
        self.chat_messages = []
        self.connected = False
        self.sync_failures = 0

        # Combat state
        self.combat_session = None
        self.activities = []
        self.last_activity_id = None

        # Threading
        self.sync_thread = None
        self.sync_running = False
        self.sync_lock = threading.Lock()

        # Constants
        self.UPDATE_INTERVAL = 0.2
        self.SYNC_INTERVAL = 1.0
        self.POSITION_THRESHOLD = 5
        self.MAX_SYNC_FAILURES = 5

        self.debug = debug

    def log(self, message):
        """Debug logging"""
        if self.debug:
            print(f"[NET] {message}")

    def request(self, method: str, endpoint: str, data: Optional[Dict] = None, timeout: int = 10) -> tuple:
        """Make HTTP request with proper error handling"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            if self.user_id:
                headers['User-ID'] = str(self.user_id)

            url = f"{self.server_url}{endpoint}"
            self.log(f"{method} {url}")

            response = None
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return False, f"Unsupported HTTP method: {method}"

            if response.status_code in [200, 201, 204]:
                try:
                    if response.content:
                        result = response.json()
                        return True, result
                    else:
                        return True, {"status": "success"}
                except:
                    return True, {"status": "success"}
            else:
                try:
                    error_data = response.json()
                    return False, error_data.get('error', response.text)
                except:
                    return False, response.text

        except requests.exceptions.ConnectionError:
            return False, "Connection error - server may be offline"
        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except Exception as e:
            return False, f"Network error: {str(e)}"

    # Authentication methods
    def login(self, username: str, password: str) -> tuple:
        """Login user"""
        success, data = self.request('POST', '/api/login', {
            'username': username,
            'password': password
        })

        if success:
            self.user_id = data.get('user_id')
            self.username = data.get('username', username)
            self.connected = True
            self.sync_failures = 0
            self.log(f"Login successful - User ID: {self.user_id}")
            self.start_sync_thread()

        return success, data

    def register(self, username: str, password: str) -> tuple:
        """Register new user"""
        success, data = self.request('POST', '/api/register', {
            'username': username,
            'password': password
        })

        if success:
            self.user_id = data.get('user_id')
            self.username = data.get('username', username)
            self.connected = True
            self.sync_failures = 0
            self.log(f"Registration successful - User ID: {self.user_id}")
            self.start_sync_thread()

        return success, data

    def logout(self):
        """Logout and cleanup"""
        self.log("Logging out...")

        # Stop sync thread
        self.stop_sync_thread()

        # Leave current session
        if self.session_id:
            self.leave_session()

        # Clear state
        self.user_id = None
        self.username = None
        self.session_id = None
        self.character_id = None
        self.character_data = {}
        self.other_players = {}
        self.chat_messages = []
        self.connected = False
        self.sync_failures = 0
        self.combat_session = None
        self.activities = []

        self.log("Logout complete")

    # Character management
    def get_characters(self) -> List[Dict]:
        """Get user's characters"""
        if not self.user_id:
            return []

        success, data = self.request('GET', '/api/characters')
        if success:
            return data.get('characters', [])
        return []

    def save_character(self, character_data: Dict) -> tuple:
        """Save character data"""
        if not self.user_id:
            return False, "Not logged in"

        success, data = self.request('POST', '/api/characters', character_data)
        if success:
            self.character_data = character_data
        return success, data

    def load_character(self, character_id: str) -> tuple:
        """Load character data"""
        if not self.user_id:
            return False, "Not logged in"

        success, data = self.request('GET', f'/api/characters/{character_id}')
        if success:
            self.character_id = character_id
            self.character_data = data.get('character', {})
        return success, data

    def delete_character(self, character_id: str) -> tuple:
        """Delete character"""
        if not self.user_id:
            return False, "Not logged in"

        return self.request('DELETE', f'/api/characters/{character_id}')

    # Session management
    def get_sessions(self) -> List[Dict]:
        """Get available sessions"""
        success, data = self.request('GET', '/api/sessions')
        if success:
            return data.get('sessions', [])
        return []

    def create_session(self, name: str, max_players: int = 4) -> tuple:
        """Create new session"""
        if not self.user_id:
            return False, "Not logged in"

        success, data = self.request('POST', '/api/sessions', {
            'name': name,
            'max_players': max_players
        })

        if success:
            self.session_id = data.get('session_id')

        return success, data

    def join_session(self, session_id: str, character_id: str) -> tuple:
        """Join session with character"""
        if not self.user_id or not character_id:
            return False, "Missing user or character ID"

        # Load character data if not already loaded
        if self.character_id != character_id:
            char_success, char_data = self.load_character(character_id)
            if not char_success:
                return False, f"Failed to load character: {char_data}"

        success, data = self.request('POST', f'/api/sessions/{session_id}/join', {
            'character_id': character_id,
            'character_data': self.character_data
        })

        if success:
            self.session_id = session_id
            self.log(f"Joined session: {session_id}")

        return success, data

    def leave_session(self) -> tuple:
        """Leave current session"""
        if not self.session_id:
            return True, "Not in session"

        success, data = self.request('POST', f'/api/sessions/{self.session_id}/leave')

        if success:
            old_session = self.session_id
            self.session_id = None
            self.other_players = {}
            self.activities = []
            self.combat_session = None
            self.log(f"Left session: {old_session}")

        return success, data

    def get_session_players(self) -> List[Dict]:
        """Get players in current session"""
        if not self.session_id:
            return []

        success, data = self.request('GET', f'/api/sessions/{self.session_id}/players')
        if success:
            return data.get('players', [])
        return []

    def update_position(self, x: float, y: float) -> bool:
        """Update player position"""
        if not self.session_id or not self.user_id:
            return False

        # Check if position changed significantly
        dx = abs(x - self.last_position[0])
        dy = abs(y - self.last_position[1])

        if dx < self.POSITION_THRESHOLD and dy < self.POSITION_THRESHOLD:
            return True  # No significant change

        success, _ = self.request('POST', f'/api/sessions/{self.session_id}/update-position', {
            'x': x,
            'y': y
        })

        if success:
            self.last_position = [x, y]
            self.last_update = time.time()

        return success

    def sync_session(self) -> Dict:
        """Sync session data"""
        if not self.session_id:
            return {}

        success, data = self.request('GET', f'/api/sessions/{self.session_id}/sync')
        if success:
            # Update other players
            players = data.get('players', [])
            self.other_players = {
                p['user_id']: p for p in players
                if p['user_id'] != self.user_id
            }

            # Update activities
            new_activities = data.get('activities', [])
            self.activities.extend([
                a for a in new_activities
                if a['id'] != self.last_activity_id
            ])
            self.activities = self.activities[-100:]  # Keep only recent activities

            if new_activities:
                self.last_activity_id = new_activities[-1]['id']

            # Update combat session
            combat_data = data.get('combat')
            if combat_data:
                self.combat_session = combat_data
            elif self.combat_session and self.combat_session.get('is_active'):
                self.combat_session = None  # Combat ended

            self.last_sync = time.time()
            self.sync_failures = 0

            return data
        else:
            self.sync_failures += 1
            self.log(f"Sync failed ({self.sync_failures}/{self.MAX_SYNC_FAILURES})")
            return {}

    # Combat methods
    def start_combat(self, enemy_data: Dict) -> tuple:
        """Start combat session"""
        if not self.session_id:
            return False, "Not in session"

        return self.request('POST', f'/api/sessions/{self.session_id}/combat/start', {
            'enemy_data': enemy_data
        })

    def combat_action(self, action: str, action_data: Dict = None) -> tuple:
        """Perform combat action"""
        if not self.session_id:
            return False, "Not in session"

        return self.request('POST', f'/api/sessions/{self.session_id}/combat/action', {
            'action': action,
            'data': action_data or {}
        })

    def end_combat(self, result: str = 'unknown') -> tuple:
        """End combat session"""
        if not self.session_id:
            return False, "Not in session"

        return self.request('POST', f'/api/sessions/{self.session_id}/combat/end', {
            'result': result
        })

    # Chat methods
    def send_chat_message(self, message: str) -> tuple:
        """Send chat message"""
        if not self.session_id:
            return False, "Not in session"

        return self.request('POST', f'/api/sessions/{self.session_id}/chat', {
            'message': message
        })

    def get_chat_messages(self, limit: int = 50) -> List[Dict]:
        """Get chat messages"""
        if not self.session_id:
            return []

        success, data = self.request('GET', f'/api/sessions/{self.session_id}/chat?limit={limit}')
        if success:
            return data.get('messages', [])
        return []

    # Background synchronization
    def start_sync_thread(self):
        """Start background sync thread"""
        if self.sync_thread and self.sync_thread.is_alive():
            return

        self.sync_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        self.log("Sync thread started")

    def stop_sync_thread(self):
        """Stop background sync thread"""
        self.sync_running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=1.0)
        self.log("Sync thread stopped")

    def _sync_loop(self):
        """Background sync loop"""
        while self.sync_running and self.connected:
            try:
                if self.session_id and time.time() - self.last_sync > self.SYNC_INTERVAL:
                    self.sync_session()

                if self.sync_failures >= self.MAX_SYNC_FAILURES:
                    self.log("Too many sync failures, attempting reconnect...")
                    # Here you could implement reconnection logic
                    self.sync_failures = 0

                time.sleep(0.1)  # Small sleep to prevent busy waiting

            except Exception as e:
                self.log(f"Sync loop error: {e}")
                time.sleep(1.0)  # Longer sleep on error

    # Utility methods
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self.connected and self.user_id is not None

    def is_in_session(self) -> bool:
        """Check if in a session"""
        return self.session_id is not None

    def is_in_combat(self) -> bool:
        """Check if in combat"""
        return self.combat_session and self.combat_session.get('is_active', False)

    def get_my_turn(self) -> bool:
        """Check if it's my turn in combat"""
        if not self.is_in_combat():
            return False
        return self.combat_session.get('current_turn') == self.user_id

    def get_combat_turn_info(self) -> Dict:
        """Get current turn information"""
        if not self.is_in_combat():
            return {}

        return {
            'current_turn': self.combat_session.get('current_turn'),
            'turn_index': self.combat_session.get('current_turn_index', 0),
            'turn_order': self.combat_session.get('turn_order', []),
            'is_my_turn': self.get_my_turn()
        }

    def get_recent_activities(self, activity_type: str = None, limit: int = 10) -> List[Dict]:
        """Get recent activities, optionally filtered by type"""
        activities = self.activities[-limit:] if limit else self.activities

        if activity_type:
            activities = [a for a in activities if a.get('type') == activity_type]

        return activities
