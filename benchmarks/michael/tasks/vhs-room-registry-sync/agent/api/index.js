/**
 * VHS Video Stack API (room/PIN service).
 *
 * Trimmed to the room, join-token and admin surface. The LiveKit SDK is replaced by a local
 * HMAC-signed join token (no npm in this environment); the HTTP layer is ./lib/express.js.
 * The app is the default export; it only listens when this file is run directly.
 */
import express from "./lib/express.js";
import crypto from "crypto";
import { fileURLToPath } from "url";

// Import local modules
import * as db from "./db.js";
import { requireRoomCreator, optionalAuth, getClientIp } from "./middleware.js";
import adminRoutes from "./admin.js";

const __filename = fileURLToPath(import.meta.url);

const app = express();

// Middleware
app.use(express.json());

// Environment variables
const {
  LIVEKIT_API_KEY = "devkey",
  LIVEKIT_API_SECRET = "devsecret",
  LIVEKIT_WS_URL = "ws://localhost:7880",
  PORT = 3000,
} = process.env;

// ============ UTILITY FUNCTIONS ============

function generateLiveKitToken(identity, name, roomName) {
  const b64 = (value) => Buffer.from(JSON.stringify(value)).toString("base64url");
  const header = b64({ alg: "HS256", typ: "JWT" });
  const payload = b64({
    iss: LIVEKIT_API_KEY,
    sub: identity,
    name,
    exp: Math.floor(Date.now() / 1000) + 30 * 60,
    video: { roomJoin: true, room: roomName, canPublish: true, canSubscribe: true, canPublishData: true },
  });
  const signature = crypto.createHmac("sha256", LIVEKIT_API_SECRET).update(`${header}.${payload}`).digest("base64url");
  return `${header}.${payload}.${signature}`;
}

// ============ ROUTES ============

// Mount admin routes
app.use('/admin', adminRoutes);

// Health check
app.get("/healthz", (_, res) => res.send("ok"));

/**
 * GET /rooms
 * List available rooms (only enabled rooms, no access codes exposed)
 */
app.get("/rooms", optionalAuth, (req, res) => {
  try {
    const rooms = db.getEnabledRooms();
    res.json({
      rooms: rooms.map(r => ({
        id: r.id,
        name: r.name,
        displayName: r.display_name
      }))
    });
  } catch (error) {
    console.error('List rooms error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /rooms
 * Create a new room (requires room creator permission)
 */
app.post("/rooms", requireRoomCreator, (req, res) => {
  try {
    const { name, displayName, accessCode } = req.body;
    
    if (!name) {
      return res.status(400).json({ error: "Room name is required" });
    }
    
    // Check if room already exists
    const existing = db.getRoomByName(name);
    if (existing) {
      return res.status(409).json({ error: "Room name already exists" });
    }
    
    const room = db.createRoom({
      name,
      displayName,
      accessCode,
      createdBy: req.user.id
    });
    
    db.addAuditLog({
      eventType: 'room_created',
      userId: req.user.id,
      roomId: room.id,
      details: { roomName: name, displayName },
      ipAddress: getClientIp(req),
      userAgent: req.get('User-Agent')
    });
    
    res.json({
      id: room.id,
      name: room.name,
      displayName: room.display_name,
      accessCode: room.access_code
    });
  } catch (error) {
    console.error('Create room error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /rooms/public
 * Create a room without authentication (public API)
 */
app.post("/rooms/public", (req, res) => {
  try {
    const { name, displayName, accessCode } = req.body;
    
    if (!name) {
      return res.status(400).json({ error: "Room name is required" });
    }
    
    if (!accessCode) {
      return res.status(400).json({ error: "Access code is required" });
    }
    
    // Check if room already exists
    const existing = db.getRoomByName(name);
    if (existing) {
      return res.status(409).json({ error: "Room name already exists" });
    }
    
    const room = db.createRoom({
      name,
      displayName: displayName || name,
      accessCode,
      createdBy: null // No user for public rooms
    });
    
    res.json({
      id: room.id,
      name: room.name,
      displayName: room.display_name,
      accessCode: room.access_code
    });
  } catch (error) {
    console.error('Create public room error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /tokens
 * Get a LiveKit token to join a room
 * Requires room access code OR authenticated session with room in history
 */
app.post("/tokens", optionalAuth, async (req, res) => {
  try {
    const { room: roomName, identity, name, accessCode, pin } = req.body;
    
    if (!roomName || !identity) {
      return res.status(400).json({ error: "Missing room/identity" });
    }
    
    // Find the room
    const room = db.getRoomByName(roomName);
    if (!room) {
      return res.status(404).json({ error: "Room not found" });
    }
    
    // Check authorization
    let authorized = false;
    let authMethod = '';
    
    // Method 1: Access code provided
    if (accessCode || pin) {
      const providedCode = accessCode || pin;
      if (providedCode === room.access_code) {
        authorized = true;
        authMethod = 'access_code';
      }
    }
    
    // Method 2: Authenticated user with room in history (rejoin)
    if (!authorized && req.user && req.session) {
      if (db.hasUserAccessedRoom(req.user.id, room.id)) {
        authorized = true;
        authMethod = 'session_rejoin';
      }
    }
    
    if (!authorized) {
      db.addAuditLog({
        eventType: 'room_join_denied',
        userId: req.user?.id,
        roomId: room.id,
        details: { reason: 'invalid_credentials' },
        ipAddress: getClientIp(req),
        userAgent: req.get('User-Agent')
      });
      
      return res.status(401).json({ error: "Invalid access code" });
    }
    
    const token = generateLiveKitToken(identity, name || identity, room.name);
    
    // Record room access if authenticated
    if (req.user && req.session) {
      db.recordRoomAccess({
        userId: req.user.id,
        roomId: room.id,
        sessionId: req.session.id
      });
    }
    
    // Log successful join
    db.addAuditLog({
      eventType: 'room_joined',
      userId: req.user?.id,
      roomId: room.id,
      sessionId: req.session?.id,
      details: { identity, authMethod },
      ipAddress: getClientIp(req),
      userAgent: req.get('User-Agent')
    });
    
    res.json({ 
      url: LIVEKIT_WS_URL, 
      token, 
      room: {
        id: room.id,
        name: room.name,
        displayName: room.display_name
      }
    });
  } catch (error) {
    console.error('Get token error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * GET /rooms/:name
 * Get room info (no access code exposed)
 */
app.get("/rooms/:name", optionalAuth, (req, res) => {
  try {
    const room = db.getRoomByName(req.params.name);
    
    if (!room) {
      return res.status(404).json({ error: "Room not found" });
    }
    
    // Check if user has access (for rejoin capability)
    let canRejoin = false;
    if (req.user) {
      canRejoin = db.hasUserAccessedRoom(req.user.id, room.id);
    }
    
    res.json({
      id: room.id,
      name: room.name,
      displayName: room.display_name,
      canRejoin
    });
  } catch (error) {
    console.error('Get room error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// ============ ERROR HANDLING ============

app.use((err, req, res, next) => {
  if (err && err.status && err.status < 500) {
    return res.status(err.status).json({ error: err.message });
  }
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ============ START SERVER ============

if (process.argv[1] === __filename) {
  app.listen(PORT, () => {
    console.log(`API listening on port ${PORT}`);
    console.log(`Database: ${db.dbPath}`);
    
    // Cleanup expired sessions on startup
    const cleaned = db.cleanupExpiredSessions();
    if (cleaned.changes > 0) {
      console.log(`Cleaned up ${cleaned.changes} expired sessions`);
    }
  });
}

export default app;
