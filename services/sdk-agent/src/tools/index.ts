/**
 * Tools Index
 * Export all custom tools for Kerrigan agents
 */

import { readConstitutionTool } from './read-constitution';
import { readSpecTool } from './read-spec';
import { listArtifactsTool } from './list-artifacts';

export { readConstitutionTool, readSpecTool, listArtifactsTool };

// Collect all tools in an array for easy registration
export const ALL_TOOLS = [
  readConstitutionTool,
  readSpecTool,
  listArtifactsTool,
];
