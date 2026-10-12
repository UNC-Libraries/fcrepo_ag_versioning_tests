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

    def load_combined_runs(self) -> Dict:
        """Combine records from every saved run in this configuration."""
        runs = self.list_available_runs()
        if not runs:
            raise ValueError("No statistics files found")

        combined = {
            "run_metadata": {"source_runs": runs},
            "summary": {},
            "responses": [],
            "creations": [],
            "workflows": [],
        }
        for run in runs:
            data = self.load_run(run)
            for key in ("responses", "creations", "workflows"):
                combined[key].extend(data.get(key, []))

        return combined
    
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
            sequences = {}
            for index, patch in enumerate(patches):
                # update_counter restarts for every created collection, including in later runs.
                collection_id = patch.get("collection_id", f"unknown-{index}")
                sequences.setdefault(collection_id, []).append(patch)

            sequence_slopes = []
            sequence_projections = []
            first_deltas = []
            last_deltas = []
            for sequence in sequences.values():
                ordered = sorted(sequence, key=lambda p: p.get("update_counter", 0))
                size_deltas = [p.get("patch_collection_ocfl_size_delta", 0) for p in ordered]
                first_deltas.append(size_deltas[0])
                last_deltas.append(size_deltas[-1])
                if len(size_deltas) < 2:
                    continue

                x_values = [p.get("update_counter", index + 1) for index, p in enumerate(ordered)]
                x_mean = sum(x_values) / len(x_values)
                y_mean = sum(size_deltas) / len(size_deltas)
                denominator = sum((x - x_mean) ** 2 for x in x_values)
                if not denominator:
                    continue

                slope = sum(
                    (x - x_mean) * (y - y_mean)
                    for x, y in zip(x_values, size_deltas)
                ) / denominator
                sequence_slopes.append(slope)
                updates = 100
                sequence_projections.append(
                    updates * size_deltas[0] + slope * updates * (updates - 1) / 2
                )

            return {
                "count": len(patches),
                "sequence_count": len(sequences),
                "growth_sequence_count": len(sequence_slopes),
                "avg_patch_duration": sum(p.get("patch_duration", 0) for p in patches) / len(patches),
                "avg_file_count_delta": sum(p.get("patch_collection_ocfl_count_delta", 0) for p in patches) / len(patches),
                "avg_dir_count_delta": sum(p.get("patch_collection_ocfl_directories_delta", 0) for p in patches) / len(patches),
                "avg_size_delta": sum(p.get("patch_collection_ocfl_size_delta", 0) for p in patches) / len(patches),
                "total_size_delta": sum(p.get("patch_collection_ocfl_size_delta", 0) for p in patches),
                "size_growth_rate": sum(sequence_slopes) / len(sequence_slopes) if sequence_slopes else None,
                "avg_first_patch_size_delta": sum(first_deltas) / len(first_deltas),
                "avg_last_patch_size_delta": sum(last_deltas) / len(last_deltas),
                "expected_100_size_delta": sum(sequence_projections) / len(sequence_projections) if sequence_projections else None,
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
            print(f"  Collection Sequences: {stats['sequence_count']}")
            print(f"  Avg Patch Duration: {stats['avg_patch_duration']:.4f}s")
            print(f"  Avg File Count Delta: {stats['avg_file_count_delta']:.2f}")
            print(f"  Avg Directory Count Delta: {stats['avg_dir_count_delta']:.2f}")
            print(f"  Avg Size Delta: {stats['avg_size_delta']:.2f} bytes")
            print(f"  Total Size Delta: {stats['total_size_delta']:.2f} bytes")
            
            # Growth rate information
            if stats.get('size_growth_rate') is not None:
                print(f"\n  Mean Storage Growth Rate: {stats['size_growth_rate']:.2f} bytes/update")
                print(f"    ({stats['growth_sequence_count']} sequence(s) with at least two PATCHes)")
                print(f"  Mean First Patch Size Delta: {stats['avg_first_patch_size_delta']:.2f} bytes")
                print(f"  Mean Last Patch Size Delta: {stats['avg_last_patch_size_delta']:.2f} bytes")
                print(f"  Mean Projected Cumulative Storage After 100 Updates: {stats['expected_100_size_delta']:,.0f} bytes ({stats['expected_100_size_delta']/1024:,.1f} KB)")
        
        
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
                
                print(f"\n  Mean Projected Cumulative Storage After 100 Updates:")
                cumulative_diff = ag['expected_100_size_delta'] - atomic['expected_100_size_delta']
                print(f"    Atomic: {atomic['expected_100_size_delta']:,.0f} bytes ({atomic['expected_100_size_delta']/1024:,.1f} KB)")
                print(f"    AG: {ag['expected_100_size_delta']:,.0f} bytes ({ag['expected_100_size_delta']/1024:,.1f} KB)")
                print(f"    Difference: {cumulative_diff:+,.0f} bytes ({cumulative_diff/1024:+.1f} KB)")
        
        
        print("=" * 70 + "\n")

    @staticmethod
    def _print_metric_change(label: str, reference: float, comparison: float, unit: str = ""):
        """Print a per-operation metric change without treating sample counts as a metric."""
        difference = comparison - reference
        if reference > 0:
            relative_change = f"{difference / reference * 100:+.1f}%"
        else:
            relative_change = "n/a (reference is not positive)"
        print(
            f"  {label}: {reference:.4f}{unit} -> {comparison:.4f}{unit} "
            f"({difference:+.4f}{unit}, {relative_change})"
        )

    def print_result_set_comparison(
        self,
        reference_data: Dict,
        comparison_data: Dict,
        reference_name: str,
        comparison_name: str,
    ):
        """Print normalized workflow and OCFL-delta changes across two result sets."""
        print("\n" + "=" * 70)
        print("RESULT SET CHANGE")
        print("=" * 70)
        print(f"Reference: {reference_name}")
        print(f"Comparison: {comparison_name}")
        print("A negative duration change means the comparison result set is faster.")

        reference_timing = self.creation_timing_summary(reference_data)
        comparison_timing = self.creation_timing_summary(comparison_data)
        for collection_type in ("atomic", "archival_group"):
            reference = reference_timing[collection_type]
            comparison = comparison_timing[collection_type]
            if not reference["attempts"] or not comparison["attempts"]:
                continue

            print(f"\nCreation timing, {collection_type.replace('_', ' ')}:")
            print(
                f"  Attempts (context only): {reference['attempts']} -> {comparison['attempts']}; "
                f"failures: {reference['failures']} -> {comparison['failures']}"
            )
            for label, key in (("Workflow", "workflow_duration"), ("Commit", "commit_duration")):
                reference_durations = reference[key]
                comparison_durations = comparison[key]
                if not reference_durations or not comparison_durations:
                    continue
                self._print_metric_change(f"{label} mean", reference_durations["mean"], comparison_durations["mean"], "s")
                self._print_metric_change(f"{label} median", reference_durations["median"], comparison_durations["median"], "s")
                self._print_metric_change(f"{label} p95", reference_durations["p95"], comparison_durations["p95"], "s")
                self._print_metric_change(f"{label} p99", reference_durations["p99"], comparison_durations["p99"], "s")

        metric_labels = (
            ("avg_workflow_duration", "Average workflow duration", "s"),
            ("avg_commit_duration", "Average commit duration", "s"),
            ("avg_file_count_delta", "Average file delta", " files"),
            ("avg_dir_count_delta", "Average directory delta", " directories"),
            ("avg_size_delta", "Average OCFL size delta", " bytes"),
        )
        reference_creations = self.compare_creation_operations(reference_data)
        comparison_creations = self.compare_creation_operations(comparison_data)
        for collection_type in ("atomic_collection", "archival_group_collection"):
            reference = reference_creations[collection_type]
            comparison = comparison_creations[collection_type]
            if not reference or not comparison:
                continue

            print(f"\nCollection creation storage, {collection_type.replace('_collection', '').replace('_', ' ')}:")
            print(f"  Operations (context only): {reference['count']} -> {comparison['count']}")
            for key, label, unit in metric_labels:
                self._print_metric_change(label, reference[key], comparison[key], unit)

        patch_metric_labels = (
            ("avg_patch_duration", "Average PATCH duration", "s"),
            ("avg_file_count_delta", "Average file delta", " files"),
            ("avg_dir_count_delta", "Average directory delta", " directories"),
            ("avg_size_delta", "Average OCFL size delta", " bytes"),
            ("size_growth_rate", "OCFL growth rate", " bytes/update"),
        )
        reference_patches = self.compare_patch_operations(reference_data)
        comparison_patches = self.compare_patch_operations(comparison_data)
        for collection_type in ("atomic_collection", "archival_group_collection"):
            reference = reference_patches[collection_type]
            comparison = comparison_patches[collection_type]
            if not reference or not comparison:
                continue

            print(f"\nPATCH storage, {collection_type.replace('_collection', '').replace('_', ' ')}:")
            print(f"  Operations (context only): {reference['count']} -> {comparison['count']}")
            for key, label, unit in patch_metric_labels:
                if reference.get(key) is not None and comparison.get(key) is not None:
                    self._print_metric_change(label, reference[key], comparison[key], unit)

        print("=" * 70 + "\n")

    @staticmethod
    def _markdown_table(headers: List[str], rows: List[List[str]]) -> List[str]:
        """Build a simple GitHub-flavored Markdown table."""
        return [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *["| " + " | ".join(row) + " |" for row in rows],
        ]

    @staticmethod
    def _markdown_change(reference: float, comparison: float, unit: str = "") -> str:
        """Format an absolute and relative change for Markdown output."""
        difference = comparison - reference
        relative = f"{difference / reference * 100:+.1f}%" if reference > 0 else "n/a"
        return f"{difference:+.4f}{unit} ({relative})"

    def _markdown_config_report(self, config_name: str, data: Dict) -> List[str]:
        """Render one configuration's pooled results as Markdown tables."""
        lines = [f"## {config_name}"]
        source_runs = data.get("run_metadata", {}).get("source_runs", [])
        lines.append(f"Pooled runs: **{len(source_runs)}** ({', '.join(f'`{run}`' for run in source_runs)})")

        timing = self.creation_timing_summary(data)
        if any(stats["attempts"] for stats in timing.values()):
            lines.extend(["", "### Creation Timing"])
            rows = []
            for collection_type, stats in timing.items():
                workflow = stats["workflow_duration"]
                commit = stats["commit_duration"]
                workflow_mean = "n/a"
                commit_mean = "n/a"
                if workflow:
                    low, high = workflow["mean_95_ci"]
                    workflow_mean = f"{workflow['mean']:.4f}s ({low:.4f}s to {high:.4f}s)"
                if commit:
                    low, high = commit["mean_95_ci"]
                    commit_mean = f"{commit['mean']:.4f}s ({low:.4f}s to {high:.4f}s)"
                rows.append([
                    collection_type.replace("_", " ").title(),
                    str(stats["successes"]),
                    str(stats["failures"]),
                    workflow_mean,
                    f"{workflow['median']:.4f}s / {workflow['p95']:.4f}s / {workflow['p99']:.4f}s" if workflow else "n/a",
                    commit_mean,
                    f"{commit['median']:.4f}s / {commit['p95']:.4f}s / {commit['p99']:.4f}s" if commit else "n/a",
                ])
            lines.extend(self._markdown_table(
                ["Collection type", "Successful", "Failed", "Workflow mean (95% CI)", "Workflow median / p95 / p99", "Commit mean (95% CI)", "Commit median / p95 / p99"],
                rows,
            ))

        creations = self.compare_creation_operations(data)
        if any(creations.values()):
            lines.extend(["", "### Collection Creation Storage"])
            rows = []
            for collection_type, stats in creations.items():
                if not stats:
                    continue
                rows.append([
                    collection_type.replace("_collection", "").replace("_", " ").title(),
                    str(stats["count"]),
                    f"{stats['avg_workflow_duration']:.4f}s",
                    f"{stats['avg_commit_duration']:.4f}s",
                    f"{stats['avg_file_count_delta']:.2f}",
                    f"{stats['avg_dir_count_delta']:.2f}",
                    f"{stats['avg_size_delta']:,.0f} bytes ({stats['avg_size_delta'] / 1024:.2f} KB)",
                ])
            lines.extend(self._markdown_table(
                ["Collection type", "Collections", "Avg workflow", "Avg commit", "Avg files", "Avg directories", "Avg OCFL size"],
                rows,
            ))

        patches = self.compare_patch_operations(data)
        if any(patches.values()):
            lines.extend(["", "### PATCH Storage"])
            rows = []
            for collection_type, stats in patches.items():
                if not stats:
                    continue
                growth = "n/a"
                projection = "n/a"
                if stats["size_growth_rate"] is not None:
                    growth = f"{stats['size_growth_rate']:,.2f} bytes/update"
                    projection = f"{stats['expected_100_size_delta']:,.0f} bytes ({stats['expected_100_size_delta'] / 1024:,.1f} KB)"
                rows.append([
                    collection_type.replace("_collection", "").replace("_", " ").title(),
                    str(stats["count"]),
                    str(stats["sequence_count"]),
                    f"{stats['avg_patch_duration']:.4f}s",
                    f"{stats['avg_file_count_delta']:.2f} / {stats['avg_dir_count_delta']:.2f} / {stats['avg_size_delta']:,.2f} bytes",
                    growth,
                    projection,
                ])
            lines.extend(self._markdown_table(
                ["Collection type", "PATCHes", "Sequences", "Avg duration", "Avg file / directory / size delta", "Mean growth rate", "Mean projected storage after 100 PATCHes"],
                rows,
            ))
        return lines

    def markdown_result_set_comparison(
        self,
        reference_data: Dict,
        comparison_data: Dict,
        reference_name: str,
        comparison_name: str,
    ) -> str:
        """Render a complete GitHub-flavored Markdown report for two result sets."""
        lines = [
            f"# Fedora Comparison: {reference_name} vs {comparison_name}",
            "",
            "Negative duration changes mean the comparison configuration is faster. "
            "Operation counts are context only; all other values are per-operation averages.",
            "",
            *self._markdown_config_report(reference_name, reference_data),
            "",
            *self._markdown_config_report(comparison_name, comparison_data),
            "",
            "## Result Set Change",
        ]

        reference_timing = self.creation_timing_summary(reference_data)
        comparison_timing = self.creation_timing_summary(comparison_data)
        timing_rows = []
        for collection_type in ("atomic", "archival_group"):
            reference = reference_timing[collection_type]
            comparison = comparison_timing[collection_type]
            if not reference["attempts"] or not comparison["attempts"]:
                continue
            timing_rows.append([
                collection_type.replace("_", " ").title(),
                f"{reference['successes']} successful, {reference['failures']} failed -> {comparison['successes']} successful, {comparison['failures']} failed",
                f"{reference['workflow_duration']['mean']:.4f}s -> {comparison['workflow_duration']['mean']:.4f}s",
                self._markdown_change(reference['workflow_duration']['mean'], comparison['workflow_duration']['mean'], "s"),
                f"{reference['commit_duration']['mean']:.4f}s -> {comparison['commit_duration']['mean']:.4f}s",
                self._markdown_change(reference['commit_duration']['mean'], comparison['commit_duration']['mean'], "s"),
            ])
        if timing_rows:
            lines.extend(["", "### Creation Timing Changes"])
            lines.extend(self._markdown_table(
                ["Collection type", "Attempts", "Workflow mean", "Workflow change", "Commit mean", "Commit change"],
                timing_rows,
            ))

        for title, method, metrics in (
            (
                "Collection Creation Storage Changes",
                self.compare_creation_operations,
                (
                    ("Avg workflow", "avg_workflow_duration", "s"),
                    ("Avg commit", "avg_commit_duration", "s"),
                    ("Avg files", "avg_file_count_delta", ""),
                    ("Avg directories", "avg_dir_count_delta", ""),
                    ("Avg OCFL size", "avg_size_delta", " bytes"),
                ),
            ),
            (
                "PATCH Storage Changes",
                self.compare_patch_operations,
                (
                    ("Avg PATCH duration", "avg_patch_duration", "s"),
                    ("Avg files", "avg_file_count_delta", ""),
                    ("Avg directories", "avg_dir_count_delta", ""),
                    ("Avg OCFL size", "avg_size_delta", " bytes"),
                    ("OCFL growth rate", "size_growth_rate", " bytes/update"),
                ),
            ),
        ):
            reference_stats = method(reference_data)
            comparison_stats = method(comparison_data)
            rows = []
            for collection_type in ("atomic_collection", "archival_group_collection"):
                reference = reference_stats[collection_type]
                comparison = comparison_stats[collection_type]
                if not reference or not comparison:
                    continue
                for label, key, unit in metrics:
                    if reference.get(key) is None or comparison.get(key) is None:
                        continue
                    rows.append([
                        collection_type.replace("_collection", "").replace("_", " ").title(),
                        label,
                        f"{reference[key]:,.4f}{unit}",
                        f"{comparison[key]:,.4f}{unit}",
                        self._markdown_change(reference[key], comparison[key], unit),
                    ])
            if rows:
                lines.extend(["", f"### {title}"])
                lines.extend(self._markdown_table(
                    ["Collection type", "Metric", reference_name, comparison_name, "Change"],
                    rows,
                ))
        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys

    def analyze_config(config_name):
        analyzer = StatsAnalyzer(config_name=config_name)
        print(f"Analyzing config: '{analyzer.config_name}'")
        print(f"Results directory: '{analyzer.results_dir}'")
        runs = analyzer.list_available_runs()
        if not runs:
            print(f"No statistics files found in '{analyzer.results_dir}' directory")
            return analyzer, None
        print(f"Found {len(runs)} test run(s)")
        print("Combining all runs")
        data = analyzer.load_combined_runs()
        analyzer.print_comparison(data)
        return analyzer, data

    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        arguments = sys.argv[2:]
        output_format = "text"
        if arguments[:2] == ["--format", "markdown"]:
            output_format = "markdown"
            arguments = arguments[2:]
        if len(arguments) != 2:
            raise SystemExit(
                "Usage: python utils/stats_analyzer.py compare [--format markdown] "
                "<reference-config> <comparison-config>"
            )

        if output_format == "markdown":
            reference_analyzer = StatsAnalyzer(config_name=arguments[0])
            comparison_analyzer = StatsAnalyzer(config_name=arguments[1])
            for analyzer in (reference_analyzer, comparison_analyzer):
                if not analyzer.list_available_runs():
                    raise SystemExit(
                        f"No statistics files found in '{analyzer.results_dir}' directory"
                    )
            reference_data = reference_analyzer.load_combined_runs()
            comparison_data = comparison_analyzer.load_combined_runs()
            print(reference_analyzer.markdown_result_set_comparison(
                reference_data,
                comparison_data,
                reference_analyzer.config_name,
                comparison_analyzer.config_name,
            ), end="")
        else:
            reference_analyzer, reference_data = analyze_config(arguments[0])
            comparison_analyzer, comparison_data = analyze_config(arguments[1])
            if reference_data and comparison_data:
                reference_analyzer.print_result_set_comparison(
                    reference_data,
                    comparison_data,
                    reference_analyzer.config_name,
                    comparison_analyzer.config_name,
                )
    else:
        config_name = sys.argv[1] if len(sys.argv) > 1 else None
        analyze_config(config_name)
