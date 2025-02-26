"""
Main module for the hexagonal puzzle solver with visualization.
"""
import argparse
import random
import time
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Set, Tuple, Optional

from .hex_grid import HexGrid, HexCoord
from .puzzle_generator import PuzzleGenerator
from .solver import PuzzleSolver
from .advanced_solver import AdvancedPuzzleSolver
from .queen_placer import QueenPlacer
from .reverse_engineering_solver import ReverseEngineeringSolver
from .puzzle_visualizer import (
    hex_to_pixel, draw_hexagon, draw_queen, get_region_color,
    grow_regions_from_queens, check_regions_contiguity,
    calculate_recommended_queens, generate_puzzle_with_queens,
    draw_hex_grid
)

def visualize_puzzle(grid: HexGrid, cell_regions: Dict[HexCoord, int], 
                     piece_positions: Dict[int, HexCoord], title: str = "Hexagonal Puzzle"):
    """
    Visualize the puzzle with regions and pieces.
    
    Args:
        grid: The hexagonal grid
        cell_regions: Mapping of cells to their regions
        piece_positions: Mapping of piece IDs to their positions
        title: Title for the plot
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    draw_hex_grid(ax, grid, cell_regions, piece_positions, show_pieces=True, title=title)
    plt.tight_layout()
    return fig

def demonstrate_queen_placement(grid_radius: int, seed: Optional[int] = None):
    """
    Demonstrate the placement of queens on a hexagonal grid, and generate a puzzle
    based on the queen positions.
    
    Args:
        grid_radius: Radius of the hexagonal grid
        seed: Random seed for reproducibility
    """
    num_queens = calculate_recommended_queens(grid_radius)
    print(f"Demonstrating queen placement with grid radius {grid_radius} and {num_queens} queens...")
    
    grid = HexGrid(grid_radius)
    placer = QueenPlacer(grid, num_queens, seed)
    
    start_time = time.time()
    success = placer.place_queens()
    placement_time = time.time() - start_time
    
    if not success:
        print(f"Failed to place {num_queens} queens on a grid of radius {grid_radius}.")
        return
    
    print(f"Queens placed successfully in {placement_time:.2f} seconds.")
    queen_positions = placer.get_queen_positions()
    
    hex_size = 0.5
    cell_regions = {}
    for cell in grid.get_all_cells():
        parity = (cell.x + cell.y + cell.z) % 2
        cell_regions[cell] = -1 - parity
    
    fig = visualize_puzzle(grid, cell_regions, queen_positions,
                         f"Queen Placement (Radius: {grid_radius}, Queens: {num_queens})")
    plt.savefig("queen_placement.png")
    print("Queen placement saved as 'queen_placement.png'")
    
    print("\nGenerating puzzle based on queen positions...")
    rng = random.Random(seed)
    success, cell_regions, regions = grow_regions_from_queens(grid, queen_positions, rng)
    
    if not success:
        print("Failed to grow regions from queen positions.")
        return
    print("Regions grown successfully.")
    
    all_contiguous = check_regions_contiguity(grid, regions)
    if all_contiguous:
        print("All regions are contiguous.")
    else:
        print("Warning: Some regions are not contiguous.")
        return
    
    region_sizes = {region_id: len(cells) for region_id, cells in regions.items()}
    print(f"Region sizes: {region_sizes}")
    
    fig = visualize_puzzle(grid, cell_regions, queen_positions,
                         f"Puzzle from Queen Placement (Radius: {grid_radius}, Queens: {num_queens})")
    plt.savefig("queen_puzzle.png")
    print("Puzzle saved as 'queen_puzzle.png'")
    
    fig = visualize_puzzle(grid, cell_regions, {},
                         f"Puzzle Regions (Radius: {grid_radius}, Queens: {num_queens})")
    plt.savefig("puzzle_regions.png")
    print("Puzzle regions saved as 'puzzle_regions.png'")
    
    # Create a visualization showing only the regions
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    cmap = plt.get_cmap('tab20', num_queens)
    colors = [cmap(i) for i in range(num_queens)]
    
    for cell in grid.get_all_cells():
        pixel = hex_to_pixel(cell, hex_size)
        if cell in cell_regions:
            region_id = cell_regions[cell]
            if region_id >= 0:
                color = colors[region_id]
                draw_hexagon(ax, pixel, hex_size, color, alpha=1.0)
    
    for cell in grid.get_all_cells():
        pixel = hex_to_pixel(cell, hex_size)
        angles = np.linspace(0, 2*np.pi, 7)[:-1]
        x = pixel[0] + hex_size * np.cos(angles)
        y = pixel[1] + hex_size * np.sin(angles)
        ax.plot(x, y, color='black', linewidth=0.5)
    
    ax.set_xlim([-2*grid.radius, 2*grid.radius])
    ax.set_ylim([-2*grid.radius, 2*grid.radius])
    ax.set_title(f"Hex Regions Only (Radius: {grid_radius}, Queens: {num_queens})")
    ax.axis('off')
    plt.tight_layout()
    plt.savefig("hex_regions.png")
    print("Hex regions visualization saved as 'hex_regions.png'")
    
    print("\nSolving with only queen positions as clues using advanced solver...")
    solver = AdvancedPuzzleSolver(grid, num_queens)
    solver.initialize_from_clues(queen_positions)
    start_time = time.time()
    solved = solver.solve()
    solve_time = time.time() - start_time
    
    if solved:
        print(f"Puzzle solved in {solve_time:.2f} seconds.")
        print(f"Solver metrics: {solver.get_metrics()}")
        solution = solver.get_solution()
        fig = visualize_puzzle(grid, solution, queen_positions, "Puzzle Solution")
        plt.savefig("queen_solution.png")
        print("Solution saved as 'queen_solution.png'")
        
        print("\nChecking solution uniqueness with advanced solver...")
        new_solver = AdvancedPuzzleSolver(grid, num_queens)
        new_solver.initialize_from_clues(queen_positions)
        solution_count = new_solver.count_solutions(2)
        
        if solution_count == 1:
            print("The puzzle has a unique solution.")
        else:
            print(f"The puzzle has at least {solution_count} solutions.")
    else:
        print("Failed to solve the puzzle.")
        print(f"Solver metrics: {solver.get_metrics()}")
        print("\nTrying to solve with additional clues using advanced solver...")
        
        num_extra_clues = max(3, len(grid.get_all_cells()) // 4)
        fixed_cells = {}
        cells = list(cell_regions.items())
        random.shuffle(cells)
        
        for i in range(min(num_extra_clues, len(cells))):
            cell, region_id = cells[i]
            if cell not in queen_positions.values():
                fixed_cells[cell] = region_id
        
        print(f"Adding {len(fixed_cells)} additional clues...")
        new_solver = AdvancedPuzzleSolver(grid, num_queens)
        new_solver.initialize_from_clues(queen_positions, fixed_cells)
        start_time = time.time()
        solved_with_clues = new_solver.solve()
        solve_time = time.time() - start_time
        
        if solved_with_clues:
            print(f"Puzzle solved with additional clues in {solve_time:.2f} seconds.")
            print(f"Solver metrics: {new_solver.get_metrics()}")
            solution = new_solver.get_solution()
            fig = visualize_puzzle(grid, solution, queen_positions, "Puzzle Solution (with additional clues)")
            plt.savefig("puzzle_solution_with_clues.png")
            print("Solution saved as 'puzzle_solution_with_clues.png'")
            print("\nNote: This puzzle requires additional clues to be solved uniquely.")
    return
def demonstrate_reverse_engineering(grid_radius: int, seed: Optional[int] = None, ensure_logical: bool = True):
    """
    Demonstrate the reverse engineering process to create challenging puzzles.
    
    Args:
        grid_radius: Radius of the hexagonal grid
        seed: Random seed for reproducibility
        ensure_logical: Whether to ensure the puzzle is solvable using only logical techniques
    """
    num_pieces = calculate_recommended_queens(grid_radius)
    print(f"Demonstrating reverse engineering with grid radius {grid_radius} and {num_pieces} pieces...")
    
    # Create a grid
    grid = HexGrid(grid_radius)
    
    # Generate a complete puzzle
    generator = PuzzleGenerator(grid, num_pieces, seed)
    if not generator.generate_puzzle(ensure_unique=True, ensure_logical=True):
        print(f"Failed to generate a puzzle with radius {grid_radius} and {num_pieces} pieces.")
        return
    
    print("Puzzle generated successfully.")
    solution = generator.cell_regions
    piece_positions = generator.piece_positions
    
    # Visualize the complete solution
    fig = visualize_puzzle(grid, solution, piece_positions,
                         f"Complete Solution (Radius: {grid_radius}, Pieces: {num_pieces})")
    plt.savefig("complete_solution.png")
    print("Complete solution saved as 'complete_solution.png'")
    
    # Create a reverse engineering solver
    print("\nStarting reverse engineering process...")
    re_solver = ReverseEngineeringSolver(grid, num_pieces, seed)
    re_solver.initialize_from_solution(solution, piece_positions)
    
    # Find minimal clues
    start_time = time.time()
    print("Finding minimal clues using basic approach...")
    minimal_clues = re_solver.find_minimal_clues(ensure_logical=ensure_logical)
    basic_time = time.time() - start_time
    
    print(f"Basic approach completed in {basic_time:.2f} seconds.")
    print(f"Initial clues: {re_solver.metrics['initial_clues']}")
    print(f"Final clues: {re_solver.metrics['final_clues']}")
    print(f"Removed clues: {re_solver.metrics['removed_clues']}")
    
    # Visualize the puzzle with minimal clues
    minimal_solution = {cell: region_id for cell, region_id in solution.items()
                      if cell in piece_positions.values() or cell in minimal_clues}
    fig = visualize_puzzle(grid, minimal_solution, piece_positions,
                         f"Minimal Clues (Basic) - {len(minimal_clues)} clues")
    plt.savefig("minimal_clues_basic.png")
    print("Minimal clues (basic) saved as 'minimal_clues_basic.png'")
    
    # Find minimal clues by importance
    print("\nFinding minimal clues using importance-based approach...")
    re_solver.initialize_from_solution(solution, piece_positions)  # Reset the solver
    start_time = time.time()
    minimal_clues_importance = re_solver.find_minimal_clues_by_importance(ensure_logical=ensure_logical)
    importance_time = time.time() - start_time
    
    print(f"Importance-based approach completed in {importance_time:.2f} seconds.")
    print(f"Initial clues: {re_solver.metrics['initial_clues']}")
    print(f"Final clues: {re_solver.metrics['final_clues']}")
    print(f"Removed clues: {re_solver.metrics['removed_clues']}")
    
    # Visualize the puzzle with minimal clues by importance
    minimal_solution_importance = {cell: region_id for cell, region_id in solution.items()
                                if cell in piece_positions.values() or cell in minimal_clues_importance}
    fig = visualize_puzzle(grid, minimal_solution_importance, piece_positions,
                         f"Minimal Clues (Importance) - {len(minimal_clues_importance)} clues")
    plt.savefig("minimal_clues_importance.png")
    print("Minimal clues (importance) saved as 'minimal_clues_importance.png'")
    
    # Verify that the puzzle is uniquely solvable
    print("\nVerifying that the puzzle is uniquely solvable...")
    solver = AdvancedPuzzleSolver(grid, num_pieces)
    solver.initialize_from_clues(piece_positions, minimal_clues_importance)
    start_time = time.time()
    solved = solver.solve()
    solve_time = time.time() - start_time
    
    if solved:
        print(f"Puzzle solved in {solve_time:.2f} seconds.")
        print(f"Solver metrics: {solver.get_metrics()}")
        solution = solver.get_solution()
        
        # Check if the solution matches the original
        matches_original = all(solution.get(cell) == region_id for cell, region_id in generator.cell_regions.items())
        print(f"Solution matches original: {matches_original}")
        
        # Visualize the solution
        fig = visualize_puzzle(grid, solution, piece_positions, "Puzzle Solution")
        plt.savefig("reverse_engineered_solution.png")
        print("Solution saved as 'reverse_engineered_solution.png'")
    else:
        print("Failed to solve the puzzle.")
        print(f"Solver metrics: {solver.get_metrics()}")
    
    return

def main():
    """Main function to parse arguments and run the program."""
    parser = argparse.ArgumentParser(description="Hexagonal Puzzle Generator and Solver")
    parser.add_argument("--radius", type=int, default=3, help="Radius of the hexagonal grid")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--attempts", type=int, default=3, help="Maximum attempts to generate a solvable puzzle")
    parser.add_argument("--visualize-only", action="store_true", help="Only visualize the puzzle, don't solve it")
    parser.add_argument("--output", type=str, default=".", help="Output directory for saved images")
    parser.add_argument("--ensure-unique", action="store_true", default=True, help="Ensure the puzzle has a unique solution")
    parser.add_argument("--ensure-logical", action="store_true", default=True, help="Ensure the puzzle is solvable using only logical techniques")
    parser.add_argument("--reverse-engineer", action="store_true", help="Use reverse engineering to create challenging puzzles")
    args = parser.parse_args()
    
    args.pieces = calculate_recommended_queens(args.radius)
    print(f"Using calculated number of pieces: {args.pieces}")
    
    if args.output != "." and not os.path.exists(args.output):
        os.makedirs(args.output)
    
    if args.reverse_engineer:
        demonstrate_reverse_engineering(args.radius, args.seed, args.ensure_logical)
    else:
        # Default behavior: demonstrate queen placement
        demonstrate_queen_placement(args.radius, args.seed)
    demonstrate_queen_placement(args.radius, args.seed)

if __name__ == "__main__":
    main()