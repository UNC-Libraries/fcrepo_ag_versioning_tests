"""
Locust performance test suite for Fedora Repository (fcrepo)
Measures response performance and tracks file counts and sizes
"""
from locust import HttpUser, task, between, events
from utils.statistics_tracker import StatisticsTracker
import os
import json


class FcrepoUser(HttpUser):
    """
    User class for simulating requests to Fedora Repository
    """
    # Wait time between tasks (in seconds)
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        Called when a simulated user starts
        Initialize any necessary state or authentication
        """
        self.stats_tracker = StatisticsTracker()
        self.base_path = os.getenv("FCREPO_BASE_PATH", "/fcrepo/rest")
    
    @task(3)
    def get_root(self):
        """
        GET request to repository root
        """
        response = self.client.get(
            self.base_path,
            headers={"Accept": "application/ld+json"}
        )
        if response.ok:
            self.stats_tracker.record_response(response)
    
    @task(2)
    def get_container(self):
        """
        GET request to a container resource
        """
        container_path = f"{self.base_path}/container"
        response = self.client.get(
            container_path,
            headers={"Accept": "application/ld+json"}
        )
        if response.ok:
            self.stats_tracker.record_response(response)
    
    @task(1)
    def create_resource(self):
        """
        POST request to create a new resource
        """
        response = self.client.post(
            self.base_path,
            headers={
                "Content-Type": "text/plain",
                "Slug": f"test-resource-{self.environment.stats.num_requests}"
            },
            data="Test resource content"
        )
        if response.status_code == 201:
            self.stats_tracker.record_creation(response)


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """
    Called when the locust process is shutting down
    Save collected statistics
    """
    print("\n=== Saving statistics ===")
    # Statistics will be saved by the tracker instances
