/**
 * Tool: read_constitution
 * Read Kerrigan constitution principles
 */

import { z } from 'zod';
import * as fs from 'fs';
import * as path from 'path';

// Simple tool definition compatible with SDK
export const readConstitutionTool = {
  name: 'read_constitution',
  description: 'Read Kerrigan constitution principles that define non-negotiable standards for all work',
  parameters: z.object({}),
  handler: async (): Promise<string> => {
    const repoPath = process.cwd();
    const constitutionPath = path.join(repoPath, 'specs/constitution.md');
    
    try {
      if (fs.existsSync(constitutionPath)) {
        return fs.readFileSync(constitutionPath, 'utf-8');
      }
      
      return 'Constitution not found in specs/constitution.md';
    } catch (error: any) {
      return `Error reading constitution: ${error.message}`;
    }
  },
};
