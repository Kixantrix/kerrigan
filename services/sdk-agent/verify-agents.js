#!/usr/bin/env node
/**
 * Verification Script
 * Demonstrates the SDK agent personas implementation
 */

const { KERRIGAN_AGENTS, getAgentConfig, getAllAgentConfigs } = require('./dist/agents');

console.log('🎯 Kerrigan SDK Agent Personas Verification\n');
console.log('='.repeat(60));

// Show all configured agents
console.log('\n📋 Configured Agent Personas:\n');
const allConfigs = getAllAgentConfigs();
allConfigs.forEach((config, index) => {
  console.log(`${index + 1}. ${config.displayName}`);
  console.log(`   Name: ${config.name}`);
  console.log(`   Label: ${config.label}`);
  console.log(`   Prompt: ${config.promptFile}`);
  console.log(`   Tools: ${config.tools.length} custom tools`);
  config.tools.forEach(tool => {
    console.log(`      - ${tool.name}: ${tool.description.substring(0, 50)}...`);
  });
  console.log('');
});

console.log('='.repeat(60));

// Show role retrieval
console.log('\n🔍 Agent Configuration Retrieval:\n');
const roles = ['spec', 'architect', 'swe', 'deploy', 'security', 'triage'];
roles.forEach(role => {
  const config = getAgentConfig(role);
  if (config) {
    console.log(`✓ ${role} -> ${config.displayName} (${config.tools.length} tools)`);
  } else {
    console.log(`✗ ${role} -> Not found`);
  }
});

console.log('\n='.repeat(60));

// Show statistics
console.log('\n📊 Implementation Statistics:\n');
console.log(`Total Agent Personas: ${allConfigs.length}`);
console.log(`Total Unique Tools: ${new Set(allConfigs.flatMap(c => c.tools.map(t => t.name))).size}`);
console.log(`Average Tools per Agent: ${(allConfigs.reduce((sum, c) => sum + c.tools.length, 0) / allConfigs.length).toFixed(1)}`);

console.log('\n✅ Verification Complete!\n');
