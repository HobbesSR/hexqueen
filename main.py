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
import matplotlib.patches as patches
from typing import Dict, List, Set, Tuple, Optional

from hex_grid import HexGrid, HexCoord
from puzzle_generator import PuzzleGenerator
from solver import PuzzleSolver
from queen_placer import QueenPlacer

def cube_to_pixel(coord: HexCoord, size: float = 1.0) -> Tuple[float, float]:
    """
    Convert cube coordinates to pixel coordinates for drawing.
    
    Args:
        coord: The hex coordinate
        size: The size of the hexagon
        
    Returns:
        Tuple of (x, y) pixel coordinates
    """
    x = size * (3/2 * coord.x)
    y = size * (np.sqrt(3)/2 * coord.x + np.sqrt(3) * coord.z)
    return (x, y)

def draw_hexagon(ax, center, size, color, alpha=1.0, edgecolor='black'):
    """
    Draw a hexagon on the given axes.
    
    Args:
        ax: Matplotlib axes
        center: Center coordinates (x, y)
        size: Size of the hexagon
        color: Fill color
        alpha: Transparency (0-1)
        edgecolor: Edge color
    """
    angles = np.linspace(0, 2*np.pi, 7)[:-1]
    x = center[0] + size * np.cos(angles)
    y = center[1] + size * np.sin(angles)
    
    hex_patch = patches.Polygon(np.column_stack([x, y]), closed=True, 
                               fill=True, color=color, alpha=alpha, 
                               edgecolor=edgecolor, linewidth=1)
    ax.add_patch(hex_patch)

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
    ax.set_aspect('equal')
    
    num_regions = max(len(piece_positions), 1)
    cmap = plt.get_cmap('tab20', num_regions)
    colors = [cmap(i) for i in range(num_regions)]
    
    hex_size = 0.5
    for cell in grid.get_all_cells():
        pixel = cube_to_pixel(cell, hex_size)
        
        if cell in cell_regions:
            region_id = cell_regions[cell]
            if region_id < 0:
                if region_id == -1:
                    draw_hexagon(ax, pixel, hex_size, 'lightgray', alpha=0.5)
                elif region_id == -2:
                    draw_hexagon(ax, pixel, hex_size, 'whitesmoke', alpha=0.5)
                else:
                    draw_hexagon(ax, pixel, hex_size, 'white', alpha=0.3)
            else:
                color_idx = region_id % len(colors)
                color = colors[color_idx]
                draw_hexagon(ax, pixel, hex_size, color)
        else:
            draw_hexagon(ax, pixel, hex_size, 'white')
    
    for piece_id, pos in piece_positions.items():
        pixel = cube_to_pixel(pos, hex_size)
        ax.plot(pixel[0], pixel[1], 'o', markersize=10, color='black')
        ax.text(pixel[0], pixel[1], str(piece_id), ha='center', va='center', 
               color='white', fontweight='bold')
    
    ax.set_xlim([-2*grid.radius, 2*grid.radius])
    ax.set_ylim([-2*grid.radius, 2*grid.radius])
    ax.set_title(title)
    ax.axis('off')
    
    plt.tight_layout()
    return fig

def calculate_recommended_pieces(radius: int) -> int:
    """
    Calculate the number of queens for a hexagonal grid of given radius.
    
    For a hex grid of radius r:
    - r=0 means 1 central hex
    - r=1 means 7 hexes (1 central + 6 around it)
    - r=2 means 19 hexes (7 from r=1 + 12 in the outer ring)
    
    The formula for the total number of cells is 3r(r+1)+1.
    For queen placement, the formula is r*2+1:
    - r=0: 1 queen
    - r=1: 3 queens
    - r=2: 5 queens
    - r=3: 7 queens
    - r=4: 9 queens
    
    Args:
        radius: The radius of the hexagonal grid
        
    Returns:
        int: Recommended number of queens
    """
    if radius == 0:
        return 1
    else:
        return radius * 2 + 1

def demonstrate_queen_placement(grid_radius: int, seed: Optional[int] = None):
    """
    Demonstrate the placement of queens on a hexagonal grid, and generate a puzzle
    based on the queen positions.
    
    Args:
        grid_radius: Radius of the hexagonal grid
        seed: Random seed for reproducibility
    """
    num_queens = calculate_recommended_pieces(grid_radius)
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
    def grow_regions_from_queens(grid, queen_positions, rng):
        from collections import defaultdict, deque
        regions = defaultdict(set)
        cell_regions = {}
        
        for queen_id, pos in queen_positions.items():
            regions[queen_id].add(pos)
            cell_regions[pos] = queen_id
        
        unassigned_cells = set(grid.get_all_cells()) - set(queen_positions.values())
        bordering_cells = defaultdict(set)
        for queen_id, pos in queen_positions.items():
            for neighbor in grid.get_neighbors(pos):
                if neighbor in unassigned_cells:
                    bordering_cells[queen_id].add(neighbor)
        
        while unassigned_cells:
            active_regions = [r for r, cells in bordering_cells.items() if cells]
            if not active_regions:
                print("No more active regions with bordering cells.")
                return False, cell_regions, regions
            region_id = rng.choice(active_regions)
            if not bordering_cells[region_id]:
                continue
            cell = rng.choice(list(bordering_cells[region_id]))
            regions[region_id].add(cell)
            cell_regions[cell] = region_id
            unassigned_cells.remove(cell)
            for r in bordering_cells:
                if cell in bordering_cells[r]:
                    bordering_cells[r].remove(cell)
            for neighbor in grid.get_neighbors(cell):
                if neighbor in unassigned_cells:
                    bordering_cells[region_id].add(neighbor)
        return True, cell_regions, regions

    rng = random.Random(seed)
    success, cell_regions, regions = grow_regions_from_queens(grid, queen_positions, rng)
    if not success:
        print("Failed to grow regions from queen positions.")
        return
    print("Regions grown successfully.")
    
    from collections import deque
    def is_region_contiguous(grid, region_cells):
        if not region_cells:
            return True
        start = next(iter(region_cells))
        visited = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in grid.get_neighbors(current):
                if neighbor in region_cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return len(visited) == len(region_cells)
    
    all_contiguous = True
    for region_id, region_cells in regions.items():
        if not is_region_contiguous(grid, region_cells):
            print(f"Warning: Region {region_id} is not contiguous.")
            all_contiguous = False
    if all_contiguous:
        print("All regions are contiguous.")
    
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
    
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    cmap = plt.get_cmap('tab20', num_queens)
    colors = [cmap(i) for i in range(num_queens)]
    for cell in grid.get_all_cells():
        pixel = cube_to_pixel(cell, hex_size)
        if cell in cell_regions:
            region_id = cell_regions[cell]
            if region_id >= 0:
                color = colors[region_id]
                draw_hexagon(ax, pixel, hex_size, color, alpha=1.0)
    for cell in grid.get_all_cells():
        pixel = cube_to_pixel(cell, hex_size)
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
    
    print("\nSolving with only queen positions as clues...")
    solver = PuzzleSolver(grid, num_queens)
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
        print("\nChecking solution uniqueness...")
        new_solver = PuzzleSolver(grid, num_queens)
        new_solver.initialize_from_clues(queen_positions)
        solution_count = new_solver.count_solutions(2)
        if solution_count == 1:
            print("The puzzle has a unique solution.")
        else:
            print(f"The puzzle has at least {solution_count} solutions.")
    else:
        print("Failed to solve the puzzle.")
        print(f"Solver metrics: {solver.get_metrics()}")
        print("\nTrying to solve with additional clues...")
        num_extra_clues = max(3, len(grid.get_all_cells()) // 4)
        fixed_cells = {}
        cells = list(cell_regions.items())
        random.shuffle(cells)
        for i in range(min(num_extra_clues, len(cells))):
            cell, region_id = cells[i]
            if cell not in queen_positions.values():
                fixed_cells[cell] = region_id
        print(f"Adding {len(fixed_cells)} additional clues...")
        new_solver = PuzzleSolver(grid, num_queens)
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
    args = parser.parse_args()
    
    args.pieces = calculate_recommended_pieces(args.radius)
    print(f"Using calculated number of pieces: {args.pieces}")
    
    if args.output != "." and not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Since queen placement is the default behavior, directly demonstrate it.
    demonstrate_queen_placement(args.radius, args.seed)

if __name__ == "__main__":
    main()