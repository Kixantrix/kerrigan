#!/usr/bin/env node

/**
 * Minimal SDK Authentication Test
 * 
 * Tests ONLY whether GitHub App tokens can authenticate the SDK.
 * Does NOT attempt to send prompts or create files.
 */

import { config } from 'dotenv';
import { App } from 'octokit';
import { readFileSync } from 'fs';

config();

const TIMEOUT_MS = 30000; // 30 second timeout

async function runTest() {
  console.log('\n=== Minimal SDK Auth Test ===\n');
  
  // Step 1: Get GitHub App token
  console.log('[1/3] Getting GitHub App installation token...');
  
  const privateKey = readFileSync(process.env.PRIVATE_KEY_PATH, 'utf-8');
  const app = new App({
    appId: process.env.APP_ID,
    privateKey: privateKey
  });
  
  const octokit = await app.getInstallationOctokit(parseInt(process.env.INSTALLATION_ID));
  const { token } = await octokit.auth({ type: 'installation' });
  
  console.log(`✅ Got installation token: ${token.substring(0, 10)}...`);
  
  // Step 2: Set token for SDK
  console.log('\n[2/3] Setting COPILOT_GITHUB_TOKEN...');
  process.env.COPILOT_GITHUB_TOKEN = token;
  console.log('✅ Token set');
  
  // Step 3: Try to import and initialize SDK with timeout
  console.log('\n[3/3] Testing SDK initialization (30s timeout)...');
  console.log('    This will spawn the Copilot CLI in server mode...');
  
  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => reject(new Error('TIMEOUT: SDK initialization took too long')), TIMEOUT_MS);
  });
  
  const sdkPromise = (async () => {
    const { CopilotClient } = await import('@github/copilot-sdk');
    console.log('    SDK imported');
    
    const client = new CopilotClient();
    console.log('    Client created, starting...');
    
    await client.start();
    console.log('    Client started!');
    
    // Immediately stop - we just want to test auth
    await client.stop();
    console.log('    Client stopped');
    
    return true;
  })();
  
  try {
    await Promise.race([sdkPromise, timeoutPromise]);
    
    console.log('\n' + '='.repeat(50));
    console.log('✅ SUCCESS: GitHub App tokens work with SDK!');
    console.log('='.repeat(50));
    console.log('\nThis validates the SDK architecture proposal.');
    console.log('Autonomous agent triggering IS possible.\n');
    
    process.exit(0);
  } catch (error) {
    console.log('\n' + '='.repeat(50));
    
    if (error.message.includes('TIMEOUT')) {
      console.log('⚠️  TIMEOUT: SDK hung during initialization');
      console.log('='.repeat(50));
      console.log('\nPossible causes:');
      console.log('  - Copilot CLI waiting for interactive login');
      console.log('  - Network issues connecting to GitHub');
      console.log('  - Token not accepted by CLI\n');
      console.log('This suggests App tokens may NOT work seamlessly.');
    } else if (error.message.includes('authentication') || error.message.includes('401')) {
      console.log('❌ AUTH FAILED: GitHub App tokens do NOT work');
      console.log('='.repeat(50));
      console.log('\nThe SDK requires user OAuth, not App tokens.');
      console.log('Autonomous triggering is NOT possible with current SDK.\n');
    } else {
      console.log('❌ ERROR:', error.message);
      console.log('='.repeat(50));
      console.error(error);
    }
    
    process.exit(1);
  }
}

runTest().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
