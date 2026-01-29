/**
 * Tests for custom tools
 */

import { readConstitutionTool, readSpecTool, listArtifactsTool } from '../src/tools';
import * as fs from 'fs';
import * as path from 'path';

// Mock file system for testing
jest.mock('fs');

describe('Custom Tools', () => {
  const mockFs = fs as jest.Mocked<typeof fs>;

  beforeEach(() => {
    jest.clearAllMocks();
    // Default: assume we're in repo root
    jest.spyOn(process, 'cwd').mockReturnValue('/test/repo');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('readConstitutionTool', () => {
    it('should have correct metadata', () => {
      expect(readConstitutionTool.name).toBe('read_constitution');
      expect(readConstitutionTool.description).toContain('constitution');
      expect(readConstitutionTool.handler).toBeDefined();
    });

    it('should read constitution file when it exists', async () => {
      const mockContent = '# Constitution\n\nTest content';
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(mockContent);

      const result = await readConstitutionTool.handler();

      expect(result).toBe(mockContent);
      expect(mockFs.existsSync).toHaveBeenCalledWith('/test/repo/specs/constitution.md');
    });

    it('should return error message when file does not exist', async () => {
      mockFs.existsSync.mockReturnValue(false);

      const result = await readConstitutionTool.handler();

      expect(result).toContain('not found');
    });
  });

  describe('readSpecTool', () => {
    it('should have correct metadata', () => {
      expect(readSpecTool.name).toBe('read_spec');
      expect(readSpecTool.description).toContain('specification');
      expect(readSpecTool.handler).toBeDefined();
    });

    it('should read specific project spec when project provided', async () => {
      const mockContent = '# Spec\n\nProject spec';
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(mockContent);

      const result = await readSpecTool.handler({ project: 'my-project' });

      expect(result).toBe(mockContent);
      expect(mockFs.existsSync).toHaveBeenCalledWith(
        '/test/repo/specs/projects/my-project/spec.md'
      );
    });

    it('should search all projects when no project specified', async () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readdirSync.mockReturnValue([
        { name: 'project1', isDirectory: () => true },
        { name: 'project2', isDirectory: () => true },
      ] as any);
      mockFs.readFileSync.mockReturnValue('# Spec content');

      const result = await readSpecTool.handler({});

      expect(result).toContain('project1');
      expect(result).toContain('project2');
    });

    it('should handle missing specs directory', async () => {
      mockFs.existsSync.mockReturnValue(false);

      const result = await readSpecTool.handler({});

      expect(result).toContain('No specs/projects directory');
    });
  });

  describe('listArtifactsTool', () => {
    it('should have correct metadata', () => {
      expect(listArtifactsTool.name).toBe('list_artifacts');
      expect(listArtifactsTool.description).toContain('artifacts');
      expect(listArtifactsTool.handler).toBeDefined();
    });

    it('should list constitution as global artifact', async () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readdirSync.mockReturnValue([]);

      const result = await listArtifactsTool.handler({});

      expect(result).toContain('constitution');
      expect(result).toContain('specs/constitution.md');
    });

    it('should list project-specific artifacts when project provided', async () => {
      mockFs.existsSync.mockImplementation((path: any) => {
        return path.includes('constitution') || path.includes('spec.md');
      });

      const result = await listArtifactsTool.handler({ project: 'my-project' });

      expect(result).toContain('spec');
      expect(result).toContain('architecture');
      expect(result).toContain('plan');
    });

    it('should list all projects when no project specified', async () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readdirSync
        .mockReturnValueOnce([
          { name: 'project1', isDirectory: () => true },
        ] as any)
        .mockReturnValueOnce(['spec.md', 'plan.md'] as any);

      const result = await listArtifactsTool.handler({});

      expect(result).toContain('project1');
    });
  });
});
