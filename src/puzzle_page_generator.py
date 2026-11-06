"""
Generates pages with hexagonal puzzles and their solutions using queen placements.
Each puzzle is generated on a full 8x11 inch page.
"""

import os
import random
import math
import matplotlib.pyplot as plt
from typing import Dict, Optional, Tuple, List
from src.hex_grid import HexGrid, HexCoord
from src.puzzle_visualizer import (
    hex_to_pixel, draw_hexagon, draw_queen, get_region_color,
    calculate_recommended_queens, draw_hex_grid
)
from src.puzzle_generator import generate_puzzle_with_queens

class PuzzlePage:
    """
    Manages the generation of a puzzle along with its solution as separate pages.
    Each puzzle is generated on an 8x11 inch page using queen placements for clues.
    """
    def __init__(self, grid_radius: int, output_path: str = "."):
        """
        Initialize the PuzzlePage.
        
        Args:
            grid_radius: Radius of the puzzle's hex grid.
            output_path: Directory to save the generated pages.
        """
        self.grid_radius = grid_radius
        self.output_path = output_path
        self.figure_width = 8
        self.figure_height = 11

    def create_page(self, page_number: int, seed: Optional[int] = None) -> Optional[List[str]]:
        """
        Create a pair of pages for a puzzle and its solution using queen placements.
        
        Args:
            page_number: Puzzle number for naming output files.
            seed: Random seed for reproducibility.
        
        Returns:
            List of generated filenames: [puzzle_page_filename, solution_page_filename],
            or None if puzzle generation failed.
        """
        grid = HexGrid(self.grid_radius)
        
        # Generate puzzle using the shared function
        success, grid, cell_regions, queen_positions = generate_puzzle_with_queens(grid, seed)
        
        if not success:
            print(f"Warning: Failed to generate a valid queen puzzle for radius {self.grid_radius} (seed: {seed})")
            return None
        
        # In queen mode, the queen positions serve as the clues.
        piece_positions = queen_positions

        # Generate puzzle page (without drawing pieces)
        fig1 = plt.figure(figsize=(self.figure_width, self.figure_height))
        ax1 = fig1.add_subplot(111)
        # For the puzzle page, display the grid and region boundaries
        self._plot_solution(ax1, grid, cell_regions, piece_positions, f"Puzzle {page_number + 1}")
        plt.tight_layout()
        puzzle_filename = os.path.join(self.output_path, f"puzzle_{page_number + 1}_puzzle.png")
        plt.savefig(puzzle_filename)
        plt.close(fig1)
        
        # Generate solution page (with queen markers)
        fig2 = plt.figure(figsize=(self.figure_width, self.figure_height))
        ax2 = fig2.add_subplot(111)
        self._plot_puzzle(ax2, grid, cell_regions, piece_positions, f"Solution {page_number + 1}")
        plt.tight_layout()
        solution_filename = os.path.join(self.output_path, f"puzzle_{page_number + 1}_solution.png")
        plt.savefig(solution_filename)
        plt.close(fig2)
        
        return [puzzle_filename, solution_filename]

    def generate_puzzle_data(self, seed: Optional[int] = None) -> Optional[Tuple[HexGrid, Dict, Dict]]:
        """
        Generate puzzle data using queen placements without rendering, returning the grid, cell regions, and queen positions.
        
        Args:
            seed: Random seed for reproducibility.
            
        Returns:
            Tuple of (grid, cell_regions, queen_positions), or None if generation failed
        """
        grid = HexGrid(self.grid_radius)
        
        # Generate puzzle using the shared function
        success, grid, cell_regions, queen_positions = generate_puzzle_with_queens(grid, seed)
        
        if not success:
            print(f"Warning: Failed to generate a valid queen puzzle for radius {self.grid_radius} (seed: {seed})")
            return None
        
        return grid, cell_regions, queen_positions

    def _plot_puzzle(self, ax, grid: HexGrid, cell_regions: Dict[HexCoord, int], 
                     piece_positions: Dict[int, HexCoord], title: str):
        """
        Plot a single puzzle (solution view with queen markers).
        """
        self._clear_ax(ax)
        draw_hex_grid(ax, grid, cell_regions, piece_positions, show_pieces=True, title=title)
    
    def _plot_solution(self, ax, grid: HexGrid, cell_regions: Dict[HexCoord, int], 
                       piece_positions: Dict[int, HexCoord], title: str):
        """
        Plot the puzzle view (without queen markers).
        """
        self._clear_ax(ax)
        draw_hex_grid(ax, grid, cell_regions, piece_positions, show_pieces=False, title=title)
    
    def _clear_ax(self, ax):
        """
        Clear the axes and set background color.
        """
        ax.clear()
        ax.set_facecolor('white')
        ax.axis('off')

def batch_generate_puzzles(num_puzzles: int, grid_radius: int, output_path: str = ".", seed: Optional[int] = None):
    """
    Batch generate puzzle pairs (puzzle and solution pages) as PNG files.
    
    Args:
        num_puzzles: Number of puzzles to generate.
        grid_radius: Radius of each puzzle's grid.
        output_path: Directory to save the generated pages.
        seed: Random seed for reproducibility.
    """
    rng = random.Random(seed)
    successful_puzzles = 0
    max_attempts = num_puzzles * 2  # Allow for some failures
    
    print(f"Attempting to generate {num_puzzles} puzzles with grid radius {grid_radius}")
    
    for attempt in range(max_attempts):
        if successful_puzzles >= num_puzzles:
            break
            
        page = PuzzlePage(grid_radius, output_path=output_path)
        # Use a consistent seed derivation method
        current_seed = None if seed is None else seed + attempt
        
        result = page.create_page(successful_puzzles, current_seed)
        if result is not None:
            successful_puzzles += 1
            print(f"Successfully generated puzzle {successful_puzzles}/{num_puzzles}")
        else:
            print(f"Failed to generate puzzle (attempt {attempt+1})")
    
    if successful_puzzles < num_puzzles:
        print(f"Warning: Only generated {successful_puzzles}/{num_puzzles} puzzles after {max_attempts} attempts")
    else:
        print(f"Successfully generated all {num_puzzles} puzzles")

def batch_generate_puzzles_pdf(num_puzzles: int, grid_radius: int, output_path: str = ".", seed: Optional[int] = None, rows: int = 1, columns: int = 1):
    """
    Batch generate puzzles and solutions as PDFs with multiple puzzles per sheet.
    
    Args:
        num_puzzles: Number of puzzles to generate.
        grid_radius: Radius of each puzzle's grid.
        output_path: Directory to save the generated PDFs.
        seed: Random seed for reproducibility.
        rows: Number of rows per PDF page.
        columns: Number of columns per PDF page.
    """
    from matplotlib.backends.backend_pdf import PdfPages
    rng = random.Random(seed)
    puzzle_data_list = []
    
    print(f"Attempting to generate {num_puzzles} puzzles with grid radius {grid_radius} for PDF")
    
    successful_puzzles = 0
    max_attempts = num_puzzles * 2  # Allow for some failures
    
    for attempt in range(max_attempts):
        if successful_puzzles >= num_puzzles:
            break
            
        page = PuzzlePage(grid_radius, output_path)
        # Use a consistent seed derivation method
        current_seed = None if seed is None else seed + attempt
        
        data = page.generate_puzzle_data(current_seed)
        if data is not None:
            puzzle_data_list.append(data)
            successful_puzzles += 1
            print(f"Successfully generated puzzle data {successful_puzzles}/{num_puzzles}")
        else:
            print(f"Failed to generate puzzle data (attempt {attempt+1})")
    
    if successful_puzzles < num_puzzles:
        print(f"Warning: Only generated {successful_puzzles}/{num_puzzles} puzzles after {max_attempts} attempts")
        if successful_puzzles == 0:
            print("No puzzles could be generated. Aborting PDF creation.")
            return
        # Adjust num_puzzles to match what we actually generated
        num_puzzles = successful_puzzles
    
    puzzles_pdf_path = os.path.join(output_path, "puzzles.pdf")
    solutions_pdf_path = os.path.join(output_path, "solutions.pdf")
    puzzles_pdf = PdfPages(puzzles_pdf_path)
    solutions_pdf = PdfPages(solutions_pdf_path)
    puzzles_per_sheet = rows * columns
    total_sheets = math.ceil(num_puzzles / puzzles_per_sheet)
    
    for sheet in range(total_sheets):
        fig_puzzle = plt.figure(figsize=(8, 11))
        fig_solution = plt.figure(figsize=(8, 11))
        
        for pos in range(puzzles_per_sheet):
            puzzle_index = sheet * puzzles_per_sheet + pos
            if puzzle_index >= num_puzzles:
                break
                
            ax_puzzle = fig_puzzle.add_subplot(rows, columns, pos+1)
            ax_solution = fig_solution.add_subplot(rows, columns, pos+1)
            
            grid, cell_regions, queen_positions = puzzle_data_list[puzzle_index]
            
            # Use the shared drawing function
            draw_hex_grid(ax_puzzle, grid, cell_regions, {}, show_pieces=False, 
                         title=f"Puzzle {puzzle_index+1}")
            draw_hex_grid(ax_solution, grid, cell_regions, queen_positions, show_pieces=True, 
                         title=f"Solution {puzzle_index+1}")
            
        fig_puzzle.tight_layout()
        fig_solution.tight_layout()
        puzzles_pdf.savefig(fig_puzzle)
        solutions_pdf.savefig(fig_solution)
        plt.close(fig_puzzle)
        plt.close(fig_solution)
        
    puzzles_pdf.close()
    solutions_pdf.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch generate hexagonal puzzle pages on 8x11 paper using queen placements. Use --pdf for PDF output with multiple puzzles per page.")
    parser.add_argument("--num_puzzles", type=int, default=6, help="Number of puzzles to generate (each yields two pages)")
    parser.add_argument("--grid_radius", type=int, default=3, help="Radius for each puzzle's hex grid")
    parser.add_argument("--output", type=str, default=".", help="Output directory for generated pages")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--pdf", action="store_true", help="Generate puzzles as PDFs with multiple puzzles per page")
    parser.add_argument("--rows", type=int, default=3, help="Number of rows per PDF page (only used with --pdf)")
    parser.add_argument("--columns", type=int, default=2, help="Number of columns per PDF page (only used with --pdf)")
    args = parser.parse_args()
    
    if args.pdf:
        batch_generate_puzzles_pdf(args.num_puzzles, args.grid_radius, args.output, args.seed, rows=args.rows, columns=args.columns)
    else:
        batch_generate_puzzles(args.num_puzzles, args.grid_radius, args.output, args.seed)