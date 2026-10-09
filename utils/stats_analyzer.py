"""
Utility for analyzing and comparing statistics from multiple test runs
"""
import json
import os
import random
from glob import glob
from datetime import datetime
from typing import List, Dict


class StatsAnalyzer:
    """
    Load and analyze statistics from previous test runs
    """
    
    def __init__(self, results_dir="results", config_name=None):
        """
        Initialize the analyzer
        
        Args:
            results_dir: Base results directory
            config_name: Optional specific config subdirectory to analyze.
                        If None, uses TEST_CONFIG_NAME env var, defaults to "default"
        """
        # If no config_name provided, check environment variable
        if config_name is None:
            config_name = os.getenv("TEST_CONFIG_NAME", "default")
        
        self.results_dir = os.path.join(results_dir, config_name)
        self.config_name = config_name
    
    def list_available_runs(self) -> List[str]:
        """
        List all available statistics files
        
        Returns:
            List of filenames
        """
        pattern = os.path.join(self.results_dir, "stats_*.json")
        files = glob(pattern)
        # Return relative paths from results_dir
        return sorted([os.path.relpath(f, self.results_dir) for f in files])
    
    def load_run(self, filename: str) -> Dict:
        """
        Load statistics from a specific run
        
        Args:
            filename: Name of the statistics file
            
        Returns:
            Dictionary containing the statistics
        """
        filepath = os.path.join(self.results_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def load_latest_run(self) -> Dict:
        """
        Load statistics from the most recent run
        
        Returns:
            Dictionary containing the statistics
        """
        runs = self.list_available_runs()
        if not runs:
            raise ValueError("No statistics files found")
        
        return self.load_run(runs[-1])
    
    def load_all_runs(self) -> List[Dict]:
        """
        Load statistics from all available runs
        
        Returns:
            List of dictionaries containing statistics
        """
        runs = self.list_available_runs()
        return [self.load_run(run) for run in runs]
    
    def compare_patch_operations(self, data: Dict) -> Dict:
        """
        Analyze PATCH operations from a run
        
        Args:
            data: Statistics data from a run
            
        Returns:
            Dictionary with analysis of atomic vs AG collections
        """
        workflows = data.get("workflows", [])
        
        atomic_patches = [w for w in workflows if w.get("operation") == "patch_collection" 
                         and w.get("collection_type") == "atomic"]
        ag_patches = [w for w in workflows if w.get("operation") == "patch_collection" 
                     and w.get("collection_type") == "archival_group"]
        
        def analyze_patches(patches):
            if not patches:
                return {}
            
            # Sort by update counter to ensure proper ordering
            sorted_patches = sorted(patches, key=lambda p: p.get("update_counter", 0))
            
            # Calculate growth rate (linear regression slope)
            size_deltas = [p.get("patch_collection_ocfl_size_delta", 0) for p in sorted_patches]
            growth_rate = None
            if len(size_deltas) > 1:
                # Linear regression: y = mx + b, we want m (slope = growth rate)
                # Since x values are sequential (1, 2, 3, ...), we can use a simplified formula
                #
                # EXAMPLE: If size_deltas = [3490, 4289, 5088, 5887, 6686]
                #   x values: [1, 2, 3, 4, 5]
                #   We're finding the line of best fit to see the trend
                #   The slope tells us: "on average, each update adds ~800 bytes"
                #
                n = len(size_deltas)
                
                # Full linear regression formula (works for any x values)
                x_values = list(range(1, n + 1))  # Update counter: 1, 2, 3, ...
                x_mean = sum(x_values) / n  # Average x position (middle of the sequence)
                y_mean = sum(size_deltas) / n  # Average size delta
                
                # Numerator: measures how y and x change together
                # For each point, we look at how far it is from the means
                numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, size_deltas))
                
                # Denominator: spread of x values from their mean
                # For x = [1,2,3,4,5] with x_mean=3: denominator = (-2)² + (-1)² + 0² + 1² + 2² = 10
                denominator = sum((x - x_mean) ** 2 for x in x_values)
                
                if denominator != 0:
                    growth_rate = numerator / denominator
                
                # In your example: growth_rate ≈ 799 bytes/update
                # This means each new update adds roughly 799 more bytes to OCFL storage
            
            
            return {
                "count": len(patches),
                "avg_patch_duration": sum(p.get("patch_duration", 0) for p in patches) / len(patches),
                "avg_file_count_delta": sum(p.get("patch_collection_ocfl_count_delta", 0) for p in patches) / len(patches),
                "avg_dir_count_delta": sum(p.get("patch_collection_ocfl_directories_delta", 0) for p in patches) / len(patches),
                "avg_size_delta": sum(p.get("patch_collection_ocfl_size_delta", 0) for p in patches) / len(patches),
                "total_size_delta": sum(p.get("patch_collection_ocfl_size_delta", 0) for p in patches),
                "size_growth_rate": growth_rate,  # Bytes per update
                "first_patch_size_delta": sorted_patches[0].get("patch_collection_ocfl_size_delta", 0) if sorted_patches else 0,
                "last_patch_size_delta": sorted_patches[-1].get("patch_collection_ocfl_size_delta", 0) if sorted_patches else 0,
            }
        
        return {
            "atomic_collection": analyze_patches(atomic_patches),
            "archival_group_collection": analyze_patches(ag_patches)
        }

    def analyze_creations(self, creations):
        if not creations:
            return {}
        
        return {
            "count": len(creations),
            "avg_workflow_duration": sum(c.get("workflow_duration", 0) for c in creations) / len(creations),
            "avg_commit_duration": sum(c.get("commit_duration", 0) for c in creations) / len(creations),
            "avg_file_count_delta": sum(c.get("create_collection_ocfl_count_delta", 0) for c in creations) / len(creations),
            "avg_dir_count_delta": sum(c.get("create_collection_ocfl_directories_delta", 0) for c in creations) / len(creations),
            "avg_size_delta": sum(c.get("create_collection_ocfl_size_delta", 0) for c in creations) / len(creations),
            "total_file_count_delta": sum(c.get("create_collection_ocfl_count_delta", 0) for c in creations),
            "total_dir_count_delta": sum(c.get("create_collection_ocfl_directories_delta", 0) for c in creations),
            "total_size_delta": sum(c.get("create_collection_ocfl_size_delta", 0) for c in creations),
        }

    def compare_creation_operations(self, data: Dict) -> Dict:
        """
        Analyze collection creation operations from a run
        
        Args:
            data: Statistics data from a run
            
        Returns:
            Dictionary with analysis of atomic vs AG collection creation
        """
        workflows = data.get("workflows", [])
        
        atomic_creations = [w for w in workflows if w.get("operation") == "create_collection"
                           and w.get("workflow_type", "collection_storage") == "collection_storage"
                           and w.get("collection_type") == "atomic"]
        ag_creations = [w for w in workflows if w.get("operation") == "create_collection"
                        and w.get("workflow_type", "collection_storage") == "collection_storage"
                        and w.get("collection_type") == "archival_group"]

        return {
            "atomic_collection": self.analyze_creations(atomic_creations),
            "archival_group_collection": self.analyze_creations(ag_creations)
        }
    
    def print_creation_comparison(self, data: Dict):
        """
        Print a formatted comparison of atomic vs AG collection creation
        
        Args:
            data: Statistics data from a run
        """
        comparison = self.compare_creation_operations(data)
        
        print("\n" + "=" * 70)
        print("COLLECTION CREATION COMPARISON: atomic vs Archival Group")
        print("=" * 70)
        
        for coll_type, stats in comparison.items():
            if not stats:
                continue
                
            print(f"\n{coll_type.replace('_', ' ').title()}:")
            print(f"  Collections Created: {stats['count']}")
            print(f"  Avg Workflow Duration: {stats['avg_workflow_duration']:.4f}s")
            print(f"  Avg Commit Duration: {stats['avg_commit_duration']:.4f}s")
            print(f"  Avg File Count Delta: {stats['avg_file_count_delta']:.2f}")
            print(f"  Avg Directory Count Delta: {stats['avg_dir_count_delta']:.2f}")
            print(f"  Avg Size Delta: {stats['avg_size_delta']:.2f} bytes ({stats['avg_size_delta']/1024:.2f} KB)")
            print(f"  Total Files Created: {stats['total_file_count_delta']}")
            print(f"  Total Directories Created: {stats['total_dir_count_delta']}")
            print(f"  Total Size: {stats['total_size_delta']:,.0f} bytes ({stats['total_size_delta']/1024:,.1f} KB)")
        
        # Compare if both exist
        if comparison.get("atomic_collection") and comparison.get("archival_group_collection"):
            print("\n" + "-" * 70)
            print("COMPARISON:")
            atomic = comparison["atomic_collection"]
            ag = comparison["archival_group_collection"]
            
            workflow_diff = ((ag["avg_workflow_duration"] - atomic["avg_workflow_duration"]) / atomic["avg_workflow_duration"]) * 100
            commit_diff = ((ag["avg_commit_duration"] - atomic["avg_commit_duration"]) / atomic["avg_commit_duration"]) * 100
            file_diff = ((ag["avg_file_count_delta"] - atomic["avg_file_count_delta"]) / atomic["avg_file_count_delta"]) * 100 if atomic["avg_file_count_delta"] > 0 else 0
            dir_diff = ((ag["avg_dir_count_delta"] - atomic["avg_dir_count_delta"]) / atomic["avg_dir_count_delta"]) * 100 if atomic["avg_dir_count_delta"] > 0 else 0
            size_diff = ((ag["avg_size_delta"] - atomic["avg_size_delta"]) / atomic["avg_size_delta"]) * 100 if atomic["avg_size_delta"] > 0 else 0
            
            print(f"  AG Workflow Duration vs atomic: {workflow_diff:+.1f}%")
            print(f"  AG Commit Duration vs atomic: {commit_diff:+.1f}%")
            print(f"  AG File Count Delta vs atomic: {file_diff:+.1f}%")
            print(f"  AG Directory Count Delta vs atomic: {dir_diff:+.1f}%")
            print(f"  AG Size Delta vs atomic: {size_diff:+.1f}%")
            
            print(f"\n  Absolute Differences (AG - atomic):")
            print(f"    Workflow Duration: {(ag['avg_workflow_duration'] - atomic['avg_workflow_duration']):+.4f}s")
            print(f"    Commit Duration: {(ag['avg_commit_duration'] - atomic['avg_commit_duration']):+.4f}s")
            print(f"    File Count Delta: {(ag['avg_file_count_delta'] - atomic['avg_file_count_delta']):+.2f} files")
            print(f"    Directory Count Delta: {(ag['avg_dir_count_delta'] - atomic['avg_dir_count_delta']):+.2f} directories")
            print(f"    Size Delta: {(ag['avg_size_delta'] - atomic['avg_size_delta']):+.2f} bytes ({(ag['avg_size_delta'] - atomic['avg_size_delta'])/1024:+.2f} KB)")
        
        print("=" * 70 + "\n")

    @staticmethod
    def _percentile(values: List[float], percentile: float) -> float:
        """Calculate a percentile using linear interpolation between samples."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * percentile / 100
        lower = int(index)
        upper = min(lower + 1, len(sorted_values) - 1)
        fraction = index - lower
        return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction

    @staticmethod
    def _mean_confidence_interval(values: List[float], samples: int = 1000) -> tuple:
        """Return a deterministic bootstrap 95% interval for the sample mean."""
        if len(values) < 2:
            return (0.0, 0.0)
        generator = random.Random(0)
        count = len(values)
        means = sorted(
            sum(generator.choice(values) for _ in range(count)) / count
            for _ in range(samples)
        )
        return (
            StatsAnalyzer._percentile(means, 2.5),
            StatsAnalyzer._percentile(means, 97.5),
        )

    def creation_timing_summary(self, data: Dict) -> Dict:
        """Summarize successful creation-only workflow timings by collection type."""
        workflows = [
            workflow for workflow in data.get("workflows", [])
            if workflow.get("operation") == "create_collection"
            and workflow.get("workflow_type") == "collection_creation_timing"
        ]

        def summarize(collection_type):
            attempts = [w for w in workflows if w.get("collection_type") == collection_type]
            successes = [w for w in attempts if w.get("success", True)]
            workflow_durations = [w["workflow_duration"] for w in successes if "workflow_duration" in w]
            commit_durations = [w["commit_duration"] for w in successes if "commit_duration" in w]

            def duration_summary(values):
                if not values:
                    return {}
                return {
                    "mean": sum(values) / len(values),
                    "median": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99),
                    "mean_95_ci": self._mean_confidence_interval(values),
                }

            return {
                "attempts": len(attempts),
                "successes": len(successes),
                "failures": len(attempts) - len(successes),
                "workflow_duration": duration_summary(workflow_durations),
                "commit_duration": duration_summary(commit_durations),
            }

        return {
            "atomic": summarize("atomic"),
            "archival_group": summarize("archival_group"),
        }

    def print_creation_timing_summary(self, data: Dict):
        """Print latency statistics for the creation-only Locust workload."""
        summary = self.creation_timing_summary(data)
        if not any(stats["attempts"] for stats in summary.values()):
            return

        print("\n" + "=" * 70)
        print("CREATION TIMING: atomic vs Archival Group")
        print("=" * 70)
        for collection_type, stats in summary.items():
            print(f"\n{collection_type.replace('_', ' ').title()}:")
            print(f"  Attempts: {stats['attempts']}")
            print(f"  Successful: {stats['successes']}")
            print(f"  Failed: {stats['failures']}")
            for label, durations in (("Workflow", stats["workflow_duration"]), ("Commit", stats["commit_duration"])):
                if not durations:
                    continue
                ci_low, ci_high = durations["mean_95_ci"]
                print(f"  {label} Mean: {durations['mean']:.4f}s (95% CI {ci_low:.4f}s to {ci_high:.4f}s)")
                print(f"  {label} Median/P95/P99: {durations['median']:.4f}s / {durations['p95']:.4f}s / {durations['p99']:.4f}s")
        print("=" * 70 + "\n")
    
    def print_comparison(self, data: Dict):
        """
        Print a formatted comparison of atomic vs AG collection performance
        
        Args:
            data: Statistics data from a run
        """

        self.print_creation_timing_summary(data)

        # Print storage-growth creation comparison first
        self.print_creation_comparison(data)

        comparison = self.compare_patch_operations(data)
        
        print("\n" + "=" * 70)
        print("PATCH OPERATION COMPARISON: atomic vs Archival Group Collections")
        print("=" * 70)
        
        for coll_type, stats in comparison.items():
            if not stats:
                continue
                
            print(f"\n{coll_type.replace('_', ' ').title()}:")
            print(f"  Operations: {stats['count']}")
            print(f"  Avg Patch Duration: {stats['avg_patch_duration']:.4f}s")
            print(f"  Avg File Count Delta: {stats['avg_file_count_delta']:.2f}")
            print(f"  Avg Directory Count Delta: {stats['avg_dir_count_delta']:.2f}")
            print(f"  Avg Size Delta: {stats['avg_size_delta']:.2f} bytes")
            print(f"  Total Size Delta: {stats['total_size_delta']:.2f} bytes")
            
            # Growth rate information
            if stats.get('size_growth_rate') is not None:
                print(f"\n  Storage Growth Rate: {stats['size_growth_rate']:.2f} bytes/update")
                print(f"  First Patch Size Delta: {stats['first_patch_size_delta']} bytes")
                print(f"  Last Patch Size Delta: {stats['last_patch_size_delta']} bytes")
                if stats['count'] > 1:
                    delta_growth = stats['last_patch_size_delta'] - stats['first_patch_size_delta']
                    print(f"  Delta Growth: {delta_growth} bytes over {stats['count']} updates")
                    print(f"    (i.e., each update's delta increased by ~{stats['size_growth_rate']:.2f} bytes)")
                
                # Expected cumulative storage after 100 updates
                # This is an arithmetic series: sum of (first_delta + 0*growth), (first_delta + 1*growth), ..., (first_delta + 99*growth)
                # Formula: n * first_term + growth_rate * n * (n-1) / 2
                n = 100
                first_delta = stats['first_patch_size_delta']
                growth_rate = stats['size_growth_rate']
                expected_100 = n * first_delta + growth_rate * n * (n - 1) / 2
                print(f"  Expected Cumulative Storage After 100 Updates: {expected_100:,.0f} bytes ({expected_100/1024:,.1f} KB)")
                print(f"    (This is the total storage added across all 100 updates)")
        
        
        # Compare if both exist
        if comparison.get("atomic_collection") and comparison.get("archival_group_collection"):
            print("\n" + "-" * 70)
            print("COMPARISON:")
            atomic = comparison["atomic_collection"]
            ag = comparison["archival_group_collection"]
            
            duration_diff = ((ag["avg_patch_duration"] - atomic["avg_patch_duration"]) / atomic["avg_patch_duration"]) * 100
            size_diff = ((ag["avg_size_delta"] - atomic["avg_size_delta"]) / atomic["avg_size_delta"]) * 100 if atomic["avg_size_delta"] > 0 else 0
            
            print(f"  AG Duration vs atomic: {duration_diff:+.1f}%")
            print(f"  AG Size Delta vs atomic: {size_diff:+.1f}%")
            
            # Growth rate comparison
            if atomic.get('size_growth_rate') is not None and ag.get('size_growth_rate') is not None:
                growth_rate_diff = ((ag['size_growth_rate'] - atomic['size_growth_rate']) / atomic['size_growth_rate']) * 100
                print(f"\n  Storage Growth Rate Comparison:")
                print(f"    Atomic: {atomic['size_growth_rate']:.2f} bytes/update")
                print(f"    AG: {ag['size_growth_rate']:.2f} bytes/update")
                print(f"    AG Growth Rate vs atomic: {growth_rate_diff:+.1f}%")
                
                print(f"\n  Expected Cumulative Storage After 100 Updates:")
                # Arithmetic series sum: n * first_term + growth_rate * n * (n-1) / 2
                n = 100
                atomic_first = atomic['first_patch_size_delta']
                atomic_growth = atomic['size_growth_rate']
                atomic_100 = n * atomic_first + atomic_growth * n * (n - 1) / 2
                
                ag_first = ag['first_patch_size_delta']
                ag_growth = ag['size_growth_rate']
                ag_100 = n * ag_first + ag_growth * n * (n - 1) / 2
                
                cumulative_diff = ag_100 - atomic_100
                print(f"    Atomic: {atomic_100:,.0f} bytes ({atomic_100/1024:,.1f} KB)")
                print(f"    AG: {ag_100:,.0f} bytes ({ag_100/1024:,.1f} KB)")
                print(f"    Difference: {cumulative_diff:+,.0f} bytes ({cumulative_diff/1024:+.1f} KB)")
        
        
        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Example usage
    import sys
    
    # Allow specifying config name as command-line argument
    # If not provided, uses TEST_CONFIG_NAME from environment
    config_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    analyzer = StatsAnalyzer(config_name=config_name)
    
    print(f"Analyzing config: '{analyzer.config_name}'")
    print(f"Results directory: '{analyzer.results_dir}'")
    
    runs = analyzer.list_available_runs()
    if runs:
        print(f"Found {len(runs)} test run(s)")
        print(f"Latest run: {runs[-1]}")
        
        # Load and analyze latest run
        data = analyzer.load_latest_run()
        analyzer.print_comparison(data)
    else:
        print(f"No statistics files found in '{analyzer.results_dir}' directory")
