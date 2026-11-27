/**
 * Database module for VHS Video Stack
 * Uses SQLite for persistent storage of rooms, users, and sessions
 */

import Database from './lib/sqlite.js';
import crypto from 'crypto';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Database file: DB_PATH (compose mounts a persistent volume at /data), else ../data/vhs.db
export const dbPath = process.env.DB_PATH || path.join(__dirname, '..', 'data', 'vhs.db');
const dataDir = path.dirname(dbPath);
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const db = new Database(dbPath);

// Enable WAL mode for better performance
db.pragma('journal_mode = WAL');

// Initialize schema
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    is_admin INTEGER DEFAULT 0,
    can_create_rooms INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT,
    access_code TEXT NOT NULL,
    created_by TEXT REFERENCES users(id),
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    magic_token TEXT UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL,
    user_agent TEXT,
    ip_address TEXT
  );
  
  CREATE TABLE IF NOT EXISTS room_access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT REFERENCES users(id),
    room_id TEXT REFERENCES rooms(id),
    session_id TEXT REFERENCES sessions(id),
    first_joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
    join_count INTEGER DEFAULT 1,
    UNIQUE(user_id, room_id)
  );
  
  CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_id TEXT,
    room_id TEXT,
    session_id TEXT,
    details TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
  CREATE INDEX IF NOT EXISTS idx_sessions_magic_token ON sessions(magic_token);
  CREATE INDEX IF NOT EXISTS idx_room_access_user ON room_access(user_id);
  CREATE INDEX IF NOT EXISTS idx_audit_log_type ON audit_log(event_type);
  CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
  CREATE INDEX IF NOT EXISTS idx_audit_log_room ON audit_log(room_id);
`);

// Generate unique IDs
export function generateId(prefix = '') {
  const id = crypto.randomBytes(12).toString('hex');
  return prefix ? `${prefix}_${id}` : id;
}

// Generate magic link token
export function generateMagicToken() {
  return crypto.randomBytes(32).toString('hex');
}

// Generate random passphrase (word-based)
const WORD_LIST = [
  'apple', 'banana', 'cherry', 'dragon', 'eagle', 'forest', 'garden', 'harbor',
  'island', 'jungle', 'kayak', 'lemon', 'mango', 'nature', 'ocean', 'piano',
  'quartz', 'river', 'sunset', 'tiger', 'umbrella', 'valley', 'winter', 'xylophone',
  'yellow', 'zebra', 'anchor', 'bridge', 'castle', 'desert', 'ember', 'falcon',
  'glacier', 'horizon', 'iceberg', 'jupiter', 'kingdom', 'lantern', 'meadow', 'neptune',
  'orchid', 'phoenix', 'quasar', 'rapids', 'summit', 'thunder', 'universe', 'volcano',
  'whisper', 'xenon', 'yonder', 'zenith'
];

export function generatePassphrase(wordCount = 3) {
  const words = [];
  for (let i = 0; i < wordCount; i++) {
    const randomIndex = crypto.randomInt(0, WORD_LIST.length);
    words.push(WORD_LIST[randomIndex]);
  }
  return words.join('-');
}

// ============ USER OPERATIONS ============

const createUserStmt = db.prepare(`
  INSERT INTO users (id, name, email, is_admin, can_create_rooms, created_at, updated_at)
  VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
`);

const getUserByIdStmt = db.prepare(`SELECT * FROM users WHERE id = ?`);
const getAllUsersStmt = db.prepare(`SELECT * FROM users ORDER BY created_at DESC`);

export function createUser({ name, email, isAdmin = false, canCreateRooms = false }) {
  const id = generateId('user');
  createUserStmt.run(id, name, email || null, isAdmin ? 1 : 0, canCreateRooms ? 1 : 0);
  return getUserByIdStmt.get(id);
}

export function getUserById(id) {
  return getUserByIdStmt.get(id);
}

export function getAllUsers() {
  return getAllUsersStmt.all();
}

// ============ ROOM OPERATIONS ============

const createRoomStmt = db.prepare(`
  INSERT INTO rooms (id, name, display_name, access_code, created_by, enabled, created_at, updated_at)
  VALUES (?, ?, ?, ?, ?, 1, datetime('now'), datetime('now'))
`);

const getRoomByIdStmt = db.prepare(`SELECT * FROM rooms WHERE id = ?`);
const getRoomByNameStmt = db.prepare(`SELECT * FROM rooms WHERE name = ? AND enabled = 1`);
const getAllRoomsStmt = db.prepare(`SELECT * FROM rooms ORDER BY created_at DESC`);
const getEnabledRoomsStmt = db.prepare(`SELECT * FROM rooms WHERE enabled = 1 ORDER BY created_at DESC`);
const updateRoomStmt = db.prepare(`
  UPDATE rooms SET name = ?, display_name = ?, access_code = ?, enabled = ?, updated_at = datetime('now')
  WHERE id = ?
`);
const deleteRoomStmt = db.prepare(`DELETE FROM rooms WHERE id = ?`);

export function createRoom({ name, displayName, accessCode, createdBy }) {
  const id = generateId('room');
  const code = accessCode || generatePassphrase();
  createRoomStmt.run(id, name, displayName || name, code, createdBy);
  return getRoomByIdStmt.get(id);
}

export function getRoomById(id) {
  return getRoomByIdStmt.get(id);
}

export function getRoomByName(name) {
  return getRoomByNameStmt.get(name);
}

export function getAllRooms() {
  return getAllRoomsStmt.all();
}

export function getEnabledRooms() {
  return getEnabledRoomsStmt.all();
}

export function updateRoom(id, { name, displayName, accessCode, enabled }) {
  const room = getRoomByIdStmt.get(id);
  if (!room) return null;
  
  updateRoomStmt.run(
    name ?? room.name,
    displayName ?? room.display_name,
    accessCode ?? room.access_code,
    enabled !== undefined ? (enabled ? 1 : 0) : room.enabled,
    id
  );
  return getRoomByIdStmt.get(id);
}

export function deleteRoom(id) {
  // Delete room_access records first to avoid foreign key constraint
  db.prepare(`DELETE FROM room_access WHERE room_id = ?`).run(id);
  // Delete audit log entries for this room
  db.prepare(`DELETE FROM audit_log WHERE room_id = ?`).run(id);
  // Now delete the room
  return deleteRoomStmt.run(id);
}

// ============ SESSION OPERATIONS ============

const createSessionStmt = db.prepare(`
  INSERT INTO sessions (id, user_id, magic_token, expires_at, user_agent, ip_address)
  VALUES (?, ?, ?, datetime('now', '+30 days'), ?, ?)
`);

const getSessionByIdStmt = db.prepare(`
  SELECT s.*, u.name as user_name, u.email as user_email, u.is_admin, u.can_create_rooms
  FROM sessions s
  JOIN users u ON s.user_id = u.id
  WHERE s.id = ? AND datetime(s.expires_at) > datetime('now')
`);

const updateSessionLastUsedStmt = db.prepare(`
  UPDATE sessions SET last_used = datetime('now') WHERE id = ?
`);

const deleteExpiredSessionsStmt = db.prepare(`
  DELETE FROM sessions WHERE datetime(expires_at) < datetime('now')
`);

export function createSession({ userId, userAgent, ipAddress }) {
  const id = generateId('sess');
  const magicToken = generateMagicToken();
  createSessionStmt.run(id, userId, magicToken, userAgent || null, ipAddress || null);
  return { 
    ...getSessionByIdStmt.get(id),
    magicToken // Return the magic token only during creation
  };
}

export function getSessionById(id) {
  return getSessionByIdStmt.get(id);
}

export function updateSessionLastUsed(id) {
  return updateSessionLastUsedStmt.run(id);
}

export function cleanupExpiredSessions() {
  return deleteExpiredSessionsStmt.run();
}

// ============ ROOM ACCESS OPERATIONS ============

const recordRoomAccessStmt = db.prepare(`
  INSERT INTO room_access (user_id, room_id, session_id, first_joined_at, last_joined_at, join_count)
  VALUES (?, ?, ?, datetime('now'), datetime('now'), 1)
  ON CONFLICT(user_id, room_id) DO UPDATE SET
    last_joined_at = datetime('now'),
    join_count = join_count + 1,
    session_id = excluded.session_id
`);

const hasUserAccessedRoomStmt = db.prepare(`
  SELECT 1 FROM room_access WHERE user_id = ? AND room_id = ?
`);

export function recordRoomAccess({ userId, roomId, sessionId }) {
  return recordRoomAccessStmt.run(userId, roomId, sessionId);
}

export function hasUserAccessedRoom(userId, roomId) {
  return !!hasUserAccessedRoomStmt.get(userId, roomId);
}

// ============ AUDIT LOG OPERATIONS ============

const addAuditLogStmt = db.prepare(`
  INSERT INTO audit_log (event_type, user_id, room_id, session_id, details, ip_address, user_agent)
  VALUES (?, ?, ?, ?, ?, ?, ?)
`);

const getAuditLogStmt = db.prepare(`
  SELECT al.*, u.name as user_name, r.name as room_name
  FROM audit_log al
  LEFT JOIN users u ON al.user_id = u.id
  LEFT JOIN rooms r ON al.room_id = r.id
  ORDER BY al.created_at DESC
  LIMIT ?
`);

export function addAuditLog({ eventType, userId, roomId, sessionId, details, ipAddress, userAgent }) {
  return addAuditLogStmt.run(
    eventType,
    userId || null,
    roomId || null,
    sessionId || null,
    details ? JSON.stringify(details) : null,
    ipAddress || null,
    userAgent || null
  );
}

export function getAuditLog(limit = 100) {
  return getAuditLogStmt.all(limit);
}

export function closeDatabase() {
  db.close();
}

export default {
  dbPath,
  generateId,
  generateMagicToken,
  generatePassphrase,

  // Users
  createUser,
  getUserById,
  getAllUsers,

  // Rooms
  createRoom,
  getRoomById,
  getRoomByName,
  getAllRooms,
  getEnabledRooms,
  updateRoom,
  deleteRoom,
  
  // Sessions
  createSession,
  getSessionById,
  updateSessionLastUsed,
  cleanupExpiredSessions,

  // Room access
  recordRoomAccess,
  hasUserAccessedRoom,

  // Audit log
  addAuditLog,
  getAuditLog,

  closeDatabase,
};
