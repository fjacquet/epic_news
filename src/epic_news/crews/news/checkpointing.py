"""
Checkpointing utilities for the news crew to handle timeouts and resume progress.
"""
import os
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path

class CheckpointManager:
    """
    Manages checkpoints for CrewAI tasks to allow resuming after timeouts.
    """
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        """
        Initialize the checkpoint manager.
        
        Args:
            checkpoint_dir: Directory to store checkpoints
        """
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(self, task_id: str, data: Dict[str, Any]) -> None:
        """
        Save a checkpoint for a specific task.
        
        Args:
            task_id: Unique identifier for the task
            data: Data to save in the checkpoint
        """
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{task_id}.json")
        
        # Add timestamp to track when the checkpoint was created
        data["timestamp"] = time.time()
        
        with open(checkpoint_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Checkpoint saved for task {task_id}")
    
    def load_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a checkpoint for a specific task if it exists.
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            The checkpoint data or None if no checkpoint exists
        """
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{task_id}.json")
        
        if not os.path.exists(checkpoint_path):
            return None
            
        try:
            with open(checkpoint_path, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded checkpoint for task {task_id} from {time.ctime(data.get('timestamp', 0))}")
                return data
        except Exception as e:
            print(f"❌ Error loading checkpoint for task {task_id}: {str(e)}")
            return None
    
    def checkpoint_exists(self, task_id: str) -> bool:
        """
        Check if a checkpoint exists for a specific task.
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            True if a checkpoint exists, False otherwise
        """
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{task_id}.json")
        return os.path.exists(checkpoint_path)
    
    def clear_checkpoint(self, task_id: str) -> None:
        """
        Clear a checkpoint for a specific task.
        
        Args:
            task_id: Unique identifier for the task
        """
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{task_id}.json")
        
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            print(f"✅ Cleared checkpoint for task {task_id}")
    
    def clear_all_checkpoints(self) -> None:
        """Clear all checkpoints."""
        for file in os.listdir(self.checkpoint_dir):
            if file.endswith(".json"):
                os.remove(os.path.join(self.checkpoint_dir, file))
        print("✅ Cleared all checkpoints")

    def list_checkpoints(self) -> Dict[str, float]:
        """
        List all available checkpoints with their timestamps.
        
        Returns:
            Dictionary mapping task IDs to timestamp
        """
        checkpoints = {}
        for file in os.listdir(self.checkpoint_dir):
            if file.endswith(".json"):
                task_id = file[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(self.checkpoint_dir, file), 'r') as f:
                        data = json.load(f)
                        checkpoints[task_id] = data.get("timestamp", 0)
                except:
                    checkpoints[task_id] = 0
        
        return checkpoints

def task_callback(task_output):
    """
    Callback function for CrewAI tasks to save checkpoints.
    
    Args:
        task_output: The output of the task
    
    Returns:
        The original task output
    """
    # Get task information from the task output if available
    task_id = getattr(task_output, 'task_id', 'unknown_task')
    task_name = getattr(task_output, 'task_name', 'unknown_task_name')
    
    checkpoint_manager = CheckpointManager()
    
    # Save the task output as a checkpoint
    checkpoint_manager.save_checkpoint(
        task_id=task_id,
        data={
            "task_name": task_name,
            "output": str(task_output)
        }
    )
    
    # Also save to a text file for easy viewing
    checkpoint_dir = Path("checkpoints")
    checkpoint_dir.mkdir(exist_ok=True)
    
    with open(checkpoint_dir / f"{task_id}.txt", "w") as f:
        f.write(str(task_output))
    
    return task_output
