"""
Statistics tracker for recording performance metrics and resource information
"""
import json
import os
from datetime import datetime
from typing import Dict, List


class StatisticsTracker:
    """
    Tracks statistics about file counts, sizes, and response performance
    """
    
    def __init__(self):
        self.responses: List[Dict] = []
        self.creations: List[Dict] = []
        self.workflows: List[Dict] = []
        self.file_count = 0
        self.total_size = 0
        self.results_dir = "results"
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def record_response(self, response):
        """
        Record information about a response
        
        Args:
            response: The HTTP response object
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
            "content_length": len(response.content) if response.content else 0
        }
        self.responses.append(record)
        
        if response.content:
            self.total_size += len(response.content)
    
    def record_creation(self, response):
        """
        Record information about a resource creation
        
        Args:
            response: The HTTP response object from a creation request
        """
        self.file_count += 1
        record = {
            "timestamp": datetime.now().isoformat(),
            "location": response.headers.get("Location", ""),
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
        self.creations.append(record)
    
    def record_workflow(self, workflow_data: Dict):
        """
        Record information about a complete workflow execution
        
        Args:
            workflow_data: Dictionary containing workflow metrics
        """
        workflow_data["timestamp"] = datetime.now().isoformat()
        self.workflows.append(workflow_data)
    
    def get_statistics(self) -> Dict:
        """
        Get aggregated statistics
        
        Returns:
            Dictionary containing summary statistics
        """
        return {
            "total_responses": len(self.responses),
            "total_creations": self.file_count,
            "total_workflows": len(self.workflows),
            "total_size_bytes": self.total_size,
            "average_response_time": self._calculate_average_response_time(),
            "average_workflow_duration": self._calculate_average_workflow_duration(),
            "average_commit_duration": self._calculate_average_commit_duration(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_average_response_time(self) -> float:
        """
        Calculate average response time across all requests
        
        Returns:
            Average response time in seconds
        """
        if not self.responses:
            return 0.0
        
        total_time = sum(r["response_time"] for r in self.responses)
        return total_time / len(self.responses)
    
    def save_statistics(self, filename: str = None):
        """
        Save statistics to a JSON file
        
        Args:
            filename: Optional custom filename, otherwise generates timestamped name
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stats_{timestamp}.json"
        
        filepath = os.path.join(self.results_dir, filename)
        
        data = {
            "summary": self.get_statistics(),
            "responses": self.responses,
            "creations": self.creations
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"Statistics saved to {filepath}")
        return filepath
