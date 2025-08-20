#!/usr/bin/env python3
"""
Multiplayer RPG Server - FIXED VERSION
HTTP-based server for the Magitech RPG Adventure game with proper synchronization
"""

import json
import time
import uuid
import threading
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
from threading import Timer

app = Flask(__name__)
CORS(app)


class GameServer:
    def __init__(self):
        self.players = {}  # player_id: player_data
        self.game_sessions = {}  # session_id: session_data
        self.chat_messages = []
        self.max_chat_messages = 100
        self.player_lock = threading.Lock()
        self.init_database()
        # Combat system storage
        self.combat_sessions = {}  # session_id: CombatSession
        self.client_activities = {}  # session_id: [activities]
        self.combat_lock = threading.Lock()

        # Enhanced session tracking for better synchronization
        self.session_players = {}  # session_id: {player_id: player_data}
        self.player_positions = {}  # session_id: {player_id: {x, y, timestamp}}
        self.position_lock = threading.Lock()

        # Activity tracking for real-time events
        self.activity_sequence = 0
        self.activity_lock = threading.Lock()

    def init_database(self):
        """Initialize SQLite database for persistent storage"""
        # Ensure assets directory exists
        os.makedirs('assets', exist_ok=True)

        self.conn = sqlite3.connect('assets/rpg_server.db', check_same_thread=False)
        self.db_lock = threading.Lock()

        # Create tables
        with self.db_lock:
            cursor = self.conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')

            # Characters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS characters (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Game sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host_user_id TEXT NOT NULL,
                    max_players INTEGER DEFAULT 4,
                    current_players INTEGER DEFAULT 0,
                    world_data TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (host_user_id) REFERENCES users (id)
                )
            ''')

            # Session players table - ENHANCED with better tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_players (
                    session_id TEXT,
                    user_id TEXT,
                    character_id TEXT,
                    character_data TEXT,
                    position_x REAL DEFAULT 400,
                    position_y REAL DEFAULT 300,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    PRIMARY KEY (session_id, user_id),
                    FOREIGN KEY (session_id) REFERENCES game_sessions (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (character_id) REFERENCES characters (id)
                )
            ''')

            # Chat messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_id TEXT,
                    username TEXT,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Session activities table for real-time events
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    activity_id TEXT UNIQUE,
                    user_id TEXT,
                    username TEXT,
                    activity_type TEXT,
                    activity_data TEXT,
                    sequence_number INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions (id)
                )
            ''')

            self.conn.commit()

    def save_character(self, user_id, character_data):
        """Save character data to database"""
        with self.db_lock:
            cursor = self.conn.cursor()
            character_id = character_data.get('id', str(uuid.uuid4()))
            character_data['id'] = character_id

            cursor.execute('''
                INSERT OR REPLACE INTO characters 
                (id, user_id, name, data, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (character_id, user_id, character_data.get('Name', 'Unknown'), json.dumps(character_data)))

            self.conn.commit()
            return character_id

    def load_character(self, character_id, user_id):
        """Load character data from database"""
        with self.db_lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT data FROM characters 
                WHERE id = ? AND user_id = ?
            ''', (character_id, user_id))

            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None

    def get_user_characters(self, user_id):
        """Get all characters for a user"""
        with self.db_lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, name, created_at FROM characters 
                WHERE user_id = ? 
                ORDER BY updated_at DESC
            ''', (user_id,))

            return [{'id': row[0], 'name': row[1], 'created_at': row[2]}
                    for row in cursor.fetchall()]

    def delete_character(self, character_id, user_id):
        """Delete a character"""
        with self.db_lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM characters 
                WHERE id = ? AND user_id = ?
            ''', (character_id, user_id))

            rows_affected = cursor.rowcount
            self.conn.commit()
            return rows_affected > 0

    def update_player_position(self, session_id, user_id, x, y):
        """Update player position with better synchronization"""
        current_time = time.time()

        with self.position_lock:
            if session_id not in self.player_positions:
                self.player_positions[session_id] = {}

            # Store previous position for change detection
            old_pos = self.player_positions[session_id].get(user_id, {'x': 0, 'y': 0})

            self.player_positions[session_id][user_id] = {
                'x': x,
                'y': y,
                'timestamp': current_time,
                'changed': abs(old_pos['x'] - x) > 1 or abs(old_pos['y'] - y) > 1
            }

        # Also update in database with better timestamp tracking
        with self.db_lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE session_players 
                SET position_x = ?, position_y = ?, last_update = CURRENT_TIMESTAMP
                WHERE session_id = ? AND user_id = ?
            ''', (x, y, session_id, user_id))
            self.conn.commit()

        # Create position update activity for other clients
        self.add_session_activity(session_id, user_id, 'position_update', {
            'x': x, 'y': y, 'timestamp': current_time
        })

    def get_session_players(self, session_id):
        """Get all players in a session with their current positions"""
        with self.db_lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT sp.user_id, u.username, sp.character_id, sp.character_data,
                       sp.position_x, sp.position_y, sp.last_update, sp.last_sync
                FROM session_players sp
                JOIN users u ON sp.user_id = u.id
                WHERE sp.session_id = ? AND sp.is_active = TRUE
                ORDER BY sp.joined_at
            ''', (session_id,))

            players = []
            for row in cursor.fetchall():
                player_data = {
                    'user_id': row[0],
                    'username': row[1],
                    'character_id': row[2],
                    'character_data': json.loads(row[3]) if row[3] else {},
                    'position': {'x': row[4], 'y': row[5]},
                    'last_update': row[6],
                    'last_sync': row[7]
                }

                # Update with most recent position if available
                if session_id in self.player_positions and row[0] in self.player_positions[session_id]:
                    pos = self.player_positions[session_id][row[0]]
                    player_data['position'] = {'x': pos['x'], 'y': pos['y']}
                    player_data['position_timestamp'] = pos.get('timestamp', time.time())

                players.append(player_data)

            return players

    def add_session_activity(self, session_id, user_id, activity_type, activity_data):
        """Add activity to session for real-time synchronization"""
        with self.activity_lock:
            self.activity_sequence += 1
            sequence = self.activity_sequence

            activity_id = f"{activity_type}_{sequence}_{int(time.time())}"

            # Get username
            with self.db_lock:
                cursor = self.conn.cursor()
                cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                username = result[0] if result else 'Unknown'

            activity = {
                'id': activity_id,
                'user_id': user_id,
                'username': username,
                'type': activity_type,
                'data': activity_data,
                'sequence': sequence,
                'timestamp': time.time()
            }

            # Add to runtime activities
            if session_id not in self.client_activities:
                self.client_activities[session_id] = []

            self.client_activities[session_id].append(activity)

            # Keep only recent activities (last 100)
            self.client_activities[session_id] = self.client_activities[session_id][-100:]

            # Also save to database for persistence
            with self.db_lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO session_activities 
                    (session_id, activity_id, user_id, username, activity_type, activity_data, sequence_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, activity_id, user_id, username, activity_type, json.dumps(activity_data), sequence))
                self.conn.commit()

    def get_session_activities(self, session_id, since_sequence=0, limit=50):
        """Get recent session activities for synchronization"""
        activities = self.client_activities.get(session_id, [])

        # Filter by sequence if specified
        if since_sequence > 0:
            activities = [a for a in activities if a.get('sequence', 0) > since_sequence]

        # Limit results
        return activities[-limit:] if limit > 0 else activities

    def update_player_sync_timestamp(self, session_id, user_id):
        """Update player's last sync timestamp"""
        with self.db_lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE session_players 
                SET last_sync = CURRENT_TIMESTAMP
                WHERE session_id = ? AND user_id = ?
            ''', (session_id, user_id))
            self.conn.commit()


class CombatSession:
    def __init__(self, session_id, initiator_id, enemy_data, participants):
        self.session_id = session_id
        self.combat_id = f"combat_{int(time.time())}_{initiator_id}"
        self.initiator_id = initiator_id
        self.enemy_data = enemy_data.copy()
        self.participants = participants[:]  # Copy the list
        self.current_turn_index = 0
        # Shuffle players for random turn order, but keep enemy last
        player_list = [p for p in participants if p != 'ENEMY']
        random.shuffle(player_list)
        self.turn_order = player_list + ['ENEMY']
        self.is_active = True
        self.created_at = time.time()
        self.turn_timeout = 30  # 30 seconds per turn
        self.last_turn_time = time.time()
        self.turn_sequence = 0  # Track turn changes

    def get_current_turn(self):
        if not self.turn_order or self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
        if self.turn_order:
            return self.turn_order[self.current_turn_index]
        return None

    def advance_turn(self):
        if self.turn_order:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            self.last_turn_time = time.time()
            self.turn_sequence += 1
        return self.get_current_turn()

    def is_turn_expired(self):
        return (time.time() - self.last_turn_time) > self.turn_timeout

    def to_dict(self):
        return {
            'combat_id': self.combat_id,
            'session_id': self.session_id,
            'initiator_id': self.initiator_id,
            'enemy_data': self.enemy_data,
            'participants': self.participants,
            'turn_order': self.turn_order,
            'current_turn_index': self.current_turn_index,
            'current_turn': self.get_current_turn(),
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_turn_time': self.last_turn_time,
            'turn_timeout': self.turn_timeout,
            'turn_sequence': self.turn_sequence
        }


def get_username_by_id(user_id, cursor):
    """Get username by user_id"""
    if user_id == 'ENEMY':
        return 'Enemy'

    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 'Unknown'


def process_enemy_turn(session_id):
    """Process enemy turn automatically with improved logic"""
    print(f"👹 [SERVER] Processing enemy turn for session {session_id}")

    try:
        with server.combat_lock:
            combat_session = server.combat_sessions.get(session_id)
            if not combat_session or not combat_session.is_active:
                print(f"👹 [SERVER] Combat session not active or not found")
                return

            # Get alive players from session
            session_players = server.get_session_players(session_id)
            alive_players = [p['user_id'] for p in session_players]

            if not alive_players:
                print(f"👹 [SERVER] No alive players, ending combat")
                server.combat_sessions.pop(session_id, None)
                return

            # Select random target
            target_player_id = random.choice(alive_players)
            target_player = next((p for p in session_players if p['user_id'] == target_player_id), None)

            if not target_player:
                print(f"👹 [SERVER] Target player not found")
                return

            # Calculate damage
            enemy_level = combat_session.enemy_data.get('level', 1)
            base_damage = random.randint(3, 12)
            level_bonus = enemy_level * 2
            total_damage = base_damage + level_bonus

            print(f"👹 [SERVER] Enemy attacking {target_player['username']} for {total_damage} damage")

            # Add enemy action activity
            server.add_session_activity(session_id, 'ENEMY', 'enemy_action', {
                'action': 'attack',
                'target_player_id': target_player_id,
                'target_player_name': target_player['username'],
                'damage_dealt': total_damage,
                'enemy_name': combat_session.enemy_data.get('name', 'Enemy'),
                'combat_session_id': combat_session.combat_id
            })

            # Advance to next player turn
            next_turn = combat_session.advance_turn()
            print(f"🔄 [SERVER] After enemy turn, advancing to: {next_turn}")

            # Add turn change activity
            with server.db_lock:
                cursor = server.conn.cursor()
                next_username = get_username_by_id(next_turn, cursor)

            server.add_session_activity(session_id, 'SERVER', 'turn_changed', {
                'new_turn_player': next_turn,
                'new_turn_name': next_username,
                'combat_session_id': combat_session.combat_id,
                'turn_index': combat_session.current_turn_index,
                'turn_sequence': combat_session.turn_sequence,
                'combat_state': combat_session.to_dict()
            })

            print(f"✅ [SERVER] Enemy turn completed, next turn: {next_turn}")

    except Exception as e:
        print(f"❌ [SERVER] Error processing enemy turn: {e}")
        import traceback
        traceback.print_exc()


server = GameServer()


# Authentication endpoints
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    with server.db_lock:
        cursor = server.conn.cursor()

        # Check if username exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 409

        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)

        cursor.execute('''
            INSERT INTO users (id, username, password_hash)
            VALUES (?, ?, ?)
        ''', (user_id, username, password_hash))

        server.conn.commit()

    return jsonify({
        'success': True,
        'user_id': user_id,
        'username': username
    })


@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    with server.db_lock:
        cursor = server.conn.cursor()
        cursor.execute('''
            SELECT id, password_hash FROM users WHERE username = ?
        ''', (username,))

        result = cursor.fetchone()
        if not result or not check_password_hash(result[1], password):
            return jsonify({'error': 'Invalid username or password'}), 401

        user_id = result[0]

        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))
        server.conn.commit()

    return jsonify({
        'success': True,
        'user_id': user_id,
        'username': username
    })


# Character management endpoints
@app.route('/api/characters', methods=['GET'])
def get_characters():
    """Get user's characters"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    characters = server.get_user_characters(user_id)
    return jsonify({'characters': characters})


@app.route('/api/characters', methods=['POST'])
def save_character():
    """Save character data"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    character_data = request.get_json()
    if not character_data:
        return jsonify({'error': 'Character data required'}), 400

    character_id = server.save_character(user_id, character_data)
    return jsonify({
        'success': True,
        'character_id': character_id
    })


@app.route('/api/characters/<character_id>', methods=['GET'])
def load_character(character_id):
    """Load character data"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    character_data = server.load_character(character_id, user_id)
    if not character_data:
        return jsonify({'error': 'Character not found'}), 404

    return jsonify({'character': character_data})


@app.route('/api/characters/<character_id>', methods=['DELETE'])
def delete_character(character_id):
    """Delete character"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    success = server.delete_character(character_id, user_id)
    if not success:
        return jsonify({'error': 'Character not found'}), 404

    return jsonify({'success': True})


# Session management endpoints
@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get available game sessions"""
    with server.db_lock:
        cursor = server.conn.cursor()
        cursor.execute('''
            SELECT gs.id, gs.name, gs.max_players, gs.current_players, 
                   u.username as host_name, gs.created_at
            FROM game_sessions gs
            JOIN users u ON gs.host_user_id = u.id
            WHERE gs.is_active = TRUE
            ORDER BY gs.created_at DESC
        ''')

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'name': row[1],
                'max_players': row[2],
                'current_players': row[3],
                'host_name': row[4],
                'created_at': row[5]
            })

    return jsonify({'sessions': sessions})


@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create new game session"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    data = request.get_json()
    session_name = data.get('name', '').strip()
    max_players = min(max(data.get('max_players', 4), 2), 8)  # Between 2-8 players

    if not session_name:
        return jsonify({'error': 'Session name required'}), 400

    session_id = str(uuid.uuid4())

    with server.db_lock:
        cursor = server.conn.cursor()
        cursor.execute('''
            INSERT INTO game_sessions (id, name, host_user_id, max_players, current_players)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, session_name, user_id, max_players, 0))
        server.conn.commit()

    return jsonify({
        'success': True,
        'session_id': session_id,
        'name': session_name
    })


@app.route('/api/sessions/<session_id>/join', methods=['POST'])
def join_session(session_id):
    """Join a game session"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    data = request.get_json()
    character_id = data.get('character_id')
    character_data = data.get('character_data', {})

    if not character_id:
        return jsonify({'error': 'Character ID required'}), 400

    with server.db_lock:
        cursor = server.conn.cursor()

        # Check if session exists and has space
        cursor.execute('''
            SELECT current_players, max_players FROM game_sessions 
            WHERE id = ? AND is_active = TRUE
        ''', (session_id,))

        session_info = cursor.fetchone()
        if not session_info:
            return jsonify({'error': 'Session not found'}), 404

        current_players, max_players = session_info
        if current_players >= max_players:
            return jsonify({'error': 'Session is full'}), 409

        # Check if user is already in session
        cursor.execute('''
            SELECT user_id FROM session_players 
            WHERE session_id = ? AND user_id = ? AND is_active = TRUE
        ''', (session_id, user_id))

        if cursor.fetchone():
            return jsonify({'error': 'Already in session'}), 409

        # Get username for activity
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        username_result = cursor.fetchone()
        username = username_result[0] if username_result else 'Unknown'

        # Add player to session
        cursor.execute('''
            INSERT OR REPLACE INTO session_players 
            (session_id, user_id, character_id, character_data, position_x, position_y, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, character_id, json.dumps(character_data), 400, 300, True))

        # Update session player count
        cursor.execute('''
            UPDATE game_sessions 
            SET current_players = current_players + 1 
            WHERE id = ?
        ''', (session_id,))

        server.conn.commit()

    # Add player join activity
    server.add_session_activity(session_id, user_id, 'player_joined', {
        'player_name': username,
        'character_name': character_data.get('Name', 'Unknown')
    })

    return jsonify({'success': True})


@app.route('/api/sessions/<session_id>/leave', methods=['POST'])
def leave_session(session_id):
    """Leave a game session"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    with server.db_lock:
        cursor = server.conn.cursor()

        # Get username before removing
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        username_result = cursor.fetchone()
        username = username_result[0] if username_result else 'Unknown'

        # Remove player from session
        cursor.execute('''
            UPDATE session_players 
            SET is_active = FALSE 
            WHERE session_id = ? AND user_id = ?
        ''', (session_id, user_id))

        # Update session player count
        cursor.execute('''
            UPDATE game_sessions 
            SET current_players = current_players - 1 
            WHERE id = ?
        ''', (session_id,))

        server.conn.commit()

    # Remove from runtime data
    with server.position_lock:
        if session_id in server.player_positions and user_id in server.player_positions[session_id]:
            del server.player_positions[session_id][user_id]

    # Add player leave activity
    server.add_session_activity(session_id, user_id, 'player_left', {
        'player_name': username
    })

    return jsonify({'success': True})


@app.route('/api/sessions/<session_id>/players', methods=['GET'])
def get_session_players_endpoint(session_id):
    """Get all players in a session"""
    players = server.get_session_players(session_id)
    return jsonify({'players': players})


@app.route('/api/sessions/<session_id>/update-position', methods=['POST'])
def update_position(session_id):
    """Update player position in session"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    data = request.get_json()
    x = data.get('x')
    y = data.get('y')

    if x is None or y is None:
        return jsonify({'error': 'Position coordinates required'}), 400

    server.update_player_position(session_id, user_id, x, y)
    server.update_player_sync_timestamp(session_id, user_id)

    return jsonify({'success': True})


@app.route('/api/sessions/<session_id>/sync', methods=['GET'])
def sync_session(session_id):
    """Enhanced session sync with activity tracking"""
    user_id = request.headers.get('User-ID')
    since_sequence = int(request.args.get('since_sequence', 0))

    players = server.get_session_players(session_id)

    # Get recent activities since last sync
    activities = server.get_session_activities(session_id, since_sequence, 50)

    # Get combat status
    combat_session = server.combat_sessions.get(session_id)
    combat_data = combat_session.to_dict() if combat_session else None

    # Update sync timestamp for requesting user
    if user_id:
        server.update_player_sync_timestamp(session_id, user_id)

    # Get latest sequence number for next sync
    latest_sequence = max([a.get('sequence', 0) for a in activities], default=since_sequence)

    return jsonify({
        'players': players,
        'activities': activities,
        'combat': combat_data,
        'latest_sequence': latest_sequence,
        'timestamp': time.time(),
        'success': True
    })


# Combat endpoints with enhanced synchronization
@app.route('/api/sessions/<session_id>/combat/start', methods=['POST'])
def start_combat(session_id):
    """Start combat session with improved turn management"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    data = request.get_json()
    enemy_data = data.get('enemy_data', {})

    # Get all players in session
    session_players = server.get_session_players(session_id)
    participant_ids = [p['user_id'] for p in session_players]

    if not participant_ids:
        return jsonify({'error': 'No players in session'}), 400

    with server.combat_lock:
        # End any existing combat
        if session_id in server.combat_sessions:
            server.combat_sessions[session_id].is_active = False

        # Create new combat session
        combat_session = CombatSession(session_id, user_id, enemy_data, participant_ids)
        server.combat_sessions[session_id] = combat_session

        # Add combat start activity
        server.add_session_activity(session_id, user_id, 'combat_started', {
            'combat_session_id': combat_session.combat_id,
            'enemy_data': enemy_data,
            'participants': participant_ids,
            'turn_order': combat_session.turn_order,
            'first_turn': combat_session.get_current_turn(),
            'turn_sequence': combat_session.turn_sequence,
            'combat_state': combat_session.to_dict()
        })

    return jsonify({
        'success': True,
        'combat_session_id': combat_session.combat_id,
        'combat_data': combat_session.to_dict()
    })


@app.route('/api/sessions/<session_id>/combat/action', methods=['POST'])
def combat_action(session_id):
    """Process combat action with better synchronization"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    data = request.get_json()
    action_type = data.get('action')
    action_data = data.get('data', {})

    with server.combat_lock:
        combat_session = server.combat_sessions.get(session_id)
        if not combat_session or not combat_session.is_active:
            return jsonify({'error': 'No active combat session'}), 404

        current_turn = combat_session.get_current_turn()
        if current_turn != user_id:
            return jsonify({'error': 'Not your turn'}), 403

        # Add combat action activity
        server.add_session_activity(session_id, user_id, 'combat_action', {
            'action': action_type,
            'combat_session_id': combat_session.combat_id,
            'turn_sequence': combat_session.turn_sequence,
            **action_data
        })

        # Advance turn
        next_turn = combat_session.advance_turn()

        # Add turn change activity
        with server.db_lock:
            cursor = server.conn.cursor()
            next_username = get_username_by_id(next_turn, cursor)

        server.add_session_activity(session_id, 'SERVER', 'turn_changed', {
            'new_turn_player': next_turn,
            'new_turn_name': next_username,
            'combat_session_id': combat_session.combat_id,
            'turn_index': combat_session.current_turn_index,
            'turn_sequence': combat_session.turn_sequence,
            'combat_state': combat_session.to_dict()
        })

        # If it's enemy turn, schedule enemy action
        if next_turn == 'ENEMY':
            Timer(2.0, process_enemy_turn, args=[session_id]).start()

    return jsonify({
        'success': True,
        'next_turn': next_turn,
        'turn_sequence': combat_session.turn_sequence,
        'combat_state': combat_session.to_dict()
    })


@app.route('/api/sessions/<session_id>/combat/end', methods=['POST'])
def end_combat(session_id):
    """End combat session"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    data = request.get_json()
    result = data.get('result', 'unknown')  # 'victory', 'defeat', 'escape'

    with server.combat_lock:
        combat_session = server.combat_sessions.get(session_id)
        if combat_session:
            combat_session.is_active = False

            # Add combat end activity
            server.add_session_activity(session_id, user_id, 'combat_ended', {
                'combat_session_id': combat_session.combat_id,
                'result': result,
                'duration': time.time() - combat_session.created_at
            })

            # Clean up
            server.combat_sessions.pop(session_id, None)

    return jsonify({'success': True})


# Chat endpoints
@app.route('/api/sessions/<session_id>/chat', methods=['POST'])
def send_chat_message(session_id):
    """Send chat message"""
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    data = request.get_json()
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Message required'}), 400

    with server.db_lock:
        cursor = server.conn.cursor()

        # Get username
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'User not found'}), 404

        username = result[0]

        # Save chat message
        cursor.execute('''
            INSERT INTO chat_messages (session_id, user_id, username, message)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, username, message))
        server.conn.commit()

    # Add chat activity
    server.add_session_activity(session_id, user_id, 'chat_message', {
        'message': message
    })

    return jsonify({'success': True})


@app.route('/api/sessions/<session_id>/chat', methods=['GET'])
def get_chat_messages(session_id):
    """Get chat messages"""
    limit = min(int(request.args.get('limit', 50)), 100)

    with server.db_lock:
        cursor = server.conn.cursor()
        cursor.execute('''
            SELECT username, message, timestamp 
            FROM chat_messages 
            WHERE session_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (session_id, limit))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                'username': row[0],
                'message': row[1],
                'timestamp': row[2]
            })

    return jsonify({'messages': list(reversed(messages))})


@app.route('/', methods=['GET'])
def root():
    """Root route - Game information"""
    return '''
    <html>
    <head>
        <title>Magitech RPG Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #0f1423; color: #dcddde; }
            h1 { color: #ffd700; }
            h2 { color: #4a90e2; }
            .status { background-color: #2d5a2d; padding: 10px; border-radius: 5px; }
            .info { background-color: #2a2a2a; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .endpoint { background-color: #1a1a1a; padding: 8px; margin: 5px 0; border-left: 3px solid #4a90e2; }
        </style>
    </head>
    <body>
        <h1>🎮 Magitech RPG Adventure Server</h1>
        <div class="status">
            <h2>✅ Server Status: Online</h2>
            <p>The multiplayer RPG server is running and ready for connections.</p>
        </div>

        <div class="info">
            <h2>🎯 Game Features</h2>
            <ul>
                <li>Multiplayer turn-based RPG with real-time synchronization</li>
                <li>6 races and 6 classes with D&D-style stats</li>
                <li>Zelda-inspired tile-based world map</li>
                <li>Turn-based combat system</li>
                <li>Character creation and progression</li>
                <li>Comprehensive loot system</li>
            </ul>
        </div>

        <div class="info">
            <h2>🚀 How to Play</h2>
            <p>To play the game, run the Python client:</p>
            <code style="background-color: #1a1a1a; padding: 10px; display: block; margin: 10px 0;">
                python main.py
            </code>
            <p>The game client will connect to this server automatically.</p>
        </div>

        <div class="info">
            <h2>🔧 API Endpoints</h2>
            <div class="endpoint">POST /api/login - User authentication</div>
            <div class="endpoint">POST /api/register - User registration</div>
            <div class="endpoint">GET /api/sessions - List game sessions</div>
            <div class="endpoint">POST /api/sessions - Create new session</div>
            <div class="endpoint">GET/POST /api/characters - Character management</div>
            <div class="endpoint">GET /api/status - Server status</div>
        </div>

        <div class="info">
            <h2>📊 Server Information</h2>
            <p>Version: 2.1.0-fixed<br>
            Database: SQLite (assets/rpg_server.db)<br>
            Port: 8000<br>
            Enhanced multiplayer synchronization enabled</p>
        </div>
    </body>
    </html>
    '''


@app.route('/api/status', methods=['GET'])
def server_status():
    """Get server status"""
    with server.position_lock:
        active_sessions = len([s for s in server.game_sessions.values() if s.get('is_active', False)])
        total_players = sum(len(players) for players in server.player_positions.values())

    return jsonify({
        'status': 'online',
        'active_sessions': active_sessions,
        'total_players': total_players,
        'uptime': time.time(),
        'version': '2.1.0-fixed'
    })


if __name__ == '__main__':
    print("🚀 Starting Magitech RPG Server - FIXED VERSION...")
    print("📡 Server will be available at http://localhost:8000")
    print("🎮 Enhanced multiplayer synchronization enabled")
    print("⚔️ Improved turn-based combat system")
    print("💾 Database: SQLite (assets/rpg_server.db)")

    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
        threaded=True,
        use_reloader=False  # Disable reloader in production
    )
