"""
Main module for the hexagonal puzzle solver with visualization.
"""
import argparse
import random
import time
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
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
    
    # Define colors for regions (using a colormap)
    num_regions = max(len(piece_positions), 1)  # Ensure at least 1 region for colormap
    cmap = plt.cm.get_cmap('tab20', num_regions)
    colors = [cmap(i) for i in range(num_regions)]
    
    # Draw all cells with their region colors
    hex_size = 0.5
    for cell in grid.get_all_cells():
        pixel = cube_to_pixel(cell, hex_size)
        
        if cell in cell_regions:
            region_id = cell_regions[cell]
            if region_id < 0:
                # Special values for unassigned cells
                if region_id == -1:
                    draw_hexagon(ax, pixel, hex_size, 'lightgray', alpha=0.5)
                elif region_id == -2:
                    draw_hexagon(ax, pixel, hex_size, 'whitesmoke', alpha=0.5)
                else:
                    draw_hexagon(ax, pixel, hex_size, 'white', alpha=0.3)
            else:
                # Make sure region_id is within the range of colors
                color_idx = region_id % len(colors)
                color = colors[color_idx]
                draw_hexagon(ax, pixel, hex_size, color)
        else:
            # Unassigned cell
            draw_hexagon(ax, pixel, hex_size, 'white')
    
    # Draw pieces (with a different marker)
    for piece_id, pos in piece_positions.items():
        pixel = cube_to_pixel(pos, hex_size)
        ax.plot(pixel[0], pixel[1], 'o', markersize=10, color='black')
        ax.text(pixel[0], pixel[1], str(piece_id), ha='center', va='center', 
               color='white', fontweight='bold')
    
    # Set limits and title
    ax.set_xlim([-2*grid.radius, 2*grid.radius])
    ax.set_ylim([-2*grid.radius, 2*grid.radius])
    ax.set_title(title)
    ax.axis('off')
    
    plt.tight_layout()
    return fig

def generate_and_solve_puzzle(grid_radius: int, num_pieces: int, seed: Optional[int] = None, max_attempts: int = 3, ensure_unique: bool = True, ensure_logical: bool = True):
    """
    Generate and solve a hexagonal puzzle.
    
    Args:
        grid_radius: Radius of the hexagonal grid
        num_pieces: Number of pieces/regions
        seed: Random seed for reproducibility
        max_attempts: Maximum number of attempts to generate a solvable puzzle
    """
    print(f"Generating puzzle with grid radius {grid_radius} and {num_pieces} pieces...")
    
    # Create grid
    grid = HexGrid(grid_radius)
    
    # Try multiple times to generate a solvable puzzle
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print(f"\nAttempt {attempt}/{max_attempts} to generate a solvable puzzle...")
            # Use a different seed for each attempt
            if seed is not None:
                current_seed = seed + attempt - 1
            else:
                current_seed = random.randint(1, 10000)
        else:
            current_seed = seed
        
        # Generate puzzle
        generator = PuzzleGenerator(grid, num_pieces, current_seed)
        start_time = time.time()
        success = generator.generate_puzzle(ensure_unique=ensure_unique, ensure_logical=ensure_logical)
        generation_time = time.time() - start_time
        
        if not success:
            print(f"Failed to generate puzzle after {generator.retry_count} attempts.")
            continue
        
        print(f"Puzzle generated successfully in {generation_time:.2f} seconds "
              f"({generator.retry_count} retries).")
        
        # Get puzzle state
        puzzle_state = generator.get_puzzle_state()
        region_sizes = generator.get_region_sizes()
        print(f"Region sizes: {region_sizes}")
        print(f"Puzzle has a unique solution: {puzzle_state.get('is_unique', 'Unknown')}")
        print(f"Puzzle is logically solvable: {puzzle_state.get('is_logically_solvable', 'Unknown')}")
        
        # Check if region sizes are too unbalanced
        max_size = max(region_sizes.values())
        min_size = min(region_sizes.values())
        total_cells = len(grid.get_all_cells())
        expected_size = total_cells / num_pieces
        
        if max_size > expected_size * 2 or min_size < expected_size * 0.5:
            print(f"Warning: Region sizes are unbalanced (min: {min_size}, max: {max_size}, expected: {expected_size:.1f})")
        
        # Convert HexCoord objects to tuples for visualization
        cell_regions = {cell: region_id for cell, region_id in generator.cell_regions.items()}
        
        # Visualize generated puzzle
        fig = visualize_puzzle(grid, cell_regions, generator.piece_positions,
                             f"Generated Puzzle (Seed: {current_seed})")
        plt.savefig("generated_puzzle.png")
        print("Generated puzzle saved as 'generated_puzzle.png'")
        
        # Create a visualization of just the hex regions without pieces
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_aspect('equal')
        
        # Define colors for regions (using a colormap)
        cmap = plt.cm.get_cmap('tab20', num_pieces)
        colors = [cmap(i) for i in range(num_pieces)]
        
        # Draw all cells with their region colors
        hex_size = 0.5
        for cell in grid.get_all_cells():
            pixel = cube_to_pixel(cell, hex_size)
            
            if cell in cell_regions:
                region_id = cell_regions[cell]
                # Make sure region_id is within the range of colors
                if region_id >= 0:  # Skip negative region IDs
                    color_idx = region_id % len(colors)
                    color = colors[color_idx]
                    draw_hexagon(ax, pixel, hex_size, color, alpha=1.0)
        
        # Add thin borders to all cells for better visibility
        for cell in grid.get_all_cells():
            pixel = cube_to_pixel(cell, hex_size)
            angles = np.linspace(0, 2*np.pi, 7)[:-1]
            x = pixel[0] + hex_size * np.cos(angles)
            y = pixel[1] + hex_size * np.sin(angles)
            ax.plot(x, y, color='black', linewidth=0.5)
        
        # Set limits and title
        ax.set_xlim([-2*grid.radius, 2*grid.radius])
        ax.set_ylim([-2*grid.radius, 2*grid.radius])
        ax.set_title(f"Hex Regions Only (Seed: {current_seed})")
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig("hex_regions.png")
        print("Hex regions visualization saved as 'hex_regions.png'")
        
        # Solve the puzzle
        print("\nSolving the puzzle...")
        
        # First, let's verify that the solver works with the complete solution
        print("Testing solver with complete solution...")
        solver_complete = PuzzleSolver(grid, num_pieces)
        solver_complete.initialize_from_generator(generator)
        
        # Verify that the complete solution is valid
        if not solver_complete.is_solved():
            print("Error: Complete solution is not valid!")
            continue
            
        # Now try to solve with just the piece positions
        print("\nSolving with only piece positions as clues...")
        solver = PuzzleSolver(grid, num_pieces)
        piece_positions = generator.piece_positions.copy()
        solver.initialize_from_clues(piece_positions)
        
        # Solve
        start_time = time.time()
        solved = solver.solve()
        solve_time = time.time() - start_time
        
        if solved:
            print(f"Puzzle solved in {solve_time:.2f} seconds.")
            print(f"Solver metrics: {solver.get_metrics()}")
            
            # Visualize solution
            solution = solver.get_solution()
            fig = visualize_puzzle(grid, solution, piece_positions, "Puzzle Solution")
            plt.savefig("puzzle_solution.png")
            print("Solution saved as 'puzzle_solution.png'")
            
            # Check uniqueness
            print("\nChecking solution uniqueness...")
            new_solver = PuzzleSolver(grid, num_pieces)
            new_solver.initialize_from_clues(piece_positions)
            solution_count = new_solver.count_solutions(2)
            
            if solution_count == 1:
                print("The puzzle has a unique solution.")
            else:
                print(f"The puzzle has at least {solution_count} solutions.")
            
            # Successfully generated and solved a puzzle
            return True
        else:
            print("Failed to solve the puzzle.")
            print(f"Solver metrics: {solver.get_metrics()}")
            
            # Try with more information (provide some fixed cells)
            print("\nTrying to solve with additional clues...")
            
            # Add some fixed cells as clues (25% of the total)
            num_extra_clues = max(3, len(grid.get_all_cells()) // 4)
            fixed_cells = {}
            cells = list(generator.cell_regions.items())
            random.shuffle(cells)
            
            for i in range(min(num_extra_clues, len(cells))):
                cell, region_id = cells[i]
                if cell not in piece_positions.values():  # Don't duplicate piece positions
                    fixed_cells[cell] = region_id
            
            print(f"Adding {len(fixed_cells)} additional clues...")
            
            # Try solving again with extra clues
            new_solver = PuzzleSolver(grid, num_pieces)
            new_solver.initialize_from_clues(piece_positions, fixed_cells)
            
            start_time = time.time()
            solved_with_clues = new_solver.solve()
            solve_time = time.time() - start_time
            
            if solved_with_clues:
                print(f"Puzzle solved with additional clues in {solve_time:.2f} seconds.")
                print(f"Solver metrics: {new_solver.get_metrics()}")
                
                # Visualize solution with clues
                solution = new_solver.get_solution()
                fig = visualize_puzzle(grid, solution, piece_positions, "Puzzle Solution (with additional clues)")
                plt.savefig("puzzle_solution_with_clues.png")
                print("Solution saved as 'puzzle_solution_with_clues.png'")
                
                print("\nNote: This puzzle requires additional clues to be solved uniquely.")
                return True
    
    print(f"\nFailed to generate a solvable puzzle after {max_attempts} attempts.")
    print("Try adjusting parameters (grid radius, number of pieces) or use a different seed.")
    return False

def demonstrate_queen_placement(grid_radius: int, num_queens: int, seed: Optional[int] = None):
    """
    Demonstrate the placement of queens on a hexagonal grid.
    
    Args:
        grid_radius: Radius of the hexagonal grid
        num_queens: Number of queens to place
        seed: Random seed for reproducibility
    """
    print(f"Demonstrating queen placement with grid radius {grid_radius} and {num_queens} queens...")
    
    # Create grid
    grid = HexGrid(grid_radius)
    
    # Create queen placer
    placer = QueenPlacer(grid, num_queens, seed)
    
    # Place queens
    start_time = time.time()
    success = placer.place_queens()
    placement_time = time.time() - start_time
    
    if not success:
        print(f"Failed to place {num_queens} queens on a grid of radius {grid_radius}.")
        return
    
    print(f"Queens placed successfully in {placement_time:.2f} seconds.")
    
    # Get queen positions
    queen_positions = placer.get_queen_positions()
    
    # Create a mapping for visualization with a checkerboard pattern
    cell_regions = {}
    
    # Draw all cells with a light gray background to show the grid better
    for cell in grid.get_all_cells():
        # Use alternating colors for better visibility
        parity = (cell.x + cell.y + cell.z) % 2
        cell_regions[cell] = -1 - parity  # -1 or -2 to indicate unassigned with different colors
    
    # Visualize the queens
    fig = visualize_puzzle(grid, cell_regions, queen_positions,
                         f"Queen Placement (Radius: {grid_radius}, Queens: {num_queens})")
    plt.savefig("queen_placement.png")
    print("Queen placement saved as 'queen_placement.png'")
    
    # Now generate a puzzle based on these queen positions
    print("\nGenerating puzzle based on queen positions...")
    
    # Create a new function to grow regions from queen positions
    def grow_regions_from_queens(grid, queen_positions, rng):
        from collections import defaultdict, deque
        """
        Grow regions from queen positions using a randomized approach.
        
        Args:
            grid: The hexagonal grid
            queen_positions: Mapping of queen IDs to their positions
            rng: Random number generator
            
        Returns:
            Tuple of (success, cell_regions, regions)
        """
        # Initialize regions with queen positions
        regions = defaultdict(set)
        cell_regions = {}
        
        # Initialize each region with its queen
        for queen_id, pos in queen_positions.items():
            regions[queen_id].add(pos)
            cell_regions[pos] = queen_id
        
        # Initialize set of unassigned cells
        unassigned_cells = set(grid.get_all_cells()) - set(queen_positions.values())
        
        # Initialize bordering cells for each region
        bordering_cells = defaultdict(set)
        for queen_id, pos in queen_positions.items():
            for neighbor in grid.get_neighbors(pos):
                if neighbor in unassigned_cells:
                    bordering_cells[queen_id].add(neighbor)
        
        # Grow regions until all cells are assigned
        while unassigned_cells:
            # Get regions that still have bordering cells
            active_regions = [r for r, cells in bordering_cells.items() if cells]
            
            if not active_regions:
                print("No more active regions with bordering cells.")
                return False, cell_regions, regions
            
            # Choose a random region
            region_id = rng.choice(active_regions)
            
            # Choose a random bordering cell for this region
            if not bordering_cells[region_id]:
                continue
                
            cell = rng.choice(list(bordering_cells[region_id]))
            
            # Add the cell to the region
            regions[region_id].add(cell)
            cell_regions[cell] = region_id
            unassigned_cells.remove(cell)
            
            # Remove this cell from all bordering sets
            for r in bordering_cells:
                if cell in bordering_cells[r]:
                    bordering_cells[r].remove(cell)
            
            # Add new bordering cells
            for neighbor in grid.get_neighbors(cell):
                if neighbor in unassigned_cells:
                    bordering_cells[region_id].add(neighbor)
        
        return True, cell_regions, regions
    
    # Grow regions using the new function
    rng = random.Random(seed)
    success, cell_regions, regions = grow_regions_from_queens(grid, queen_positions, rng)
    
    if not success:
        print("Failed to grow regions from queen positions.")
        return
    
    print("Regions grown successfully.")
    
    # Check if all regions are contiguous
    from collections import deque
    def is_region_contiguous(grid, region_cells):
        """Check if a region is contiguous."""
        if not region_cells:
            return True
        
        # Use BFS to check if all cells are connected
        start = next(iter(region_cells))
        visited = {start}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            for neighbor in grid.get_neighbors(current):
                if neighbor in region_cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # If all cells are visited, the region is contiguous
        return len(visited) == len(region_cells)
    
    # Check if all regions are contiguous
    all_contiguous = True
    for region_id, region_cells in regions.items():
        if not is_region_contiguous(grid, region_cells):
            print(f"Warning: Region {region_id} is not contiguous.")
            all_contiguous = False
    
    if all_contiguous:
        print("All regions are contiguous.")
    
    # Get region sizes
    region_sizes = {region_id: len(cells) for region_id, cells in regions.items()}
    print(f"Region sizes: {region_sizes}")
    
    # Visualize the puzzle with queens
    fig = visualize_puzzle(grid, cell_regions, queen_positions,
                         f"Puzzle from Queen Placement (Radius: {grid_radius}, Queens: {num_queens})")
    plt.savefig("queen_puzzle.png")
    print("Puzzle saved as 'queen_puzzle.png'")
    
    # Visualize the puzzle without queens (just regions)
    fig = visualize_puzzle(grid, cell_regions, {},
                         f"Puzzle Regions (Radius: {grid_radius}, Queens: {num_queens})")
    plt.savefig("puzzle_regions.png")
    print("Puzzle regions saved as 'puzzle_regions.png'")
    
    # Create a cleaner visualization of just the regions with distinct colors
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    
    # Define colors for regions (using a colormap)
    cmap = plt.cm.get_cmap('tab20', num_queens)
    colors = [cmap(i) for i in range(num_queens)]
    
    # Draw all cells with their region colors
    hex_size = 0.5
    for cell in grid.get_all_cells():
        pixel = cube_to_pixel(cell, hex_size)
        
        if cell in cell_regions:
            region_id = cell_regions[cell]
            if region_id >= 0:  # Only draw cells assigned to regions
                color = colors[region_id]
                draw_hexagon(ax, pixel, hex_size, color, alpha=1.0)
    
    # Add thin borders to all cells for better visibility
    for cell in grid.get_all_cells():
        pixel = cube_to_pixel(cell, hex_size)
        angles = np.linspace(0, 2*np.pi, 7)[:-1]
        x = pixel[0] + hex_size * np.cos(angles)
        y = pixel[1] + hex_size * np.sin(angles)
        ax.plot(x, y, color='black', linewidth=0.5)
    
    # Set limits and title
    ax.set_xlim([-2*grid.radius, 2*grid.radius])
    ax.set_ylim([-2*grid.radius, 2*grid.radius])
    ax.set_title(f"Hex Regions Only (Radius: {grid_radius}, Queens: {num_queens})")
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig("hex_regions.png")
    print("Hex regions visualization saved as 'hex_regions.png'")
    
    # Solve the puzzle
    print("\nSolving the puzzle...")
    
    # First, let's verify that the solver works with the complete solution
    print("Testing solver with complete solution...")
    solver_complete = PuzzleSolver(grid, num_queens)
    
    # Initialize with the complete solution
    solver_complete.assigned_cells = cell_regions.copy()
    for cell, region_id in cell_regions.items():
        solver_complete.region_cells[region_id].add(cell)
    
    # Verify that the complete solution is valid
    if not solver_complete.is_solved():
        print("Error: Complete solution is not valid!")
        return
    
    print("Complete solution is valid.")
    
    # Now try to solve with just the queen positions
    print("\nSolving with only queen positions as clues...")
    solver = PuzzleSolver(grid, num_queens)
    solver.initialize_from_clues(queen_positions)
    
    # Solve
    start_time = time.time()
    solved = solver.solve()
    solve_time = time.time() - start_time
    
    if solved:
        print(f"Puzzle solved in {solve_time:.2f} seconds.")
        print(f"Solver metrics: {solver.get_metrics()}")
        
        # Visualize solution
        solution = solver.get_solution()
        fig = visualize_puzzle(grid, solution, queen_positions, "Puzzle Solution")
        plt.savefig("queen_solution.png")
        print("Solution saved as 'queen_solution.png'")
        
        # Check uniqueness
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
        
        # Try with more information (provide some fixed cells)
        print("\nTrying to solve with additional clues...")
        
        # Add some fixed cells as clues (25% of the total)
        num_extra_clues = max(3, len(grid.get_all_cells()) // 4)
        fixed_cells = {}
        cells = list(cell_regions.items())
        random.shuffle(cells)
        
        for i in range(min(num_extra_clues, len(cells))):
            cell, region_id = cells[i]
            if cell not in queen_positions.values():  # Don't duplicate queen positions
                fixed_cells[cell] = region_id
        
        print(f"Adding {len(fixed_cells)} additional clues...")
        
        # Try solving again with extra clues
        new_solver = PuzzleSolver(grid, num_queens)
        new_solver.initialize_from_clues(queen_positions, fixed_cells)
        
        start_time = time.time()
        solved_with_clues = new_solver.solve()
        solve_time = time.time() - start_time
        
        if solved_with_clues:
            print(f"Puzzle solved with additional clues in {solve_time:.2f} seconds.")
            print(f"Solver metrics: {new_solver.get_metrics()}")
            
            # Visualize solution with clues
            solution = new_solver.get_solution()
            fig = visualize_puzzle(grid, solution, queen_positions, "Puzzle Solution (with additional clues)")
            plt.savefig("puzzle_solution_with_clues.png")
            print("Solution saved as 'puzzle_solution_with_clues.png'")
            
            print("\nNote: This puzzle requires additional clues to be solved uniquely.")

def calculate_recommended_pieces(radius: int) -> int:
    """
    Calculate the number of queens for a hexagonal grid of given radius.
    
    For a hex grid of radius r:
    - r=0 means 1 central hex
    - r=1 means 7 hexes (1 central + 6 around it)
    - r=2 means 19 hexes (7 from r=1 + 12 in the outer ring)
    
    The formula for the total number of cells is 3r(r+1)+1
    
    For queens placement, the formula is r*2+1, which gives:
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
    # For radius 0, there's only one cell, so only one queen
    if radius == 0:
        return 1
    # For all other radii, use the formula r*2+1
    else:
        return radius * 2 + 1

def main():
    """Main function to parse arguments and run the program."""
    parser = argparse.ArgumentParser(description="Hexagonal Puzzle Generator and Solver")
    parser.add_argument("--radius", type=int, default=3, help="Radius of the hexagonal grid")
    parser.add_argument("--pieces", type=int, default=None, help="Number of pieces/regions (default: calculated based on radius)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--attempts", type=int, default=3, help="Maximum attempts to generate a solvable puzzle")
    parser.add_argument("--visualize-only", action="store_true", help="Only visualize the puzzle, don't solve it")
    parser.add_argument("--output", type=str, default=".", help="Output directory for saved images")
    parser.add_argument("--queens", action="store_true", help="Demonstrate queen placement and generate puzzle from it")
    parser.add_argument("--ensure-unique", action="store_true", default=False, help="Ensure the puzzle has a unique solution")
    parser.add_argument("--ensure-logical", action="store_true", default=True, help="Ensure the puzzle is solvable using only logical techniques")
    args = parser.parse_args()
    
    # Calculate number of pieces if not specified
    if args.pieces is None:
        args.pieces = calculate_recommended_pieces(args.radius)
        print(f"Using calculated number of pieces: {args.pieces}")
    
    # Create output directory if it doesn't exist
    import os
    if args.output != "." and not os.path.exists(args.output):
        os.makedirs(args.output)
    
    if args.queens:
        # Demonstrate queen placement
        demonstrate_queen_placement(args.radius, args.pieces, args.seed)
    elif args.visualize_only:
        # Just generate and visualize the puzzle
        grid = HexGrid(args.radius)
        generator = PuzzleGenerator(grid, args.pieces, args.seed)
        if generator.generate_puzzle(ensure_unique=args.ensure_unique, ensure_logical=args.ensure_logical):
            cell_regions = {cell: region_id for cell, region_id in generator.cell_regions.items()}
            fig = visualize_puzzle(grid, cell_regions, generator.piece_positions,
                                 f"Generated Puzzle (Seed: {args.seed})")
            plt.savefig(os.path.join(args.output, "generated_puzzle.png"))
            print(f"Generated puzzle saved as '{os.path.join(args.output, 'generated_puzzle.png')}'")
        else:
            print(f"Failed to generate puzzle after {generator.retry_count} attempts.")
    else:
        # Generate and solve the puzzle
        generate_and_solve_puzzle(args.radius, args.pieces, args.seed, args.attempts, args.ensure_unique, args.ensure_logical)

if __name__ == "__main__":
    main()