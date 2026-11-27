/**
 * Admin routes for VHS Video Stack
 * All routes require admin authentication
 */

import express from './lib/express.js';
import * as db from './db.js';
import { requireAdmin, getClientIp } from './middleware.js';

const router = express.Router();

// All admin routes require admin authentication
router.use(requireAdmin);

// ============ ROOM MANAGEMENT ============

/**
 * GET /admin/rooms
 * List all rooms (including disabled)
 */
router.get('/rooms', (req, res) => {
  try {
    const rooms = db.getAllRooms();
    res.json({
      rooms: rooms.map(r => ({
        id: r.id,
        name: r.name,
        displayName: r.display_name,
        accessCode: r.access_code,
        createdBy: r.created_by,
        enabled: r.enabled === 1,
        createdAt: r.created_at,
        updatedAt: r.updated_at
      }))
    });
  } catch (error) {
    console.error('List rooms error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /admin/rooms
 * Create a new room
 */
router.post('/rooms', (req, res) => {
  try {
    const { name, displayName, accessCode } = req.body;
    
    if (!name) {
      return res.status(400).json({ error: 'Room name is required' });
    }
    
    // Check if room name already exists
    const existing = db.getRoomByName(name);
    if (existing) {
      return res.status(409).json({ error: 'Room name already exists' });
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
      room: {
        id: room.id,
        name: room.name,
        displayName: room.display_name,
        accessCode: room.access_code,
        createdBy: room.created_by,
        enabled: room.enabled === 1,
        createdAt: room.created_at
      }
    });
  } catch (error) {
    console.error('Create room error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * PUT /admin/rooms/:id
 * Update a room
 */
router.put('/rooms/:id', (req, res) => {
  try {
    const { id } = req.params;
    const { name, displayName, accessCode, enabled } = req.body;
    
    const existing = db.getRoomById(id);
    if (!existing) {
      return res.status(404).json({ error: 'Room not found' });
    }
    
    // Check if new name conflicts
    if (name && name !== existing.name) {
      const nameRoom = db.getRoomByName(name);
      if (nameRoom) {
        return res.status(409).json({ error: 'Room name already exists' });
      }
    }
    
    const room = db.updateRoom(id, { name, displayName, accessCode, enabled });
    
    db.addAuditLog({
      eventType: 'room_updated',
      userId: req.user.id,
      roomId: id,
      details: { changes: { name, displayName, accessCode, enabled } },
      ipAddress: getClientIp(req),
      userAgent: req.get('User-Agent')
    });
    
    res.json({
      room: {
        id: room.id,
        name: room.name,
        displayName: room.display_name,
        accessCode: room.access_code,
        createdBy: room.created_by,
        enabled: room.enabled === 1,
        updatedAt: room.updated_at
      }
    });
  } catch (error) {
    console.error('Update room error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * DELETE /admin/rooms/:id
 * Delete a room
 */
router.delete('/rooms/:id', (req, res) => {
  try {
    const { id } = req.params;
    
    const room = db.getRoomById(id);
    if (!room) {
      return res.status(404).json({ error: 'Room not found' });
    }
    
    db.deleteRoom(id);
    
    db.addAuditLog({
      eventType: 'room_deleted',
      userId: req.user.id,
      roomId: id,
      details: { roomName: room.name },
      ipAddress: getClientIp(req),
      userAgent: req.get('User-Agent')
    });
    
    res.json({ success: true });
  } catch (error) {
    console.error('Delete room error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /admin/rooms/:id/regenerate-code
 * Generate a new access code for a room
 */
router.post('/rooms/:id/regenerate-code', (req, res) => {
  try {
    const { id } = req.params;
    
    const room = db.getRoomById(id);
    if (!room) {
      return res.status(404).json({ error: 'Room not found' });
    }
    
    const newCode = db.generatePassphrase();
    const updated = db.updateRoom(id, { accessCode: newCode });
    
    db.addAuditLog({
      eventType: 'room_code_regenerated',
      userId: req.user.id,
      roomId: id,
      details: { roomName: room.name },
      ipAddress: getClientIp(req),
      userAgent: req.get('User-Agent')
    });
    
    res.json({
      room: {
        id: updated.id,
        name: updated.name,
        accessCode: updated.access_code
      }
    });
  } catch (error) {
    console.error('Regenerate code error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});


export default router;
