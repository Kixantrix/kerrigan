"""
Basic tests for Task Tracker CLI.

This is a simplified test suite to demonstrate the structure.
In a real project, this would have comprehensive coverage.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from task_tracker.auth import AuthManager
from task_tracker.tasks import TaskManager


class TestAuth(unittest.TestCase):
    """Test authentication functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_home = Path.home()
        # Mock home directory for testing
        AuthManager.__init__.__globals__['Path'].home = lambda: self.test_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_register_user(self):
        """Test user registration."""
        auth = AuthManager()
        result = auth.register_user("testuser", "password123")
        self.assertTrue(result)
    
    def test_register_duplicate_user(self):
        """Test registering duplicate user."""
        auth = AuthManager()
        auth.register_user("testuser", "password123")
        result = auth.register_user("testuser", "password456")
        self.assertFalse(result)
    
    def test_login_success(self):
        """Test successful login."""
        auth = AuthManager()
        auth.register_user("testuser", "password123")
        result = auth.login("testuser", "password123")
        self.assertTrue(result)
    
    def test_login_failure(self):
        """Test login with wrong password."""
        auth = AuthManager()
        auth.register_user("testuser", "password123")
        result = auth.login("testuser", "wrongpassword")
        self.assertFalse(result)


class TestTaskManager(unittest.TestCase):
    """Test task management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_home = Path.home()
        TaskManager.__init__.__globals__['Path'].home = lambda: self.test_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_add_task(self):
        """Test adding a task."""
        mgr = TaskManager("testuser")
        task_id = mgr.add_task("Test task", "high")
        self.assertEqual(task_id, 1)
    
    def test_list_tasks(self):
        """Test listing tasks."""
        mgr = TaskManager("testuser")
        mgr.add_task("Task 1", "high")
        mgr.add_task("Task 2", "low")
        tasks = mgr.list_tasks()
        self.assertEqual(len(tasks), 2)
    
    def test_complete_task(self):
        """Test completing a task."""
        mgr = TaskManager("testuser")
        task_id = mgr.add_task("Test task", "medium")
        result = mgr.complete_task(task_id)
        self.assertTrue(result)
        tasks = mgr.list_tasks(status_filter="completed")
        self.assertEqual(len(tasks), 1)
    
    def test_delete_task(self):
        """Test deleting a task."""
        mgr = TaskManager("testuser")
        task_id = mgr.add_task("Test task", "medium")
        result = mgr.delete_task(task_id)
        self.assertTrue(result)
        tasks = mgr.list_tasks()
        self.assertEqual(len(tasks), 0)


if __name__ == "__main__":
    unittest.main()
