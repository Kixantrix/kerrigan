"""Storage layer for task persistence."""

import json
import os
from pathlib import Path
from typing import List, Dict


class TaskStorage:
    """Handle file I/O and data persistence."""

    def __init__(self, storage_path: str = None):
        """Initialize storage.

        Args:
            storage_path: Path to storage file (default: ~/.task-tracker/tasks.json)
        """
        if storage_path is None:
            home = Path.home()
            storage_dir = home / ".task-tracker"
            storage_path = storage_dir / "tasks.json"
        
        self.storage_path = Path(storage_path)
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)

    def load(self) -> List[Dict]:
        """Load tasks from storage file.

        Returns:
            List of task dictionaries, empty list if file doesn't exist
        """
        if not self.storage_path.exists():
            return []
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    # Corrupted data, backup and reset
                    self._backup_corrupted()
                    return []
                return data
        except json.JSONDecodeError:
            # Corrupted JSON, backup and reset
            self._backup_corrupted()
            return []
        except (IOError, OSError) as e:
            raise IOError(f"Cannot read storage file: {e}")

    def save(self, tasks: List[Dict]) -> None:
        """Save tasks to storage file.

        Args:
            tasks: List of task dictionaries to save
        """
        try:
            # Write to temp file first for atomic write
            temp_path = self.storage_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(tasks, f, indent=2)
            
            # Atomic replace
            temp_path.replace(self.storage_path)
            
            # Set permissions
            os.chmod(self.storage_path, 0o644)
        except (IOError, OSError) as e:
            raise IOError(f"Cannot write storage file: {e}")

    def _backup_corrupted(self) -> None:
        """Backup corrupted storage file."""
        if self.storage_path.exists():
            backup_path = self.storage_path.with_suffix('.corrupted')
            try:
                self.storage_path.rename(backup_path)
            except (IOError, OSError):
                # If backup fails, just remove the corrupted file
                self.storage_path.unlink(missing_ok=True)
