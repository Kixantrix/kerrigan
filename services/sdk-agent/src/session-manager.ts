/**
 * SessionManager
 * Manages the lifecycle and registry of SDK sessions
 */

import { SessionInfo, SessionState } from './types';
import * as fs from 'fs';
import * as path from 'path';

export class SessionManager {
  private sessions: Map<string, SessionInfo> = new Map();
  private persistencePath?: string;

  constructor(persistencePath?: string) {
    this.persistencePath = persistencePath;
    if (persistencePath) {
      this.loadState();
    }
  }

  /**
   * Register a new session
   */
  registerSession(sessionInfo: SessionInfo): void {
    console.log(`📝 Registering session: ${sessionInfo.sessionId} for issue #${sessionInfo.issueNumber}`);
    this.sessions.set(sessionInfo.sessionId, sessionInfo);
    this.persistState();
  }

  /**
   * Update session state
   */
  updateSessionState(sessionId: string, state: SessionState, error?: string): void {
    const session = this.sessions.get(sessionId);
    if (!session) {
      console.warn(`⚠️  Session not found: ${sessionId}`);
      return;
    }

    session.state = state;
    session.updatedAt = new Date();
    
    if (error) {
      session.error = error;
    }

    if (state === SessionState.COMPLETED || state === SessionState.FAILED) {
      session.completedAt = new Date();
    }

    console.log(`🔄 Session ${sessionId} state updated: ${state}`);
    this.persistState();
  }

  /**
   * Get session by ID
   */
  getSession(sessionId: string): SessionInfo | undefined {
    return this.sessions.get(sessionId);
  }

  /**
   * Get session by issue number
   */
  getSessionByIssue(issueNumber: number): SessionInfo | undefined {
    for (const session of this.sessions.values()) {
      if (session.issueNumber === issueNumber) {
        return session;
      }
    }
    return undefined;
  }

  /**
   * Get all sessions
   */
  getAllSessions(): SessionInfo[] {
    return Array.from(this.sessions.values());
  }

  /**
   * Get active sessions (not completed or failed)
   */
  getActiveSessions(): SessionInfo[] {
    return this.getAllSessions().filter(
      (s) => s.state !== SessionState.COMPLETED && s.state !== SessionState.FAILED
    );
  }

  /**
   * Remove a session from registry
   */
  removeSession(sessionId: string): void {
    console.log(`🗑️  Removing session: ${sessionId}`);
    this.sessions.delete(sessionId);
    this.persistState();
  }

  /**
   * Cleanup completed and failed sessions
   */
  cleanupCompletedSessions(): void {
    const toRemove: string[] = [];
    for (const [sessionId, session] of this.sessions.entries()) {
      if (session.state === SessionState.COMPLETED || session.state === SessionState.FAILED) {
        toRemove.push(sessionId);
      }
    }

    toRemove.forEach((sessionId) => this.removeSession(sessionId));
    console.log(`🧹 Cleaned up ${toRemove.length} completed sessions`);
  }

  /**
   * Get session count
   */
  getSessionCount(): number {
    return this.sessions.size;
  }

  /**
   * Persist state to disk
   */
  private persistState(): void {
    if (!this.persistencePath) {
      return;
    }

    try {
      const data = JSON.stringify(
        Array.from(this.sessions.entries()).map(([id, info]) => ({
          id,
          info: {
            ...info,
            createdAt: info.createdAt.toISOString(),
            updatedAt: info.updatedAt.toISOString(),
            completedAt: info.completedAt?.toISOString(),
          },
        })),
        null,
        2
      );

      const dir = path.dirname(this.persistencePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      fs.writeFileSync(this.persistencePath, data, 'utf-8');
    } catch (error) {
      console.error('❌ Failed to persist session state:', error);
    }
  }

  /**
   * Load state from disk
   */
  private loadState(): void {
    if (!this.persistencePath || !fs.existsSync(this.persistencePath)) {
      return;
    }

    try {
      const data = fs.readFileSync(this.persistencePath, 'utf-8');
      const entries = JSON.parse(data);

      for (const entry of entries) {
        const info: SessionInfo = {
          ...entry.info,
          createdAt: new Date(entry.info.createdAt),
          updatedAt: new Date(entry.info.updatedAt),
          completedAt: entry.info.completedAt ? new Date(entry.info.completedAt) : undefined,
        };
        this.sessions.set(entry.id, info);
      }

      console.log(`✅ Loaded ${this.sessions.size} sessions from disk`);
    } catch (error) {
      console.error('❌ Failed to load session state:', error);
    }
  }

  /**
   * Clear all sessions
   */
  clear(): void {
    this.sessions.clear();
    this.persistState();
    console.log('🧹 All sessions cleared');
  }
}
