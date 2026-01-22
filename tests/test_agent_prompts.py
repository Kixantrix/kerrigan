#!/usr/bin/env python3
"""Tests for agent prompt validation.

This test suite validates that all agent prompts follow expected structure,
include required sections, and properly reference artifact contracts.
"""

import re
import unittest
from pathlib import Path


class TestAgentPromptStructure(unittest.TestCase):
    """Test that agent prompts have required structural elements"""

    def setUp(self):
        """Load all agent role prompts"""
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"
        self.role_prompts = list(self.agents_dir.glob("role.*.md"))
        
        # Ensure we found some agent prompts
        self.assertGreater(len(self.role_prompts), 0, 
            "No agent role prompts found in .github/agents/")

    def test_all_agents_check_status_json(self):
        """Test that all agent prompts check status.json before starting work"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Check for status.json checking instructions
                self.assertIn("status.json", content,
                    f"{prompt_file.name} must mention checking status.json")
                
                # Check for blocked status handling
                self.assertIn("blocked", content.lower(),
                    f"{prompt_file.name} must handle blocked status")
                
                # Check for STOP instruction when blocked
                self.assertIn("STOP", content,
                    f"{prompt_file.name} must instruct agent to STOP when blocked")

    def test_all_agents_have_role_section(self):
        """Test that all agent prompts clearly define their role"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should have a "Your Role" or "Role" section
                self.assertTrue(
                    "## Your Role" in content or "## Role" in content,
                    f"{prompt_file.name} must have a 'Your Role' or 'Role' section"
                )

    def test_all_agents_specify_deliverables(self):
        """Test that all agent prompts specify deliverables or outputs"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should mention deliverables, outputs, or artifacts
                has_deliverables = any(term in content for term in [
                    "Deliverables",
                    "deliverables",
                    "Required Deliverables",
                    "artifacts",
                    "produce",
                    "create"
                ])
                
                self.assertTrue(has_deliverables,
                    f"{prompt_file.name} must specify deliverables or outputs")

    def test_all_agents_have_guidelines(self):
        """Test that all agent prompts include guidelines or principles"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should have guidelines, principles, standards, workflow, or checklist section
                has_guidance = any(term in content for term in [
                    "Guidelines",
                    "Principles",
                    "Standards",
                    "Approach",
                    "Workflow",
                    "Checklist",
                    "Best Practices"
                ])
                
                self.assertTrue(has_guidance,
                    f"{prompt_file.name} must include guidelines, principles, or workflow")

    def test_agent_prompts_are_markdown(self):
        """Test that all agent prompts use markdown format"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should have markdown headers (anywhere in the document)
                self.assertRegex(content, r'##?\s+\w+', 
                    f"{prompt_file.name} should use markdown format with headers")


class TestAgentPromptContent(unittest.TestCase):
    """Test specific content requirements for different agent types"""

    def setUp(self):
        """Load agent prompts"""
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"

    def test_spec_agent_mentions_required_sections(self):
        """Test that spec agent prompt mentions required spec.md sections"""
        spec_prompt = self.agents_dir / "role.spec.md"
        if not spec_prompt.exists():
            self.skipTest("Spec agent prompt not found")
        
        content = spec_prompt.read_text(encoding="utf-8")
        
        # Check for required spec.md sections
        required_sections = [
            "Goal",
            "Scope",
            "Non-goals",
            "Acceptance criteria"
        ]
        
        for section in required_sections:
            self.assertIn(section, content,
                f"Spec agent must mention required section: {section}")
        
        # Should mention acceptance-tests.md
        self.assertIn("acceptance-tests.md", content,
            "Spec agent must mention acceptance-tests.md deliverable")

    def test_swe_agent_emphasizes_testing(self):
        """Test that SWE agent prompt emphasizes testing"""
        swe_prompt = self.agents_dir / "role.swe.md"
        if not swe_prompt.exists():
            self.skipTest("SWE agent prompt not found")
        
        content = swe_prompt.read_text(encoding="utf-8")
        
        # Should emphasize testing
        test_keywords = ["test", "Test", "testing", "TDD"]
        test_count = sum(content.count(keyword) for keyword in test_keywords)
        
        self.assertGreater(test_count, 5,
            "SWE agent must emphasize testing (multiple mentions)")
        
        # Should mention linting
        self.assertIn("lint", content.lower(),
            "SWE agent must mention linting")

    def test_architect_agent_mentions_architecture_deliverables(self):
        """Test that architect agent mentions key architecture deliverables"""
        architect_prompt = self.agents_dir / "role.architect.md"
        if not architect_prompt.exists():
            self.skipTest("Architect agent prompt not found")
        
        content = architect_prompt.read_text(encoding="utf-8")
        
        # Should mention key deliverables
        deliverables = ["architecture.md", "plan.md"]
        
        for deliverable in deliverables:
            self.assertIn(deliverable, content,
                f"Architect agent must mention {deliverable}")

    def test_testing_agent_mentions_coverage(self):
        """Test that testing agent prompt mentions coverage"""
        testing_prompt = self.agents_dir / "role.testing.md"
        if not testing_prompt.exists():
            self.skipTest("Testing agent prompt not found")
        
        content = testing_prompt.read_text(encoding="utf-8")
        
        # Should mention coverage
        self.assertIn("coverage", content.lower(),
            "Testing agent must mention test coverage")
        
        # Should mention test-plan.md
        self.assertIn("test-plan.md", content,
            "Testing agent must mention test-plan.md")


class TestAgentPromptArtifactAlignment(unittest.TestCase):
    """Test that agent prompts align with artifact contracts"""

    def setUp(self):
        """Load artifact contract and agent prompts"""
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"
        self.artifact_contract = repo_root / "specs" / "kerrigan" / "020-artifact-contracts.md"
        
        if not self.artifact_contract.exists():
            self.fail("Artifact contract document not found")
        
        self.contract_content = self.artifact_contract.read_text(encoding="utf-8")

    def test_spec_agent_deliverables_match_contract(self):
        """Test that spec agent deliverables match artifact contract"""
        spec_prompt = self.agents_dir / "role.spec.md"
        if not spec_prompt.exists():
            self.skipTest("Spec agent prompt not found")
        
        content = spec_prompt.read_text(encoding="utf-8")
        
        # From artifact contract: spec agent should produce spec.md and acceptance-tests.md
        self.assertIn("spec.md", content,
            "Spec agent must mention spec.md deliverable")
        self.assertIn("acceptance-tests.md", content,
            "Spec agent must mention acceptance-tests.md deliverable")

    def test_architect_agent_deliverables_match_contract(self):
        """Test that architect agent deliverables match artifact contract"""
        architect_prompt = self.agents_dir / "role.architect.md"
        if not architect_prompt.exists():
            self.skipTest("Architect agent prompt not found")
        
        content = architect_prompt.read_text(encoding="utf-8")
        
        # From artifact contract: architect should produce architecture.md, plan.md, tasks.md, test-plan.md
        # Testing core deliverables that are always required
        required_deliverables = ["architecture.md", "plan.md", "tasks.md", "test-plan.md"]
        
        for deliverable in required_deliverables:
            self.assertIn(deliverable, content,
                f"Architect agent must mention {deliverable} deliverable")

    def test_deployment_agent_mentions_runbook(self):
        """Test that deployment agent mentions runbook.md"""
        deploy_prompt = self.agents_dir / "role.deployment.md"
        if not deploy_prompt.exists():
            self.skipTest("Deployment agent prompt not found")
        
        content = deploy_prompt.read_text(encoding="utf-8")
        
        # From artifact contract: deployment agent should produce runbook.md
        self.assertIn("runbook.md", content,
            "Deployment agent must mention runbook.md deliverable")


class TestAgentPromptExamples(unittest.TestCase):
    """Test that agent prompts include helpful examples"""

    def setUp(self):
        """Load agent prompts"""
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"
        self.role_prompts = list(self.agents_dir.glob("role.*.md"))

    def test_agents_include_examples_or_patterns(self):
        """Test that agent prompts include examples or common patterns"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should have examples, patterns, or common sections
                has_examples = any(term in content for term in [
                    "Example",
                    "example",
                    "Pattern",
                    "pattern",
                    "Common",
                    "```"  # Code block marker
                ])
                
                self.assertTrue(has_examples,
                    f"{prompt_file.name} should include examples or patterns")

    def test_agents_mention_common_mistakes(self):
        """Test that agent prompts warn about common mistakes"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should mention mistakes, avoid, or common errors
                has_warnings = any(term in content for term in [
                    "mistake",
                    "Mistake",
                    "avoid",
                    "Avoid",
                    "Don't",
                    "❌",
                    "✅"
                ])
                
                self.assertTrue(has_warnings,
                    f"{prompt_file.name} should warn about common mistakes")


class TestAgentPromptConsistency(unittest.TestCase):
    """Test consistency across all agent prompts"""

    def setUp(self):
        """Load all agent prompts"""
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"
        self.role_prompts = list(self.agents_dir.glob("role.*.md"))

    def test_all_agents_use_consistent_status_check_format(self):
        """Test that all agents use consistent format for status.json checking"""
        status_check_pattern = r'status\.json'
        
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should use consistent naming
                self.assertRegex(content, status_check_pattern,
                    f"{prompt_file.name} should reference status.json consistently")

    def test_all_agents_identify_themselves(self):
        """Test that all agents clearly identify their role at the start"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                lines = content.split('\n')
                
                # First few lines should identify the agent role
                header_section = '\n'.join(lines[:10])
                
                # Extract role name from filename (e.g., role.spec.md -> Spec)
                role_name = prompt_file.stem.replace('role.', '').title()
                
                # Should mention the role name or "Agent" in the header
                self.assertTrue(
                    role_name.lower() in header_section.lower() or 
                    "agent" in header_section.lower(),
                    f"{prompt_file.name} should identify its role early"
                )

    def test_prompt_file_naming_convention(self):
        """Test that agent prompt files follow naming convention"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                # Should follow role.{name}.md pattern
                self.assertRegex(prompt_file.name, r'^role\.\w+\.md$',
                    f"{prompt_file.name} should follow role.{{name}}.md naming convention")


class TestAgentPromptCompleteness(unittest.TestCase):
    """Test that all expected agents have prompts"""

    def setUp(self):
        """Set up expected agent list"""
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"

    def test_expected_agents_exist(self):
        """Test that all expected agent role prompts exist
        
        This is a test for CORE agents that are part of the standard workflow.
        If adding new core agents, update this list. Non-core or experimental
        agents don't need to be in this list.
        """
        expected_agents = [
            "role.spec.md",
            "role.architect.md",
            "role.swe.md",
            "role.testing.md",
            "role.debugging.md",
            "role.deployment.md",
            "role.security.md"
        ]
        
        for agent_file in expected_agents:
            agent_path = self.agents_dir / agent_file
            self.assertTrue(agent_path.exists(),
                f"Expected agent prompt not found: {agent_file}")

    def test_agents_readme_exists(self):
        """Test that agents directory has a README"""
        readme = self.agents_dir / "README.md"
        self.assertTrue(readme.exists(),
            "Agents directory must have a README.md")

    def test_agents_readme_documents_all_roles(self):
        """Test that README documents all agent roles"""
        readme = self.agents_dir / "README.md"
        if not readme.exists():
            self.skipTest("README not found")
        
        readme_content = readme.read_text(encoding="utf-8")
        role_prompts = list(self.agents_dir.glob("role.*.md"))
        
        for prompt_file in role_prompts:
            # Extract role name (e.g., role.spec.md -> spec)
            role_name = prompt_file.stem.replace('role.', '')
            
            # README should mention this role
            self.assertIn(role_name, readme_content.lower(),
                f"README should document the {role_name} agent")


class TestAgentSignatureInPrompts(unittest.TestCase):
    """Test that agent prompts include signature instructions"""

    def setUp(self):
        """Load all agent role prompts"""
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"
        self.role_prompts = list(self.agents_dir.glob("role.*.md"))
        
        self.assertGreater(len(self.role_prompts), 0,
            "No agent role prompts found in .github/agents/")

    def test_all_agents_have_signature_section(self):
        """Test that all agent prompts include agent signature section"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should have an "Agent Signature" section
                self.assertIn("Agent Signature", content,
                    f"{prompt_file.name} must have an 'Agent Signature' section")

    def test_all_agents_mention_signature_format(self):
        """Test that all agent prompts mention AGENT_SIGNATURE format"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should mention the signature comment format
                self.assertIn("AGENT_SIGNATURE", content,
                    f"{prompt_file.name} must mention AGENT_SIGNATURE format")

    def test_all_agents_reference_correct_role(self):
        """Test that agent prompts reference their correct role in signature examples"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Extract expected role from filename (e.g., role.spec.md -> role:spec)
                role_name = prompt_file.stem.replace('role.', '')
                expected_role = f"role:{role_name}"
                
                # Signature section should reference the correct role
                if "Agent Signature" in content:
                    signature_section_start = content.find("Agent Signature")
                    signature_section = content[signature_section_start:signature_section_start + 500]
                    
                    self.assertIn(expected_role, signature_section,
                        f"{prompt_file.name} signature section should reference {expected_role}")

    def test_all_agents_mention_audit_tool(self):
        """Test that agent prompts mention the agent_audit.py tool"""
        for prompt_file in self.role_prompts:
            with self.subTest(agent=prompt_file.name):
                content = prompt_file.read_text(encoding="utf-8")
                
                # Should mention the audit tool for generating signatures
                self.assertIn("agent_audit.py", content,
                    f"{prompt_file.name} should mention agent_audit.py tool")


if __name__ == "__main__":
    unittest.main()
