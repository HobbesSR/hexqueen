"""
Test module for the advanced puzzle solver.
"""
import time
import random
from typing import Dict, Set, Tuple

from hex_grid import HexGrid, HexCoord
from solver import PuzzleSolver
from advanced_solver import AdvancedPuzzleSolver
from src.puzzle_visualizer import generate_puzzle_with_queens, draw_hex_grid
import matplotlib.pyplot as plt

def create_test_puzzle(grid_radius: int = 3, seed: int = 42) -> Tuple[HexGrid, Dict[int, HexCoord], Dict[HexCoord, int]]:
    """
    Create a test puzzle with queens.
    
    Args:
        grid_radius: Radius of the hexagonal grid
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (grid, queen_positions, cell_regions)
    """
    grid = HexGrid(grid_radius)
    success, grid, cell_regions, queen_positions = generate_puzzle_with_queens(grid, seed)
    
    if not success:
        raise ValueError("Failed to generate a valid puzzle")
    
    return grid, queen_positions, cell_regions

def compare_solvers(grid: HexGrid, queen_positions: Dict[int, HexCoord], num_queens: int):
    """
    Compare the basic and advanced solvers.
    
    Args:
        grid: The hexagonal grid
        queen_positions: Mapping of queen IDs to their positions
        num_queens: Number of queens/regions
    """
    print("\n=== Comparing Basic and Advanced Solvers ===")
    
    # Basic solver
    basic_solver = PuzzleSolver(grid, num_queens)
    basic_solver.initialize_from_clues(queen_positions)
    
    start_time = time.time()
    basic_solved = basic_solver.solve()
    basic_time = time.time() - start_time
    
    basic_metrics = basic_solver.get_metrics()
    
    # Advanced solver
    advanced_solver = AdvancedPuzzleSolver(grid, num_queens)
    advanced_solver.initialize_from_clues(queen_positions)
    
    start_time = time.time()
    advanced_solved = advanced_solver.solve()
    advanced_time = time.time() - start_time
    
    advanced_metrics = advanced_solver.get_metrics()
    
    # Print results
    print("\n--- Basic Solver ---")
    print(f"Solved: {basic_solved}")
    print(f"Time: {basic_time:.4f} seconds")
    print("Metrics:")
    for key, value in basic_metrics.items():
        print(f"  {key}: {value}")
    
    print("\n--- Advanced Solver ---")
    print(f"Solved: {advanced_solved}")
    print(f"Time: {advanced_time:.4f} seconds")
    print("Metrics:")
    for key, value in advanced_metrics.items():
        print(f"  {key}: {value}")
    
    # Compare solutions if both solved
    if basic_solved and advanced_solved:
        basic_solution = basic_solver.get_solution()
        advanced_solution = advanced_solver.get_solution()
        
        if basic_solution == advanced_solution:
            print("\nBoth solvers found the same solution.")
        else:
            print("\nSolvers found different solutions.")
            
            # Count differences
            diff_count = sum(1 for cell in basic_solution if cell in advanced_solution and basic_solution[cell] != advanced_solution[cell])
            print(f"Number of differences: {diff_count}")
    
    # Return the solutions for visualization
    return (basic_solved, basic_solver.get_solution() if basic_solved else None,
            advanced_solved, advanced_solver.get_solution() if advanced_solved else None)

def test_specific_techniques():
    """Test specific advanced techniques with crafted examples."""
    print("\n=== Testing Specific Advanced Techniques ===")
    
    # Test Region Bridging
    print("\n--- Testing Region Bridging ---")
    grid = HexGrid(2)  # Small grid for testing
    
    # Create a scenario where region bridging is needed
    # Region 0 has cells at opposite sides with a single connecting path
    solver = AdvancedPuzzleSolver(grid, 2)  # 2 regions
    
    # Initialize with some fixed cells
    piece_positions = {0: HexCoord(0, 0, 0), 1: HexCoord(2, -1, -1)}
    fixed_cells = {
        HexCoord(-2, 1, 1): 0,  # Region 0 on one side
        HexCoord(2, -2, 0): 0,  # Region 0 on the other side
        # The bridge cell will be HexCoord(0, -1, 1)
    }
    
    solver.initialize_from_clues(piece_positions, fixed_cells)
    
    # Apply region bridging technique
    print("Before region bridging:")
    for cell, candidates in solver.cell_candidates.items():
        if cell not in solver.assigned_cells and 0 in candidates:
            print(f"  {cell}: {candidates}")
    
    result = solver.apply_region_bridging_technique()
    
    print(f"Region bridging made progress: {result}")
    print("After region bridging:")
    for cell, candidates in solver.cell_candidates.items():
        if cell not in solver.assigned_cells and 0 in candidates:
            print(f"  {cell}: {candidates}")
    
    # Test Critical Cut Detection
    print("\n--- Testing Critical Cut Detection ---")
    grid = HexGrid(2)
    solver = AdvancedPuzzleSolver(grid, 2)
    
    # Initialize with some fixed cells creating a critical cut scenario
    piece_positions = {0: HexCoord(0, 0, 0), 1: HexCoord(2, -1, -1)}
    fixed_cells = {
        HexCoord(-2, 1, 1): 0,  # Region 0 on one side
        HexCoord(2, -2, 0): 0,  # Region 0 on the other side
        # Critical cut cells: HexCoord(0, -1, 1), HexCoord(1, -1, 0)
    }
    
    solver.initialize_from_clues(piece_positions, fixed_cells)
    
    # Apply critical cut detection
    print("Before critical cut detection:")
    for cell, candidates in solver.cell_candidates.items():
        if cell not in solver.assigned_cells and 0 in candidates:
            print(f"  {cell}: {candidates}")
    
    result = solver.apply_critical_cut_detection()
    
    print(f"Critical cut detection made progress: {result}")
    print("After critical cut detection:")
    for cell, candidates in solver.cell_candidates.items():
        if cell not in solver.assigned_cells and 0 in candidates:
            print(f"  {cell}: {candidates}")

def main():
    """Main function to run tests."""
    # Set random seed for reproducibility
    random.seed(42)
    
    # Create a test puzzle
    grid_radius = 3
    grid, queen_positions, cell_regions = create_test_puzzle(grid_radius)
    num_queens = len(queen_positions)
    
    print(f"Created test puzzle with radius {grid_radius} and {num_queens} queens")
    
    # Compare solvers
    basic_solved, basic_solution, advanced_solved, advanced_solution = compare_solvers(
        grid, queen_positions, num_queens
    )
    
    # Visualize solutions
    if basic_solved and advanced_solved:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        
        draw_hex_grid(ax1, grid, basic_solution, queen_positions, 
                     title="Basic Solver Solution")
        
        draw_hex_grid(ax2, grid, advanced_solution, queen_positions,
                     title="Advanced Solver Solution")
        
        plt.tight_layout()
        plt.savefig("solver_comparison.png")
        print("Solver comparison visualization saved as 'solver_comparison.png'")
    
    # Test specific techniques
    test_specific_techniques()

if __name__ == "__main__":
    main()