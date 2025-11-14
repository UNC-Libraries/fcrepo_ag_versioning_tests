"""
Locust performance test suite for Fedora Repository (fcrepo)
Measures response performance and tracks file counts and sizes
"""
from locust import HttpUser, task, between, events
from utils.statistics_tracker import StatisticsTracker
from dotenv import load_dotenv
import os
import json
import time

# Load environment variables from .env file
load_dotenv()


class FcrepoUser(HttpUser):
    """
    User class for simulating requests to Fedora Repository
    """
    # Set the host from environment variable
    host = os.getenv("FCREPO_HOST", "http://localhost:8080")
    
    # Wait time between tasks (in seconds)
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        Called when a simulated user starts
        Initialize any necessary state or authentication
        """
        self.stats_tracker = StatisticsTracker()
        self.base_path = os.getenv("FCREPO_BASE_PATH", "/fcrepo/rest")
        self.test_bins_path = "/Users/bbpennel/git/boxc-ansible/workspace/test_bins/"
        
        # Set up authentication if credentials are provided
        username = os.getenv("FCREPO_USERNAME")
        password = os.getenv("FCREPO_PASSWORD")
        
        if username and password:
            self.auth = (username, password)
        else:
            self.auth = None

    def _create_test_binary(self, filename, timestamp):
        """
        Create a test binary file with the timestamp as content
        """
        timestamped_name = f"{filename}.{timestamp}"
        filepath = os.path.join(self.test_bins_path, timestamped_name)
        with open(filepath, 'w') as f:
            f.write(str(timestamp))
        return timestamped_name

    @task(1)
    def create_collection_with_transaction(self):
        """
        Complete workflow: Create a collection object with metadata in a transaction
        Steps 2-5 from the requirements
        """
        workflow_start = time.time()
        
        # Generate timestamp for this collection
        timestamp = round(time.time() * 1000)
        collection_slug = f"collection.{timestamp}"
        
        try:
            # Step 2: Open transaction
            tx_response = self.client.post(
                f"{self.base_path}/fcr:tx",
                auth=self.auth,
                name="Open Transaction"
            )
            if not tx_response.ok:
                print(f"Failed to open transaction: {tx_response.status_code}")
                return
            
            # Get transaction ID from Location header
            tx_id = tx_response.headers.get("Location")
            if not tx_id:
                print("No transaction ID in response Location header")
                return
            
            print(f"Transaction opened: {tx_id}")
            
            # Step 3: Create test binary files
            md_descriptive_file = self._create_test_binary(f"md_descriptive", timestamp)
            md_descriptive_history_file = self._create_test_binary(f"md_descriptive_history", timestamp)
            event_log_file = self._create_test_binary(f"event_log", timestamp)
            
            # Step 4: Create collection object and children
            # All requests must include Atomic-ID header with transaction ID
            tx_headers = {"Atomic-ID": tx_id}
            
            # 4a: Create collection object
            collection_response = self.client.post(
                self.base_path,
                headers={
                    **tx_headers,
                    "Slug": collection_slug,
                    "Content-Type": "text/turtle"
                },
                data="",
                auth=self.auth,
                name="Create Collection"
            )
            if not collection_response.ok:
                print(f"Failed to create collection: {collection_response.status_code}")
                return
            
            # 4b: Create md container
            md_response = self.client.put(
                f"{self.base_path}/{collection_slug}/md",
                headers={
                    **tx_headers,
                    "Content-Type": "text/turtle"
                },
                data="",
                auth=self.auth,
                name="Create md container"
            )
            if not md_response.ok:
                print(f"Failed to create md: {md_response.status_code}")
                return
            
            # 4c: Create md_description with external content
            md_desc_response = self.client.put(
                f"{self.base_path}/{collection_slug}/md/md_description",
                headers={
                    **tx_headers,
                    "Content-Type": "text/turtle",
                    "Link": f'<file:///vagrant/workspace/test_bins/{md_descriptive_file}>; rel="http://fedora.info/definitions/fcrepo#ExternalContent"; handling="proxy"; type="text/xml"'
                },
                data="",
                auth=self.auth,
                name="Create md_description"
            )
            if not md_desc_response.ok:
                print(f"Response body: {md_desc_response.text}")
                print(f"Response headers: {dict(md_desc_response.headers)}")
                print(f"Failed to create md_description: {md_desc_response.status_code}")
                return
            
            # 4d: Create md_description_history with external content
            md_hist_response = self.client.put(
                f"{self.base_path}/{collection_slug}/md/md_description_history",
                headers={
                    **tx_headers,
                    "Content-Type": "text/turtle",
                    "Link": f'<file:///vagrant/workspace/test_bins/{md_descriptive_history_file}>; rel="http://fedora.info/definitions/fcrepo#ExternalContent"; handling="proxy"; type="text/xml"'
                },
                data="",
                auth=self.auth,
                name="Create md_description_history"
            )
            if not md_hist_response.ok:
                print(f"Failed to create md_description_history: {md_hist_response.status_code}")
                print(f"Response body: {md_hist_response.text}")
                print(f"Response headers: {dict(md_hist_response.headers)}")
                return
            
            # 4e: Create event_log with external content
            event_log_response = self.client.put(
                f"{self.base_path}/{collection_slug}/md/event_log",
                headers={
                    **tx_headers,
                    "Content-Type": "text/turtle",
                    "Link": f'<file:///vagrant/workspace/test_bins/{event_log_file}>; rel="http://fedora.info/definitions/fcrepo#ExternalContent"; handling="proxy"; type="application/n-triples"'
                },
                data="",
                auth=self.auth,
                name="Create event_log"
            )
            if not event_log_response.ok:
                print(f"Failed to create event_log: {event_log_response.status_code}")
                return
            
            # Step 5: Commit transaction
            commit_start = time.time()
            commit_response = self.client.put(
                tx_id,
                auth=self.auth,
                name="Commit Transaction"
            )
            commit_duration = time.time() - commit_start
            
            if not commit_response.ok:
                print(f"Failed to commit transaction: {commit_response.status_code}")
                return
            
            # Step 6: Record total workflow time
            workflow_duration = time.time() - workflow_start
            
            print(f"✓ Collection {collection_slug} created successfully")
            print(f"  - Commit time: {commit_duration:.3f}s")
            print(f"  - Total workflow time: {workflow_duration:.3f}s")
            
            # Record statistics
            self.stats_tracker.record_workflow({
                "collection_id": collection_slug,
                "timestamp": timestamp,
                "commit_duration": commit_duration,
                "workflow_duration": workflow_duration
            })
            
        except Exception as e:
            print(f"Error in collection creation workflow: {e}")

    @task(3)
    def get_root(self):
        """
        GET request to repository root
        """
        response = self.client.get(
            self.base_path,
            auth=self.auth
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
            auth=self.auth
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
                "Slug": f"test-resource-{round(time.time() * 1000)}"
            },
            auth=self.auth
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
