"""
Main module for the hexagonal puzzle generator with visualization.
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
from .growth_region_generator import GrowthRegionGenerator
from .interfaces import PuzzleSpecification
from .puzzle_visualizer import (
    hex_to_pixel, draw_hexagon, draw_queen, get_region_color,
    calculate_recommended_queens, draw_hex_grid
)
from .puzzle_generator import generate_puzzle_with_queens
from .hex_queen_puzzle import HexQueenPuzzle
from .rule_validator import RuleValidator

def demonstrate_queen_placement(grid_radius: int, seed: Optional[int] = None):
    """
    Demonstrate the placement of queens on a hexagonal grid, and generate a puzzle
    based on the queen positions using the new architecture.
    
    Args:
        grid_radius: Radius of the hexagonal grid
        seed: Random seed for reproducibility
    """
    num_regions = calculate_recommended_queens(grid_radius)
    print(f"Demonstrating queen placement with grid radius {grid_radius} and {num_regions} queens...")
    
    # Create grid
    grid = HexGrid(grid_radius)
    
    # Create region generator and puzzle generator
    region_generator = GrowthRegionGenerator(seed)
    generator = PuzzleGenerator(region_generator)
    
    # Place queens using QueenPlacer
    from .queen_placer import QueenPlacer
    
    placer = QueenPlacer(grid, num_regions, seed)
    if not placer.place_queens():
        print(f"Failed to place {num_regions} queens on a grid of radius {grid_radius}.")
        return
    
    queen_positions = placer.get_queen_positions()
    print(f"Queens placed successfully using QueenPlacer.")
    
    # Create a puzzle with just the queens (no regions yet)
    # Use a temporary cell_regions mapping for visualization
    temp_cell_regions = {}
    for cell in grid.get_all_cells():
        parity = (cell.x + cell.y + cell.z) % 2
        temp_cell_regions[cell] = -1 - parity
    
    queens_only_puzzle = HexQueenPuzzle(grid, queen_positions, temp_cell_regions)
    fig = queens_only_puzzle.visualize_puzzle(title=f"Queen Placement (Radius: {grid_radius}, Queens: {num_regions})")
    plt.savefig("queen_placement.png")
    print("Queen placement saved as 'queen_placement.png'")
    
    # Generate regions using the region generator
    print("\nGenerating puzzle based on queen positions...")
    cell_regions = region_generator.generate_regions(grid, queen_positions)
    
    if not cell_regions:
        print("Failed to grow regions from queen positions.")
        return
    print("Regions grown successfully.")
    
    # Check region contiguity
    is_contiguous = RuleValidator.check_region_contiguity(grid, cell_regions)
    if is_contiguous:
        print("All regions are contiguous.")
    else:
        print("Warning: Some regions are not contiguous.")
        return
    
    # Get region sizes
    region_sizes = region_generator.get_region_sizes()
    print(f"Region sizes: {region_sizes}")
    
    # Create the final puzzle
    puzzle = HexQueenPuzzle(grid, queen_positions, cell_regions)
    
    # Visualize the puzzle with queens
    fig = puzzle.visualize_puzzle(title=f"Puzzle from Queen Placement (Radius: {grid_radius}, Queens: {num_regions})")
    plt.savefig("queen_puzzle.png")
    print("Puzzle saved as 'queen_puzzle.png'")
    
    # Create a puzzle without pieces for visualization
    no_pieces_puzzle = HexQueenPuzzle(grid, {}, cell_regions)
    fig = no_pieces_puzzle.visualize_puzzle(show_pieces=False, title=f"Puzzle Regions (Radius: {grid_radius}, Queens: {num_regions})")
    plt.savefig("puzzle_regions.png")
    print("Puzzle regions saved as 'puzzle_regions.png'")

    # Serialize and save the puzzle to a JSON file
    puzzle_json = puzzle.to_json()
    output_path = os.path.join(".", "puzzle.json")
    with open(output_path, "w") as f:
        f.write(puzzle_json)
    print(f"Puzzle saved as 'puzzle.json'")
    
    return

def demonstrate_reverse_engineering(grid_radius: int, seed: Optional[int] = None, max_difficulty: int = 3):
    """
    Demonstrate the puzzle generation process using the new architecture.
    
    Args:
        grid_radius: Radius of the hexagonal grid
        seed: Random seed for reproducibility
    """
    num_regions = calculate_recommended_queens(grid_radius)
    print(f"Demonstrating puzzle generation with grid radius {grid_radius} and {num_regions} regions...")
    
    # Create a grid
    grid = HexGrid(grid_radius)
    
    # Create region generator and puzzle generator
    region_generator = GrowthRegionGenerator(seed)
    generator = PuzzleGenerator(region_generator)
    
    # Create puzzle specification
    spec = PuzzleSpecification(
        grid=grid,
        num_regions=num_regions,
        seed=seed,
        max_difficulty=max_difficulty,
    )
    
    # Generate a complete puzzle
    hex_queen_puzzle = generator.generate_puzzle(spec)
    if not hex_queen_puzzle:
        print(f"Failed to generate a puzzle with radius {grid_radius} and {num_regions} regions.")
        return
    
    print(f"Puzzle generated: unique solution, solvable by logic (difficulty {hex_queen_puzzle.difficulty}/4).")
    solution = hex_queen_puzzle.cell_regions
    queen_positions = hex_queen_puzzle.queen_positions
    
    # Visualize the complete solution
    fig = hex_queen_puzzle.visualize_puzzle(title=f"Complete Solution (Radius: {grid_radius}, Regions: {num_regions})")
    plt.savefig("complete_solution.png")
    print("Complete solution saved as 'complete_solution.png'")
    
    # Create a puzzle without pieces for visualization
    no_pieces_puzzle = HexQueenPuzzle(grid, {}, solution)
    fig = no_pieces_puzzle.visualize_puzzle(show_pieces=False, title=f"Puzzle Regions (Radius: {grid_radius}, Regions: {num_regions})")
    plt.savefig("puzzle_regions.png")
    print("Puzzle regions saved as 'puzzle_regions.png'")
    
    # Validate the puzzle
    print("\nValidating puzzle...")
    is_valid = hex_queen_puzzle.validate()
    print(f"Puzzle is valid: {is_valid}")
    
    # Check region contiguity
    print("Checking region contiguity...")
    is_contiguous = RuleValidator.check_region_contiguity(grid, solution)
    print(f"All regions are contiguous: {is_contiguous}")
    
    # Check queen visibility
    print("Checking queen visibility...")
    queens_not_visible = RuleValidator.check_queen_visibility(grid, queen_positions)
    print(f"Queens cannot see each other: {queens_not_visible}")
    
    # Serialize and save the puzzle to a JSON file
    puzzle_json = hex_queen_puzzle.to_json()
    output_path = os.path.join(".", "puzzle.json")
    with open(output_path, "w") as f:
        f.write(puzzle_json)
    print(f"Puzzle saved as 'puzzle.json'")

    return

def main():
    """Main function to parse arguments and run the program."""
    parser = argparse.ArgumentParser(description="Hexagonal Puzzle Generator")
    parser.add_argument("--radius", type=int, default=3, help="Radius of the hexagonal grid")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default=".", help="Output directory for saved images")
    parser.add_argument("--max-difficulty", type=int, default=3, choices=[1, 2, 3, 4],
                        help="Hardest deduction a solver may need (1=easy .. 4=hard)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed generator logging")
    parser.add_argument("--generate-puzzle", action="store_true", help="Generate a complete puzzle using the region generator")
    args = parser.parse_args()
    import logging
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format="%(name)s: %(message)s")
    
    args.regions = calculate_recommended_queens(args.radius)
    print(f"Using calculated number of regions: {args.regions}")
    
    if args.output != "." and not os.path.exists(args.output):
        os.makedirs(args.output)
    
    if args.generate_puzzle:
        demonstrate_reverse_engineering(args.radius, args.seed, args.max_difficulty)
    else:
        # Default behavior: demonstrate queen placement
        demonstrate_queen_placement(args.radius, args.seed)

if __name__ == "__main__":
    main()