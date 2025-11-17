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
import atexit

# Load environment variables from .env file
load_dotenv()

# Global dictionary to track all stats trackers for saving on exit
_all_stats_trackers = []

def save_all_stats():
    """Save all statistics on program exit"""
    print("\n=== Saving all statistics ===")
    for tracker in _all_stats_trackers:
        try:
            tracker.save_statistics()
        except Exception as e:
            print(f"Error saving statistics: {e}")

# Register the cleanup function
atexit.register(save_all_stats)


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
        # Register this tracker for saving on exit
        _all_stats_trackers.append(self.stats_tracker)
        
        self.base_path = os.getenv("FCREPO_BASE_PATH", "/fcrepo/rest")
        self.test_bins_path = "/Users/bbpennel/git/boxc-ansible/workspace/test_bins/"
        self.test_ocfl_path = "/Users/bbpennel/git/boxc-ansible/workspace/ocfl_root/"
        
        # Track created collections and their update counters
        self.created_collections = []
        self.collection_counters = {}
        self.normal_collection = None
        self.ag_collection = None
        
        # Set up authentication if credentials are provided
        username = os.getenv("FCREPO_USERNAME")
        password = os.getenv("FCREPO_PASSWORD")
        
        if username and password:
            self.auth = (username, password)
        else:
            self.auth = None
        
        # Create both a normal collection and an archival group collection
        self.create_collection_with_transaction(is_archival_group=False)
        self.create_collection_with_transaction(is_archival_group=True)

    def _create_test_binary(self, filename, timestamp):
        """
        Create a test binary file with the timestamp as content
        """
        timestamped_name = f"{filename}.{timestamp}"
        filepath = os.path.join(self.test_bins_path, timestamped_name)
        with open(filepath, 'w') as f:
            f.write(str(timestamp))
        return timestamped_name

    def _get_directory_stats(self, path):
        """
        Get file count, directory count, and total size for a directory
        
        Args:
            path: Directory path to analyze
            
        Returns:
            Tuple of (file_count, dir_count, total_size_bytes)
        """
        file_count = 0
        dir_count = 0
        total_size = 0
        
        if not os.path.exists(path):
            return 0, 0, 0
        
        for root, dirs, files in os.walk(path):
            dir_count += len(dirs)
            file_count += len(files)
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    # Skip files we can't access
                    pass
        
        return file_count, dir_count, total_size

    def create_collection_with_transaction(self, is_archival_group=False):
        """
        Complete workflow: Create a collection object with metadata in a transaction
        Steps 2-5 from the requirements
        Called once during on_start() to set up the collection for this user
        
        Args:
            is_archival_group: If True, creates an ArchivalGroup collection
        """
        # Capture initial OCFL storage state
        initial_file_count, initial_dir_count, initial_total_size = self._get_directory_stats(self.test_ocfl_path)
        
        workflow_start = time.time()
        
        # Generate timestamp for this collection
        timestamp = round(time.time() * 1000)
        collection_prefix = "ag_collection" if is_archival_group else "collection"
        collection_slug = f"{collection_prefix}.{timestamp}"
        
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
            collection_headers = {
                **tx_headers,
                "Slug": collection_slug,
                "Content-Type": "text/turtle"
            }
            # Add ArchivalGroup Link header if needed
            if is_archival_group:
                collection_headers["Link"] = '<http://fedora.info/definitions/v4/repository#ArchivalGroup>;rel="type"'
            
            collection_response = self.client.post(
                self.base_path,
                headers=collection_headers,
                data="""<> <http://example.com/test_property> "0" .""",
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
            
            # Step 6: Record total workflow time and capture final OCFL storage state
            workflow_duration = time.time() - workflow_start
            
            # Capture final OCFL storage state
            final_file_count, final_dir_count, final_total_size = self._get_directory_stats(self.test_ocfl_path)
            
            # Calculate deltas
            file_count_delta = final_file_count - initial_file_count
            dir_count_delta = final_dir_count - initial_dir_count
            size_delta = final_total_size - initial_total_size
            
            print(f"✓ Collection {collection_slug} created successfully")
            print(f"  - Commit time: {commit_duration:.3f}s")
            print(f"  - Total workflow time: {workflow_duration:.3f}s")
            print(f"  - OCFL file count delta: {file_count_delta}")
            print(f"  - OCFL directory count delta: {dir_count_delta}")
            print(f"  - OCFL size delta: {size_delta} bytes")
            
            # Record statistics
            self.stats_tracker.record_workflow({
                "operation": "create_collection",
                "collection_type": "archival_group" if is_archival_group else "normal",
                "collection_id": collection_slug,
                "timestamp": timestamp,
                "commit_duration": commit_duration,
                "workflow_duration": workflow_duration,
                "create_collection_ocfl_count_delta": file_count_delta,
                "create_collection_ocfl_directories_delta": dir_count_delta,
                "create_collection_ocfl_size_delta": size_delta
            })
            
            # Add to list of created collections for PATCH operations
            self.created_collections.append(collection_slug)
            self.collection_counters[collection_slug] = 0
            
            # Store reference to normal or AG collection
            if is_archival_group:
                self.ag_collection = collection_slug
            else:
                self.normal_collection = collection_slug
            
        except Exception as e:
            print(f"Error in collection creation workflow: {e}")

    def _patch_collection_property(self, collection_slug, operation_name):
        """
        Internal method to perform PATCH request on a collection
        
        Args:
            collection_slug: The collection ID to patch
            operation_name: Name for the Locust statistics (e.g., "PATCH Collection Property")
        """
        # Increment counter for this collection
        self.collection_counters[collection_slug] += 1
        counter = self.collection_counters[collection_slug]
        prev_counter = counter - 1
        
        # Build SPARQL update query
        sparql_query = f"""DELETE {{
  <> <http://example.com/test_property> "{prev_counter}" .
}}
INSERT {{   
  <> <http://example.com/test_property> "{counter}" .
}}
WHERE {{ }}"""
        
        # Capture initial OCFL storage state
        initial_file_count, initial_dir_count, initial_total_size = self._get_directory_stats(self.test_ocfl_path)
        
        # Perform PATCH request
        patch_start = time.time()
        response = self.client.patch(
            f"{self.base_path}/{collection_slug}",
            headers={
                "Content-Type": "application/sparql-update"
            },
            data=sparql_query,
            auth=self.auth,
            name=operation_name
        )
        patch_duration = time.time() - patch_start
        
        if not response.ok:
            print(f"Failed to patch collection {collection_slug}: {response.status_code}")
            print(f"Response body: {response.text}")
            return
        
        # Capture final OCFL storage state
        final_file_count, final_dir_count, final_total_size = self._get_directory_stats(self.test_ocfl_path)
        
        # Calculate deltas
        file_count_delta = final_file_count - initial_file_count
        dir_count_delta = final_dir_count - initial_dir_count
        size_delta = final_total_size - initial_total_size
        
        collection_type = "AG" if collection_slug.startswith("ag_") else "Normal"
        print(f"✓ Patched {collection_type} {collection_slug} (update #{counter})")
        print(f"  - Patch time: {patch_duration:.3f}s")
        print(f"  - OCFL file count delta: {file_count_delta}")
        print(f"  - OCFL directory count delta: {dir_count_delta}")
        print(f"  - OCFL size delta: {size_delta} bytes")
        
        # Record statistics
        self.stats_tracker.record_workflow({
            "operation": "patch_collection",
            "collection_type": "archival_group" if collection_slug.startswith("ag_") else "normal",
            "collection_id": collection_slug,
            "update_counter": counter,
            "timestamp": time.time(),
            "patch_duration": patch_duration,
            "patch_collection_ocfl_count_delta": file_count_delta,
            "patch_collection_ocfl_directories_delta": dir_count_delta,
            "patch_collection_ocfl_size_delta": size_delta
        })

    @task(10)
    def patch_normal_collection_property(self):
        """
        PATCH request to update a property on a normal collection
        """
        if not self.normal_collection:
            return
        
        self._patch_collection_property(self.normal_collection, "PATCH Collection Property")
    
    @task(10)
    def patch_ag_collection_property(self):
        """
        PATCH request to update a property on an archival group collection
        """
        if not self.ag_collection:
            return
        
        self._patch_collection_property(self.ag_collection, "PATCH AG Collection Property")

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
    
    def on_stop(self):
        """
        Called when a simulated user stops
        Save statistics for this user
        """
        if hasattr(self, 'stats_tracker'):
            try:
                # Generate unique filename for this user's stats
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                user_id = id(self) % 10000  # Simple user identifier
                filename = f"stats_{timestamp}_user_{user_id}.json"
                self.stats_tracker.save_statistics(filename)
            except Exception as e:
                print(f"Error saving statistics in on_stop: {e}")


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """
    Called when the locust process is shutting down
    Save collected statistics
    """
    print("\n=== Test run completed ===")
    print("Statistics have been saved to the results/ directory")
    # Statistics will be saved by the tracker instances
