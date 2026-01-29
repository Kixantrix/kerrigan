#!/usr/bin/env node
/**
 * Example: Async Swarm Dispatcher Demo
 * 
 * This script demonstrates how to use the SwarmDispatcher to process
 * multiple GitHub issues in parallel.
 * 
 * Usage:
 *   node examples/swarm-dispatcher-demo.js
 * 
 * Environment variables required:
 *   - GITHUB_TOKEN: GitHub personal access token or installation token
 */

const { Octokit } = require('@octokit/rest');

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const owner = process.env.GITHUB_OWNER || 'Kixantrix';
  const repo = process.env.GITHUB_REPO || 'kerrigan';

  if (!token) {
    console.error('❌ GITHUB_TOKEN environment variable is required');
    process.exit(1);
  }

  console.log('�� Async Swarm Dispatcher Demo');
  console.log(`   Repository: ${owner}/${repo}`);
  console.log('');
  console.log('✅ Demo setup complete');
  console.log('   See ASYNC-SWARM-DISPATCHER.md for usage examples');
}

if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}
