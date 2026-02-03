/**
 * Tests for prompt loader utility
 */

import { loadPrompt, buildSystemMessage } from '../src/agents/prompt-loader';
import * as fs from 'fs';

jest.mock('fs');

describe('Prompt Loader', () => {
  const mockFs = fs as jest.Mocked<typeof fs>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('loadPrompt', () => {
    it('should load prompt from prompts directory', () => {
      const mockContent = '# Test Prompt\n\nContent';
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(mockContent);

      const result = loadPrompt('test.md', '/repo');

      expect(mockFs.existsSync).toHaveBeenCalledWith('/repo/prompts/test.md');
      expect(result).toBe(mockContent);
    });

    it('should fallback to .github/agents directory', () => {
      const mockContent = '# Agent Prompt';
      mockFs.existsSync.mockImplementation((path: any) => {
        return path.includes('.github/agents');
      });
      mockFs.readFileSync.mockReturnValue(mockContent);

      const result = loadPrompt('test.md', '/repo');

      expect(mockFs.existsSync).toHaveBeenCalledWith('/repo/prompts/test.md');
      expect(mockFs.existsSync).toHaveBeenCalledWith('/repo/.github/agents/test.md');
      expect(result).toBe(mockContent);
    });

    it('should return warning message when file not found', () => {
      mockFs.existsSync.mockReturnValue(false);

      const result = loadPrompt('missing.md', '/repo');

      expect(result).toContain('not found');
    });

    it('should handle file read errors gracefully', () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockImplementation(() => {
        throw new Error('Permission denied');
      });

      const result = loadPrompt('test.md', '/repo');

      expect(result).toContain('Error loading prompt');
      expect(result).toContain('Permission denied');
    });
  });

  describe('buildSystemMessage', () => {
    it('should wrap prompt in kerrigan_agent tags', () => {
      const prompt = 'You are a test agent.';
      const result = buildSystemMessage('test', prompt);

      expect(result).toContain('<kerrigan_agent role="test">');
      expect(result).toContain('You are a test agent.');
      expect(result).toContain('</kerrigan_agent>');
    });

    it('should include constitution when provided', () => {
      const prompt = 'You are a spec agent.';
      const constitution = '# Constitution\n\nPrinciples';
      
      const result = buildSystemMessage('spec', prompt, constitution);

      expect(result).toContain('<constitution>');
      expect(result).toContain('# Constitution');
      expect(result).toContain('</constitution>');
    });

    it('should work without constitution', () => {
      const prompt = 'You are an architect agent.';
      
      const result = buildSystemMessage('architect', prompt);

      expect(result).toContain('You are an architect agent.');
      expect(result).not.toContain('<constitution>');
    });

    it('should properly format multi-line prompts', () => {
      const prompt = 'Line 1\nLine 2\nLine 3';
      
      const result = buildSystemMessage('swe', prompt);

      expect(result).toContain('Line 1\nLine 2\nLine 3');
    });
  });
});
