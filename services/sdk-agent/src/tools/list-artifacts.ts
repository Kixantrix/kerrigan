/**
 * Tool: list_artifacts
 * List existing project artifacts (specs, plans, ADRs, etc.)
 */

import { z } from 'zod';
import * as fs from 'fs';
import * as path from 'path';

interface ArtifactInfo {
  type: string;
  path: string;
  exists: boolean;
}

export const listArtifactsTool = {
  name: 'list_artifacts',
  description: 'List existing project artifacts including specs, plans, architecture docs, ADRs, and runbooks',
  parameters: z.object({
    project: z.string().optional().describe('Project name to list artifacts for (defaults to all)'),
  }),
  handler: async (params: { project?: string }): Promise<string> => {
    const repoPath = process.cwd();
    const artifacts: ArtifactInfo[] = [];
    
    try {
      // Constitution (global)
      const constitutionPath = path.join(repoPath, 'specs/constitution.md');
      artifacts.push({
        type: 'constitution',
        path: 'specs/constitution.md',
        exists: fs.existsSync(constitutionPath),
      });
      
      // If specific project requested
      if (params.project) {
        const projectPath = path.join(repoPath, 'specs/projects', params.project);
        
        const projectArtifacts = [
          { type: 'spec', file: 'spec.md' },
          { type: 'architecture', file: 'architecture.md' },
          { type: 'plan', file: 'plan.md' },
          { type: 'runbook', file: 'runbook.md' },
          { type: 'test-plan', file: 'test-plan.md' },
        ];
        
        for (const artifact of projectArtifacts) {
          const artifactPath = path.join(projectPath, artifact.file);
          artifacts.push({
            type: artifact.type,
            path: `specs/projects/${params.project}/${artifact.file}`,
            exists: fs.existsSync(artifactPath),
          });
        }
        
        // Check for ADRs
        const adrsPath = path.join(projectPath, 'adrs');
        if (fs.existsSync(adrsPath)) {
          const adrFiles = fs.readdirSync(adrsPath)
            .filter(f => f.endsWith('.md'));
          
          for (const adrFile of adrFiles) {
            artifacts.push({
              type: 'adr',
              path: `specs/projects/${params.project}/adrs/${adrFile}`,
              exists: true,
            });
          }
        }
      } else {
        // List all projects
        const projectsPath = path.join(repoPath, 'specs/projects');
        if (fs.existsSync(projectsPath)) {
          const projects = fs.readdirSync(projectsPath, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory());
          
          for (const project of projects) {
            const projectPath = path.join(projectsPath, project.name);
            const projectFiles = fs.readdirSync(projectPath);
            
            for (const file of projectFiles) {
              if (file.endsWith('.md')) {
                const fileType = file.replace('.md', '');
                artifacts.push({
                  type: fileType,
                  path: `specs/projects/${project.name}/${file}`,
                  exists: true,
                });
              }
            }
            
            // Check for ADRs
            const adrsPath = path.join(projectPath, 'adrs');
            if (fs.existsSync(adrsPath)) {
              const adrFiles = fs.readdirSync(adrsPath)
                .filter(f => f.endsWith('.md'));
              artifacts.push({
                type: 'adrs',
                path: `specs/projects/${project.name}/adrs/ (${adrFiles.length} files)`,
                exists: true,
              });
            }
          }
        }
      }
      
      // Format output
      const existing = artifacts.filter(a => a.exists);
      const missing = artifacts.filter(a => !a.exists);
      
      let output = '# Existing Artifacts\n\n';
      
      if (existing.length > 0) {
        output += '## Available:\n';
        for (const artifact of existing) {
          output += `- [${artifact.type}] ${artifact.path}\n`;
        }
      }
      
      if (missing.length > 0) {
        output += '\n## Missing:\n';
        for (const artifact of missing) {
          output += `- [${artifact.type}] ${artifact.path}\n`;
        }
      }
      
      if (existing.length === 0 && missing.length === 0) {
        output += 'No artifacts found.\n';
      }
      
      return output;
    } catch (error: any) {
      return `Error listing artifacts: ${error.message}`;
    }
  },
};
