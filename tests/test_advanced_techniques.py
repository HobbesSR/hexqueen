"""
Test module for demonstrating the advanced solver techniques with specific puzzle configurations.
"""
import time
import matplotlib.pyplot as plt
from typing import Dict, Set

from hex_grid import HexGrid, HexCoord
from solver import PuzzleSolver
from advanced_solver import AdvancedPuzzleSolver
from src.puzzle_visualizer import draw_hex_grid

def test_region_bridging():
    """
    Test the region bridging technique with a specific puzzle configuration.
    """
    print("\n=== Testing Region Bridging Technique ===")
    
    # Create a small grid
    grid = HexGrid(2)
    
    # Create a puzzle with 2 regions where region bridging is needed
    piece_positions = {
        0: HexCoord(0, 0, 0),  # Center
        1: HexCoord(2, -1, -1)  # Edge
    }
    
    # Fixed cells that create a scenario where region bridging is needed
    fixed_cells = {
        HexCoord(-2, 1, 1): 0,  # Region 0 on one side
        HexCoord(2, -2, 0): 0,  # Region 0 on the other side
        # The bridge cell will be HexCoord(0, -1, 1) or similar
    }
    
    # Compare basic and advanced solvers
    basic_solver = PuzzleSolver(grid, 2)
    basic_solver.initialize_from_clues(piece_positions, fixed_cells)
    
    print("Basic solver initial state:")
    print_region_candidates(basic_solver, 0)
    
    start_time = time.time()
    basic_result = basic_solver.apply_logical_techniques()
    basic_time = time.time() - start_time
    
    print(f"\nBasic solver after logical techniques (time: {basic_time:.4f}s):")
    print_region_candidates(basic_solver, 0)
    
    # Advanced solver
    advanced_solver = AdvancedPuzzleSolver(grid, 2)
    advanced_solver.initialize_from_clues(piece_positions, fixed_cells)
    
    print("\nAdvanced solver initial state:")
    print_region_candidates(advanced_solver, 0)
    
    start_time = time.time()
    advanced_result = advanced_solver.apply_logical_techniques()
    advanced_time = time.time() - start_time
    
    print(f"\nAdvanced solver after logical techniques (time: {advanced_time:.4f}s):")
    print_region_candidates(advanced_solver, 0)
    
    # Visualize the results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Basic solver result
    draw_hex_grid(ax1, grid, basic_solver.assigned_cells, piece_positions, 
                 title="Basic Solver Result")
    
    # Advanced solver result
    draw_hex_grid(ax2, grid, advanced_solver.assigned_cells, piece_positions,
                 title="Advanced Solver Result")
    
    plt.tight_layout()
    plt.savefig("region_bridging_comparison.png")
    print("\nVisualization saved as 'region_bridging_comparison.png'")
    
    return basic_solver, advanced_solver

def test_critical_cut_detection():
    """
    Test the critical cut detection technique with a specific puzzle configuration.
    """
    print("\n=== Testing Critical Cut Detection Technique ===")
    
    # Create a small grid
    grid = HexGrid(2)
    
    # Create a puzzle with 2 regions where critical cut detection is needed
    piece_positions = {
        0: HexCoord(-2, 1, 1),  # Edge
        1: HexCoord(2, -1, -1)   # Opposite edge
    }
    
    # Fixed cells that create a scenario where critical cut detection is needed
    fixed_cells = {
        HexCoord(-1, 2, -1): 0,  # Region 0 on one side
        HexCoord(0, -2, 2): 0,   # Region 0 on another side
        # The critical cut cells will be in the middle
    }
    
    # Compare basic and advanced solvers
    basic_solver = PuzzleSolver(grid, 2)
    basic_solver.initialize_from_clues(piece_positions, fixed_cells)
    
    print("Basic solver initial state:")
    print_region_candidates(basic_solver, 0)
    
    start_time = time.time()
    basic_result = basic_solver.apply_logical_techniques()
    basic_time = time.time() - start_time
    
    print(f"\nBasic solver after logical techniques (time: {basic_time:.4f}s):")
    print_region_candidates(basic_solver, 0)
    
    # Advanced solver
    advanced_solver = AdvancedPuzzleSolver(grid, 2)
    advanced_solver.initialize_from_clues(piece_positions, fixed_cells)
    
    print("\nAdvanced solver initial state:")
    print_region_candidates(advanced_solver, 0)
    
    start_time = time.time()
    advanced_result = advanced_solver.apply_logical_techniques()
    advanced_time = time.time() - start_time
    
    print(f"\nAdvanced solver after logical techniques (time: {advanced_time:.4f}s):")
    print_region_candidates(advanced_solver, 0)
    
    # Visualize the results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Basic solver result
    draw_hex_grid(ax1, grid, basic_solver.assigned_cells, piece_positions, 
                 title="Basic Solver Result")
    
    # Advanced solver result
    draw_hex_grid(ax2, grid, advanced_solver.assigned_cells, piece_positions,
                 title="Advanced Solver Result")
    
    plt.tight_layout()
    plt.savefig("critical_cut_comparison.png")
    print("\nVisualization saved as 'critical_cut_comparison.png'")
    
    return basic_solver, advanced_solver

def test_forcing_chains():
    """
    Test the forcing chains technique with a specific puzzle configuration.
    """
    print("\n=== Testing Forcing Chains Technique ===")
    
    # Create a small grid
    grid = HexGrid(2)
    
    # Create a puzzle with 2 regions where forcing chains are needed
    piece_positions = {
        0: HexCoord(0, 0, 0),  # Center
        1: HexCoord(2, -1, -1)  # Edge
    }
    
    # Fixed cells that create a scenario where forcing chains are needed
    fixed_cells = {
        HexCoord(-2, 1, 1): 0,  # Region 0
        HexCoord(1, -2, 1): 1,  # Region 1
        HexCoord(-1, 2, -1): 1, # Region 1
        # The forcing chain will propagate through the remaining cells
    }
    
    # Compare basic and advanced solvers
    basic_solver = PuzzleSolver(grid, 2)
    basic_solver.initialize_from_clues(piece_positions, fixed_cells)
    
    print("Basic solver initial state:")
    print_all_candidates(basic_solver)
    
    start_time = time.time()
    basic_result = basic_solver.apply_logical_techniques()
    basic_time = time.time() - start_time
    
    print(f"\nBasic solver after logical techniques (time: {basic_time:.4f}s):")
    print_all_candidates(basic_solver)
    
    # Advanced solver
    advanced_solver = AdvancedPuzzleSolver(grid, 2)
    advanced_solver.initialize_from_clues(piece_positions, fixed_cells)
    
    print("\nAdvanced solver initial state:")
    print_all_candidates(advanced_solver)
    
    start_time = time.time()
    advanced_result = advanced_solver.apply_logical_techniques()
    advanced_time = time.time() - start_time
    
    print(f"\nAdvanced solver after logical techniques (time: {advanced_time:.4f}s):")
    print_all_candidates(advanced_solver)
    
    # Visualize the results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Basic solver result
    draw_hex_grid(ax1, grid, basic_solver.assigned_cells, piece_positions, 
                 title="Basic Solver Result")
    
    # Advanced solver result
    draw_hex_grid(ax2, grid, advanced_solver.assigned_cells, piece_positions,
                 title="Advanced Solver Result")
    
    plt.tight_layout()
    plt.savefig("forcing_chains_comparison.png")
    print("\nVisualization saved as 'forcing_chains_comparison.png'")
    
    return basic_solver, advanced_solver

def print_region_candidates(solver, region_id):
    """Print cells that are candidates for a specific region."""
    print(f"Cells assigned to region {region_id}:")
    for cell in solver.region_cells[region_id]:
        print(f"  {cell}")
    
    print(f"Candidate cells for region {region_id}:")
    for cell, candidates in solver.cell_candidates.items():
        if cell not in solver.assigned_cells and region_id in candidates:
            print(f"  {cell}: {candidates}")

def print_all_candidates(solver):
    """Print all cell candidates."""
    print("All cell candidates:")
    for cell, candidates in solver.cell_candidates.items():
        if cell not in solver.assigned_cells:
            print(f"  {cell}: {candidates}")

def main():
    """Main function to run tests."""
    # Test region bridging
    basic_rb, advanced_rb = test_region_bridging()
    
    # Test critical cut detection
    basic_cc, advanced_cc = test_critical_cut_detection()
    
    # Test forcing chains
    basic_fc, advanced_fc = test_forcing_chains()
    
    # Print metrics
    print("\n=== Solver Metrics ===")
    
    print("\nRegion Bridging Test:")
    print("Basic solver metrics:", basic_rb.metrics)
    print("Advanced solver metrics:", advanced_rb.metrics)
    
    print("\nCritical Cut Test:")
    print("Basic solver metrics:", basic_cc.metrics)
    print("Advanced solver metrics:", advanced_cc.metrics)
    
    print("\nForcing Chains Test:")
    print("Basic solver metrics:", basic_fc.metrics)
    print("Advanced solver metrics:", advanced_fc.metrics)

if __name__ == "__main__":
    main()