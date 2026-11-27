/**
 * Authentication middleware for VHS Video Stack
 */

import * as db from './db.js';

/**
 * Extract session ID from request
 * Checks: Authorization header, cookie, query param
 */
export function extractSessionId(req) {
  // Check Authorization header: "Bearer sess_xxxxx"
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.slice(7);
  }
  
  return null;
}

/**
 * Get authenticated session and user from request
 */
export function getSessionFromRequest(req) {
  const sessionId = extractSessionId(req);
  if (!sessionId) return null;
  
  const session = db.getSessionById(sessionId);
  if (!session) return null;
  
  // Update last used time
  db.updateSessionLastUsed(sessionId);
  
  return {
    id: session.id,
    userId: session.user_id,
    user: {
      id: session.user_id,
      name: session.user_name,
      email: session.user_email,
      isAdmin: session.is_admin === 1,
      canCreateRooms: session.can_create_rooms === 1
    },
    createdAt: session.created_at,
    lastUsed: session.last_used,
    expiresAt: session.expires_at
  };
}

/**
 * Middleware: Require any authenticated user
 */
export function requireAuth(req, res, next) {
  const session = getSessionFromRequest(req);
  
  if (!session) {
    return res.status(401).json({ 
      error: 'Authentication required',
      code: 'UNAUTHORIZED'
    });
  }
  
  req.session = session;
  req.user = session.user;
  next();
}

/**
 * Middleware: Require admin user
 */
export function requireAdmin(req, res, next) {
  const session = getSessionFromRequest(req);
  
  if (!session) {
    return res.status(401).json({ 
      error: 'Authentication required',
      code: 'UNAUTHORIZED'
    });
  }
  
  if (!session.user.isAdmin) {
    db.addAuditLog({
      eventType: 'admin_access_denied',
      userId: session.userId,
      sessionId: session.id,
      ipAddress: req.ip,
      userAgent: req.get('User-Agent')
    });
    
    return res.status(403).json({ 
      error: 'Admin access required',
      code: 'FORBIDDEN'
    });
  }
  
  req.session = session;
  req.user = session.user;
  next();
}

/**
 * Middleware: Require room creation permission (admin or canCreateRooms)
 */
export function requireRoomCreator(req, res, next) {
  const session = getSessionFromRequest(req);
  
  if (!session) {
    return res.status(401).json({ 
      error: 'Authentication required',
      code: 'UNAUTHORIZED'
    });
  }
  
  if (!session.user.isAdmin && !session.user.canCreateRooms) {
    db.addAuditLog({
      eventType: 'room_creation_denied',
      userId: session.userId,
      sessionId: session.id,
      ipAddress: req.ip,
      userAgent: req.get('User-Agent')
    });
    
    return res.status(403).json({ 
      error: 'Room creation permission required',
      code: 'FORBIDDEN'
    });
  }
  
  req.session = session;
  req.user = session.user;
  next();
}

/**
 * Middleware: Optionally authenticate (doesn't fail if no session)
 */
export function optionalAuth(req, res, next) {
  const session = getSessionFromRequest(req);
  
  if (session) {
    req.session = session;
    req.user = session.user;
  }
  
  next();
}

/**
 * Get client IP address from request
 */
export function getClientIp(req) {
  return req.headers['x-forwarded-for']?.split(',')[0].trim() || 
         req.headers['x-real-ip'] || 
         req.socket?.remoteAddress || 
         req.ip;
}

export default {
  extractSessionId,
  getSessionFromRequest,
  requireAuth,
  requireAdmin,
  requireRoomCreator,
  optionalAuth,
  getClientIp
};
