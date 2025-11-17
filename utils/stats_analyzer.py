"""
Utility for analyzing and comparing statistics from multiple test runs
"""
import json
import os
from glob import glob
from datetime import datetime
from typing import List, Dict


class StatsAnalyzer:
    """
    Load and analyze statistics from previous test runs
    """
    
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
    
    def list_available_runs(self) -> List[str]:
        """
        List all available statistics files
        
        Returns:
            List of filenames
        """
        pattern = os.path.join(self.results_dir, "stats_*.json")
        files = glob(pattern)
        return sorted([os.path.basename(f) for f in files])
    
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
            Dictionary with analysis of normal vs AG collections
        """
        workflows = data.get("workflows", [])
        
        normal_patches = [w for w in workflows if w.get("operation") == "patch_collection" 
                         and w.get("collection_type") == "normal"]
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
            "normal_collection": analyze_patches(normal_patches),
            "archival_group_collection": analyze_patches(ag_patches)
        }
    
    def print_comparison(self, data: Dict):
        """
        Print a formatted comparison of normal vs AG collection performance
        
        Args:
            data: Statistics data from a run
        """
        comparison = self.compare_patch_operations(data)
        
        print("\n" + "=" * 70)
        print("PATCH OPERATION COMPARISON: Normal vs Archival Group Collections")
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
                    total_growth = stats['last_patch_size_delta'] - stats['first_patch_size_delta']
                    print(f"  Total Growth: {total_growth} bytes over {stats['count']} updates")
        
        # Compare if both exist
        if comparison.get("normal_collection") and comparison.get("archival_group_collection"):
            print("\n" + "-" * 70)
            print("COMPARISON:")
            normal = comparison["normal_collection"]
            ag = comparison["archival_group_collection"]
            
            duration_diff = ((ag["avg_patch_duration"] - normal["avg_patch_duration"]) / normal["avg_patch_duration"]) * 100
            size_diff = ((ag["avg_size_delta"] - normal["avg_size_delta"]) / normal["avg_size_delta"]) * 100 if normal["avg_size_delta"] > 0 else 0
            
            print(f"  AG Duration vs Normal: {duration_diff:+.1f}%")
            print(f"  AG Size Delta vs Normal: {size_diff:+.1f}%")
            
            # Growth rate comparison
            if normal.get('size_growth_rate') is not None and ag.get('size_growth_rate') is not None:
                growth_rate_diff = ((ag['size_growth_rate'] - normal['size_growth_rate']) / normal['size_growth_rate']) * 100
                print(f"\n  Storage Growth Rate Comparison:")
                print(f"    Normal: {normal['size_growth_rate']:.2f} bytes/update")
                print(f"    AG: {ag['size_growth_rate']:.2f} bytes/update")
                print(f"    AG Growth Rate vs Normal: {growth_rate_diff:+.1f}%")
                print(f"\n  After 100 updates, expected cumulative storage difference:")
                cumulative_diff = (ag['size_growth_rate'] - normal['size_growth_rate']) * 100
                print(f"    {cumulative_diff:+.0f} bytes ({cumulative_diff/1024:+.1f} KB)")
        
        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Example usage
    analyzer = StatsAnalyzer()
    
    runs = analyzer.list_available_runs()
    if runs:
        print(f"Found {len(runs)} test run(s)")
        print(f"Latest run: {runs[-1]}")
        
        # Load and analyze latest run
        data = analyzer.load_latest_run()
        analyzer.print_comparison(data)
    else:
        print("No statistics files found in results/ directory")
