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
import uuid

# Load environment variables from .env file
load_dotenv()

class BaseFcrepoUser(HttpUser):
    """
    User class for simulating requests to Fedora Repository
    """
    # Set the host from environment variable
    host = os.getenv("FCREPO_HOST", "http://localhost:8080")
    
    # Wait time between tasks (in seconds)
    wait_time = between(1, 3)
    abstract = True
    
    def on_start(self):
        """
        Called when a simulated user starts
        Initialize any necessary state or authentication
        """
        self.stats_tracker = self.environment.stats_tracker
        
        self.base_path = os.getenv("FCREPO_BASE_PATH", "/fcrepo/rest")
        self.test_bins_path = "/Users/bbpennel/git/boxc-ansible/workspace/test_bins/"
        self.test_ocfl_path = "/Users/bbpennel/git/boxc-ansible/workspace/ocfl_root/"
        
        # Track created collections and their update counters
        self.created_collections = []
        self.collection_counters = {}
        self.atomic_collection = None
        self.ag_collection = None
        
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

    def _record_collection_workflow(
        self,
        collection_slug,
        is_archival_group,
        workflow_duration,
        commit_duration=None,
        storage_deltas=None,
        success=True,
        failure_stage=None,
        workflow_type="collection_storage",
    ):
        """Record one collection creation attempt, including failed timing samples."""
        data = {
            "operation": "create_collection",
            "workflow_type": workflow_type,
            "collection_type": "archival_group" if is_archival_group else "atomic",
            "collection_id": collection_slug,
            "success": success,
            "workflow_duration": workflow_duration,
        }
        if commit_duration is not None:
            data["commit_duration"] = commit_duration
        if failure_stage:
            data["failure_stage"] = failure_stage
        if storage_deltas:
            data.update(storage_deltas)
        self.stats_tracker.record_workflow(data)

    def create_collection_with_transaction(
        self,
        is_archival_group=False,
        measure_storage=True,
        workflow_type="collection_storage",
        verbose=True,
    ):
        """
        Complete workflow: Create a collection object with metadata in a transaction
        Steps 2-5 from the requirements
        Called once during on_start() to set up the collection for this user
        
        Args:
            is_archival_group: If True, creates an ArchivalGroup collection
        """
        initial_file_count = initial_dir_count = initial_total_size = 0
        if measure_storage:
            initial_file_count, initial_dir_count, initial_total_size = self._get_directory_stats(self.test_ocfl_path)
        
        workflow_start = time.perf_counter()
        
        # Generate timestamp for this collection
        timestamp = f"{round(time.time() * 1000)}-{uuid.uuid4().hex}"
        collection_prefix = "ag_collection" if is_archival_group else "collection"
        collection_slug = f"{collection_prefix}.{timestamp}"
        
        failure_stage = "open_transaction"
        try:
            # Step 2: Open transaction
            tx_response = self.client.post(
                f"{self.base_path}/fcr:tx",
                auth=self.auth,
                name="Open Transaction"
            )
            if not tx_response.ok:
                print(f"Failed to open transaction: {tx_response.status_code}")
                self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, success=False, failure_stage=failure_stage, workflow_type=workflow_type)
                return
            
            # Get transaction ID from Location header
            tx_id = tx_response.headers.get("Location")
            if not tx_id:
                print("No transaction ID in response Location header")
                self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, success=False, failure_stage="missing_transaction_location", workflow_type=workflow_type)
                return
            
            if verbose:
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
            
            failure_stage = "create_collection"
            collection_response = self.client.post(
                self.base_path,
                headers=collection_headers,
                data="""<> <http://example.com/test_property> "0" .""",
                auth=self.auth,
                name="Create Collection"
            )
            if not collection_response.ok:
                print(f"Failed to create collection: {collection_response.status_code}")
                self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, success=False, failure_stage=failure_stage, workflow_type=workflow_type)
                return
            
            # 4b: Create md container
            failure_stage = "create_md_container"
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
                self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, success=False, failure_stage=failure_stage, workflow_type=workflow_type)
                return
            
            # 4c: Create md_description with external content
            failure_stage = "create_md_description"
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
                self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, success=False, failure_stage=failure_stage, workflow_type=workflow_type)
                return
            
            # 4d: Create md_description_history with external content
            failure_stage = "create_md_description_history"
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
                self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, success=False, failure_stage=failure_stage, workflow_type=workflow_type)
                return
            
            # 4e: Create event_log with external content
            failure_stage = "create_event_log"
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
                self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, success=False, failure_stage=failure_stage, workflow_type=workflow_type)
                return
            
            # Step 5: Commit transaction
            failure_stage = "commit_transaction"
            commit_start = time.perf_counter()
            commit_response = self.client.put(
                tx_id,
                auth=self.auth,
                name="Commit Transaction"
            )
            commit_duration = time.perf_counter() - commit_start
            
            if not commit_response.ok:
                print(f"Failed to commit transaction: {commit_response.status_code}")
                self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, commit_duration=commit_duration, success=False, failure_stage=failure_stage, workflow_type=workflow_type)
                return
            
            # Step 6: Record total workflow time and capture final OCFL storage state
            workflow_duration = time.perf_counter() - workflow_start
            
            storage_deltas = None
            if measure_storage:
                final_file_count, final_dir_count, final_total_size = self._get_directory_stats(self.test_ocfl_path)
                storage_deltas = {
                    "create_collection_ocfl_count_delta": final_file_count - initial_file_count,
                    "create_collection_ocfl_directories_delta": final_dir_count - initial_dir_count,
                    "create_collection_ocfl_size_delta": final_total_size - initial_total_size,
                }
            
            if verbose:
                print(f"Collection {collection_slug} created successfully")
                print(f"  - Commit time: {commit_duration:.3f}s")
                print(f"  - Total workflow time: {workflow_duration:.3f}s")
                if storage_deltas:
                    print(f"  - OCFL file count delta: {storage_deltas['create_collection_ocfl_count_delta']}")
                    print(f"  - OCFL directory count delta: {storage_deltas['create_collection_ocfl_directories_delta']}")
                    print(f"  - OCFL size delta: {storage_deltas['create_collection_ocfl_size_delta']} bytes")
            
            # Record statistics
            self._record_collection_workflow(collection_slug, is_archival_group, workflow_duration, commit_duration, storage_deltas, workflow_type=workflow_type)
            
            # Add to list of created collections for PATCH operations
            self.created_collections.append(collection_slug)
            self.collection_counters[collection_slug] = 0
            
            # Store reference to atomic or AG collection
            if is_archival_group:
                self.ag_collection = collection_slug
            else:
                self.atomic_collection = collection_slug
            
        except Exception as e:
            print(f"Error in collection creation workflow: {e}")
            self._record_collection_workflow(collection_slug, is_archival_group, time.perf_counter() - workflow_start, success=False, failure_stage=failure_stage, workflow_type=workflow_type)

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
        
        collection_type = "AG" if collection_slug.startswith("ag_") else "Atomic"
        print(f"✓ Patched {collection_type} {collection_slug} (update #{counter})")
        print(f"  - Patch time: {patch_duration:.3f}s")
        print(f"  - OCFL file count delta: {file_count_delta}")
        print(f"  - OCFL directory count delta: {dir_count_delta}")
        print(f"  - OCFL size delta: {size_delta} bytes")
        
        # Record statistics
        self.stats_tracker.record_workflow({
            "operation": "patch_collection",
            "collection_type": "archival_group" if collection_slug.startswith("ag_") else "atomic",
            "collection_id": collection_slug,
            "update_counter": counter,
            "timestamp": time.time(),
            "patch_duration": patch_duration,
            "patch_collection_ocfl_count_delta": file_count_delta,
            "patch_collection_ocfl_directories_delta": dir_count_delta,
            "patch_collection_ocfl_size_delta": size_delta
        })

class FcrepoUser(BaseFcrepoUser):
    """Mixed storage-growth workload for serial or low-concurrency runs."""

    def on_start(self):
        super().on_start()
        self.create_collection_with_transaction(is_archival_group=False)
        self.create_collection_with_transaction(is_archival_group=True)

    @task(10)
    def patch_atomic_collection_property(self):
        """
        PATCH request to update a property on a atomic collection
        """
        if not self.atomic_collection:
            return
        
        self._patch_collection_property(self.atomic_collection, "PATCH Collection Property")
    
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
        """Run statistics are saved once by the test-stop listener."""
        pass


class CreationTimingUser(BaseFcrepoUser):
    """Concurrent collection creation workload without OCFL filesystem scans."""

    @task
    def create_atomic_collection(self):
        self.create_collection_with_transaction(
            is_archival_group=False,
            measure_storage=False,
            workflow_type="collection_creation_timing",
            verbose=False,
        )

    @task
    def create_ag_collection(self):
        self.create_collection_with_transaction(
            is_archival_group=True,
            measure_storage=False,
            workflow_type="collection_creation_timing",
            verbose=False,
        )


@events.test_start.add_listener
def create_run_statistics_tracker(environment, **kwargs):
    """Create one shared tracker so concurrent users produce one run result."""
    config_name = os.getenv("TEST_CONFIG_NAME", "default")
    parsed_options = getattr(environment, "parsed_options", None)
    environment.stats_tracker = StatisticsTracker(
        results_dir=os.path.join("results", config_name),
        run_metadata={
            "config_name": config_name,
            "start_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "user_classes": [user_class.__name__ for user_class in environment.user_classes],
            "users": getattr(parsed_options, "num_users", None),
            "spawn_rate": getattr(parsed_options, "spawn_rate", None),
        },
    )


@events.test_stop.add_listener
def save_run_statistics(environment, **kwargs):
    """Persist the complete run after all users have stopped."""
    tracker = getattr(environment, "stats_tracker", None)
    if tracker:
        tracker.set_run_metadata(end_time=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        tracker.save_statistics()
        print("\n=== Test run completed ===")
