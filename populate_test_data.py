"""
Script for populating test data in a Fedora Repository (fcrepo) instance.
Creates resources via API calls to build a test dataset for performance testing.
"""
import argparse
import requests
import time
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class FcrepoDataPopulator:
    """
    Handles creation of test data in a Fedora Repository instance
    """
    
    def __init__(
        self,
        base_url: str,
        base_path: str = "/fcrepo/rest",
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize the data populator
        
        Args:
            base_url: Base URL of the fcrepo instance (e.g., http://localhost:8080)
            base_path: Base path for API endpoints (default: /fcrepo/rest)
            username: Username for basic authentication (optional)
            password: Password for basic authentication (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.base_path = base_path
        self.full_path = f"{self.base_url}{self.base_path}"
        self.auth = (username, password) if username and password else None
        self.session = requests.Session()
        if self.auth:
            self.session.auth = self.auth
        
        # Statistics tracking
        self.created_count = 0
        self.failed_count = 0
        self.ag_count = 0
        self.atomic_count = 0
        self.child_count = 0
        self.start_time = None
        self.created_resources = []
    
    def create_resource(self, index: int) -> Tuple[bool, str, Optional[str]]:
        """
        Create a single resource via POST request
        50% of the time creates an Archival Group, 50% creates an Atomic Resource
        
        Args:
            index: Resource index number for slug generation
            
        Returns:
            Tuple of (success, message, resource_uri)
        """
        timestamp = round(time.time() * 1000)
        is_archival_group = random.random() < 0.5
        
        if is_archival_group:
            slug = f"ag-resource-{index}-{timestamp}"
            headers = {
                "Slug": slug,
                "Link": '<http://fedora.info/definitions/v4/repository#ArchivalGroup>;rel="type"'
            }
        else:
            slug = f"atomic-resource-{index}-{timestamp}"
            headers = {"Slug": slug}
        
        try:
            response = self.session.post(
                self.full_path,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                resource_uri = response.headers.get('Location', '')
                if is_archival_group:
                    self.ag_count += 1
                else:
                    self.atomic_count += 1
                return True, f"Created {'AG' if is_archival_group else 'atomic'} resource {index}: {slug}", resource_uri
            else:
                return False, f"Failed to create resource {index}: HTTP {response.status_code}", None
                
        except requests.exceptions.RequestException as e:
            return False, f"Error creating resource {index}: {str(e)}", None
    
    def create_child_resource(self, parent_uri: str, child_index: int) -> Tuple[bool, str]:
        """
        Create a child resource within a parent resource
        
        Args:
            parent_uri: URI of the parent resource
            child_index: Index of the child for slug generation
            
        Returns:
            Tuple of (success, message)
        """
        timestamp = round(time.time() * 1000)
        slug = f"child-resource-{child_index}-{timestamp}"
        
        try:
            response = self.session.post(
                parent_uri,
                headers={"Slug": slug},
                timeout=30
            )
            
            if response.status_code == 201:
                self.child_count += 1
                return True, f"Created child {child_index}"
            else:
                return False, f"Failed to create child {child_index}: HTTP {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Error creating child {child_index}: {str(e)}"
    
    def create_resource_with_children(self, index: int) -> Tuple[bool, str, Optional[str]]:
        """
        Create a resource and its child resources
        50% of the time creates 0 children, 50% creates 1-10 children
        
        Args:
            index: Resource index number
            
        Returns:
            Tuple of (success, message, resource_uri)
        """
        # Create parent resource
        success, message, resource_uri = self.create_resource(index)
        
        if not success:
            return success, message, resource_uri
        
        # Determine number of children: 50% chance of 0, 50% chance of 1-10
        if random.random() < 0.5:
            num_children = 0
        else:
            num_children = random.randint(1, 10)
        
        # Create children
        children_created = 0
        for i in range(1, num_children + 1):
            child_success, child_message = self.create_child_resource(resource_uri, i)
            if child_success:
                children_created += 1
        
        if num_children > 0:
            message += f" (with {children_created}/{num_children} children)"
        
        return success, message, resource_uri
    
    def populate(
        self,
        num_resources: int,
        max_workers: int = 10,
        verbose: bool = True
    ) -> None:
        """
        Create resources in parallel using thread pool
        
        Args:
            num_resources: Number of resources to create
            max_workers: Maximum number of parallel workers
            verbose: Whether to print progress updates
        """
        self.start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"Starting creation of {num_resources} resources")
        print(f"Target: {self.full_path}")
        print(f"Workers: {max_workers}")
        print(f"Mix: 50% Archival Groups, 50% Atomic Resources")
        print(f"{'='*60}\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self.create_resource_with_children, i): i 
                for i in range(1, num_resources + 1)
            }
            
            # Process results as they complete
            for future in as_completed(futures):
                index = futures[future]
                try:
                    success, message, resource_uri = future.result()
                    
                    if success:
                        self.created_count += 1
                        self.created_resources.append(resource_uri)
                        if verbose and self.created_count % 100 == 0:
                            elapsed = time.time() - self.start_time
                            rate = self.created_count / elapsed
                            print(f"Progress: {self.created_count}/{num_resources} created ({rate:.2f} resources/sec)")
                    else:
                        self.failed_count += 1
                        if verbose:
                            print(f"ERROR: {message}")
                            
                except Exception as e:
                    self.failed_count += 1
                    if verbose:
                        print(f"ERROR: Exception for resource {index}: {str(e)}")
        
        self._print_summary()
    
    def _print_summary(self) -> None:
        """Print summary statistics of the population run"""
        elapsed = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"Population Summary")
        print(f"{'='*60}")
        print(f"Successfully created: {self.created_count} parent resources")
        print(f"  - Archival Groups: {self.ag_count}")
        print(f"  - Atomic Resources: {self.atomic_count}")
        print(f"Child resources created: {self.child_count}")
        print(f"Total resources: {self.created_count + self.child_count}")
        print(f"Failed: {self.failed_count}")
        print(f"Total time: {elapsed:.2f} seconds")
        print(f"Average rate: {(self.created_count + self.child_count) / elapsed:.2f} resources/sec")
        print(f"{'='*60}\n")


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description="Populate test data in a Fedora Repository instance"
    )
    parser.add_argument(
        '--num-resources',
        type=int,
        default=10000,
        help='Number of resources to create (default: 10000)'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        default=os.getenv("FCREPO_HOST", "http://localhost:8080"),
        help='Base URL of the fcrepo instance (default: from FCREPO_HOST env var or http://localhost:8080)'
    )
    parser.add_argument(
        '--base-path',
        type=str,
        default=os.getenv("FCREPO_BASE_PATH", "/fcrepo/rest"),
        help='Base path for API endpoints (default: from FCREPO_BASE_PATH env var or /fcrepo/rest)'
    )
    parser.add_argument(
        '--username',
        type=str,
        default=os.getenv("FCREPO_USERNAME"),
        help='Username for basic authentication (default: from FCREPO_USERNAME env var)'
    )
    parser.add_argument(
        '--password',
        type=str,
        default=os.getenv("FCREPO_PASSWORD"),
        help='Password for basic authentication (default: from FCREPO_PASSWORD env var)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of parallel workers (default: 10)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output (only show summary)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.num_resources <= 0:
        print("ERROR: Number of resources must be greater than 0")
        sys.exit(1)
    
    # Initialize populator
    populator = FcrepoDataPopulator(
        base_url=args.base_url,
        base_path=args.base_path,
        username=args.username,
        password=args.password
    )
    
    # Run population
    try:
        populator.populate(
            num_resources=args.num_resources,
            max_workers=args.workers,
            verbose=not args.quiet
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        populator._print_summary()
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
