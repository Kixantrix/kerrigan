/**
 * Tool: read_spec
 * Read project specification file
 */

import { z } from 'zod';
import * as fs from 'fs';
import * as path from 'path';

export const readSpecTool = {
  name: 'read_spec',
  description: 'Read project specification from specs/projects/{project}/spec.md',
  parameters: z.object({
    project: z.string().optional().describe('Project name/directory (defaults to searching for any spec.md)'),
  }),
  handler: async (params: { project?: string }): Promise<string> => {
    const repoPath = process.cwd();
    
    try {
      // If project name provided, look for specific project
      if (params.project) {
        const specPath = path.join(repoPath, 'specs/projects', params.project, 'spec.md');
        if (fs.existsSync(specPath)) {
          return fs.readFileSync(specPath, 'utf-8');
        }
        return `Spec not found for project: ${params.project}`;
      }
      
      // Otherwise, search for any spec.md in specs/projects/
      const projectsPath = path.join(repoPath, 'specs/projects');
      if (!fs.existsSync(projectsPath)) {
        return 'No specs/projects directory found';
      }
      
      const projects = fs.readdirSync(projectsPath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory());
      
      const specs: string[] = [];
      for (const project of projects) {
        const specPath = path.join(projectsPath, project.name, 'spec.md');
        if (fs.existsSync(specPath)) {
          const content = fs.readFileSync(specPath, 'utf-8');
          specs.push(`## Project: ${project.name}\n\n${content}`);
        }
      }
      
      if (specs.length === 0) {
        return 'No spec.md files found in specs/projects/';
      }
      
      return specs.join('\n\n---\n\n');
    } catch (error: any) {
      return `Error reading spec: ${error.message}`;
    }
  },
};
