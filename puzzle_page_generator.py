"""
Generates pages with hexagonal puzzles and their solutions.
Each puzzle is rendered on an 8x11 inch page. Optionally, puzzles can be generated
using queen placements (via --queens), which places queens and grows regions from their positions.
"""

import os
import random
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import Dict, Optional, Tuple
from hex_grid import HexGrid, HexCoord
from puzzle_generator import PuzzleGenerator

class PuzzlePage:
    """
    Manages the generation of a puzzle along with its solution as separate pages.
    Each puzzle is generated on a full 8x11 inch page.
    """
    def __init__(self, grid_radius: int, output_path: str = ".", use_queens: bool = False):
        """
        Initialize the PuzzlePage.
        
        Args:
            grid_radius: Radius of the puzzle's hex grid.
            output_path: Directory to save the generated pages.
            use_queens: If True, generate the puzzle via queen placement.
        """
        self.grid_radius = grid_radius
        self.output_path = output_path
        self.figure_width = 8
        self.figure_height = 11
        self.use_queens = use_queens

    def create_page(self, page_number: int, seed: Optional[int] = None):
        """
        Create a pair of pages for a puzzle and its solution.
        
        Args:
            page_number: Puzzle number for naming output files.
            seed: Random seed for reproducibility.
        
        Returns:
            List of generated filenames: [puzzle_page_filename, solution_page_filename].
        """
        grid = HexGrid(self.grid_radius)
        if self.use_queens:
            from queen_placer import QueenPlacer
            max_attempts = 3
            attempt = 0
            valid = False
            while attempt < max_attempts and not valid:
                rng = random.Random(seed)
                num_queens = self.grid_radius * 2 + 1
                placer = QueenPlacer(grid, num_queens, seed)
                if not placer.place_queens():
                    attempt += 1
                    if seed is not None:
                        seed += 1
                    continue
                queen_positions = placer.get_queen_positions()
                valid, cell_regions, regions = self.grow_regions_from_queens(grid, queen_positions, rng)
                if valid and not self._regions_are_contiguous(grid, regions):
                    valid = False
                if not valid:
                    attempt += 1
                    if seed is not None:
                        seed += 1
            if not valid:
                raise Exception("Failed to generate a valid queen puzzle after several attempts.")
            # In queen mode, we use queen positions as the clues.
            piece_positions = queen_positions
        else:
            max_attempts = 3
            attempt = 0
            valid = False
            while attempt < max_attempts and not valid:
                generator = PuzzleGenerator(grid, grid.radius * 2 + 1, seed)
                valid = generator.generate_puzzle()
                if not valid:
                    attempt += 1
                    if seed is not None:
                        seed += 1
            if not valid:
                raise Exception(f"Failed to generate a valid puzzle after {max_attempts} attempts")
            cell_regions = generator.cell_regions.copy()
            piece_positions = generator.piece_positions

        # Generate puzzle page (without pieces/queens)
        fig1 = plt.figure(figsize=(self.figure_width, self.figure_height))
        ax1 = fig1.add_subplot(111)
        self._plot_solution(ax1, grid, cell_regions, piece_positions, f"Puzzle {page_number + 1}")
        plt.tight_layout()
        puzzle_filename = os.path.join(self.output_path, f"puzzle_{page_number + 1}_puzzle.png")
        plt.savefig(puzzle_filename)
        plt.close(fig1)
        
        # Generate solution page (with pieces/queens)
        fig2 = plt.figure(figsize=(self.figure_width, self.figure_height))
        ax2 = fig2.add_subplot(111)
        self._plot_puzzle(ax2, grid, cell_regions, piece_positions, f"Solution {page_number + 1}")
        plt.tight_layout()
        solution_filename = os.path.join(self.output_path, f"puzzle_{page_number + 1}_solution.png")
        plt.savefig(solution_filename)
        plt.close(fig2)
        
        return [puzzle_filename, solution_filename]

    def generate_puzzle_data(self, seed: Optional[int] = None) -> Tuple[HexGrid, Dict, Dict]:
        """
        Generate puzzle data without rendering, returning the grid, cell regions, and piece positions.
        
        Args:
            seed: Random seed for reproducibility.
            
        Returns:
            Tuple of (grid, cell_regions, piece_positions)
        """
        grid = HexGrid(self.grid_radius)
        if self.use_queens:
            from queen_placer import QueenPlacer
            max_attempts = 3
            attempt = 0
            valid = False
            while attempt < max_attempts and not valid:
                rng_local = random.Random(seed)
                num_queens = self.grid_radius * 2 + 1
                placer = QueenPlacer(grid, num_queens, seed)
                if not placer.place_queens():
                    attempt += 1
                    if seed is not None:
                        seed += 1
                    continue
                queen_positions = placer.get_queen_positions()
                valid, cell_regions, regions = self.grow_regions_from_queens(grid, queen_positions, rng_local)
                if valid and not self._regions_are_contiguous(grid, regions):
                    valid = False
                if not valid:
                    attempt += 1
                    if seed is not None:
                        seed += 1
            if not valid:
                raise Exception("Failed to generate a valid queen puzzle after several attempts.")
            piece_positions = queen_positions
            return grid, cell_regions, piece_positions
        else:
            max_attempts = 3
            attempt = 0
            valid = False
            while attempt < max_attempts and not valid:
                generator = PuzzleGenerator(grid, grid.radius * 2 + 1, seed)
                valid = generator.generate_puzzle()
                if not valid:
                    attempt += 1
                    if seed is not None:
                        seed += 1
            if not valid:
                raise Exception(f"Failed to generate a valid puzzle after {max_attempts} attempts")
            cell_regions = generator.cell_regions.copy()
            piece_positions = generator.piece_positions
            return grid, cell_regions, piece_positions

    def grow_regions_from_queens(self, grid: HexGrid, queen_positions: Dict[int, HexCoord], rng: random.Random):
        """
        Grow regions from queen positions using a randomized approach.
        
        Args:
            grid: The hexagonal grid.
            queen_positions: Mapping of queen IDs to their positions.
            rng: Random number generator.
            
        Returns:
            Tuple of (success, cell_regions, regions).
        """
        from collections import defaultdict
        regions = defaultdict(set)
        cell_regions = {}
        # Initialize regions with queen positions
        for queen_id, pos in queen_positions.items():
            regions[queen_id].add(pos)
            cell_regions[pos] = queen_id
        # Unassigned cells
        unassigned_cells = set(grid.get_all_cells()) - set(queen_positions.values())
        bordering_cells = defaultdict(set)
        for queen_id, pos in queen_positions.items():
            for neighbor in grid.get_neighbors(pos):
                if neighbor in unassigned_cells:
                    bordering_cells[queen_id].add(neighbor)
        # Grow regions until all cells are assigned
        while unassigned_cells:
            active_regions = [r for r, cells in bordering_cells.items() if cells]
            if not active_regions:
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

    def _regions_are_contiguous(self, grid: HexGrid, regions: Dict[int, set]) -> bool:
        """
        Check that every region is contiguous using BFS.
        
        Args:
            grid: The hexagonal grid.
            regions: Mapping of region id to set of cells.
            
        Returns:
            True if all regions are contiguous, False otherwise.
        """
        from collections import deque
        for region_id, cells in regions.items():
            if not cells:
                continue
            start = next(iter(cells))
            visited = {start}
            queue = deque([start])
            while queue:
                current = queue.popleft()
                for neighbor in grid.get_neighbors(current):
                    if neighbor in cells and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            if len(visited) != len(cells):
                return False
        return True

    def _plot_puzzle(self, ax, grid: HexGrid, cell_regions: Dict[HexCoord, int], 
                     piece_positions: Dict[int, HexCoord], title: str):
        """
        Plot a single puzzle.
        """
        self._clear_ax(ax)
        self._draw_hex_grid(ax, grid, cell_regions, piece_positions, show_pieces=False)
        ax.set_title(title)
    
    def _plot_solution(self, ax, grid: HexGrid, cell_regions: Dict[HexCoord, int], 
                       piece_positions: Dict[int, HexCoord], title: str):
        """
        Plot the solution for a puzzle.
        """
        self._clear_ax(ax)
        self._draw_hex_grid(ax, grid, cell_regions, piece_positions, show_pieces=True)
        ax.set_title(title)
    
    def _draw_hex_grid(self, ax, grid: HexGrid, cell_regions: Dict[HexCoord, int], 
                       piece_positions: Dict[int, HexCoord], show_pieces: bool = True):
        """
        Draw the hex grid with regions and pieces.
        """
        hex_size = 0.5
        
        for cell in grid.get_all_cells():
            pixel = self.hex_to_pixel(cell, hex_size)
            if cell in cell_regions:
                region_id = cell_regions[cell]
                color = self.get_region_color(region_id)
                self._draw_hex(ax, pixel, hex_size, color)
        
        if show_pieces:
            for pos in piece_positions.values():
                pixel = self.hex_to_pixel(pos, hex_size)
                self._draw_piece(ax, pixel)
        
        ax.set_aspect('equal')
        ax.set_xlim([-2*grid.radius, 2*grid.radius])
        ax.set_ylim([-2*grid.radius, 2*grid.radius])
        ax.axis('off')
    
    def _draw_hex(self, ax, center: Tuple[float, float], size: float, color: str):
        """
        Draw a hexagon on the given axes.
        """
        angles = np.linspace(0, 2*np.pi, 7)[:-1]
        x = center[0] + size * np.cos(angles)
        y = center[1] + size * np.sin(angles)
        
        hex_patch = patches.Polygon(np.column_stack([x, y]), closed=True, 
                                    fill=True, color=color, alpha=0.8, 
                                    edgecolor='black', linewidth=0.5)
        ax.add_patch(hex_patch)
    
    def _draw_piece(self, ax, center: Tuple[float, float]):
        """
        Draw a piece (or queen) on the given axes.
        """
        ax.plot(center[0], center[1], 'o', markersize=10, color='black')
    
    def hex_to_pixel(self, coord: HexCoord, size: float = 1.0) -> Tuple[float, float]:
        """
        Convert hex coordinates to pixel coordinates.
        """
        x = size * (3/2 * coord.x)
        y = size * (np.sqrt(3)/2 * coord.x + np.sqrt(3) * coord.z)
        return (x, y)
    
    def get_region_color(self, region_id: int) -> str:
        """
        Get a color for a region using a colormap.
        """
        cmap = plt.cm.get_cmap('tab20', 20)
        return cmap(region_id % 20)
    
    def _clear_ax(self, ax):
        """
        Clear the axes and set background color.
        """
        ax.clear()
        ax.set_facecolor('white')
        ax.axis('off')

def batch_generate_puzzles(num_puzzles: int, grid_radius: int, output_path: str = ".", seed: Optional[int] = None, use_queens: bool = False):
    """
    Batch generate puzzle pairs (puzzle and solution pages) as PNG files.
    
    Args:
        num_puzzles: Number of puzzles to generate.
        grid_radius: Radius of each puzzle's grid.
        output_path: Directory to save the generated pages.
        seed: Random seed for reproducibility.
        use_queens: If True, generate puzzles using queen placements.
    """
    rng = random.Random(seed)
    
    for puzzle_number in range(num_puzzles):
        page = PuzzlePage(grid_radius, output_path=output_path, use_queens=use_queens)
        current_seed = rng.randint(1, 10000)
        page.create_page(puzzle_number, current_seed)

def batch_generate_puzzles_pdf(num_puzzles: int, grid_radius: int, output_path: str = ".", seed: Optional[int] = None, use_queens: bool = False, rows: int = 1, columns: int = 1):
    """
    Batch generate puzzles and solutions as PDFs with multiple puzzles per sheet.
    
    Args:
        num_puzzles: Number of puzzles to generate.
        grid_radius: Radius of each puzzle's grid.
        output_path: Directory to save the generated PDFs.
        seed: Random seed for reproducibility.
        use_queens: If True, generate puzzles using queen placements.
        rows: Number of rows per PDF page.
        columns: Number of columns per PDF page.
    """
    from matplotlib.backends.backend_pdf import PdfPages
    rng = random.Random(seed)
    puzzle_data_list = []
    for puzzle_number in range(num_puzzles):
        page = PuzzlePage(grid_radius, output_path=output_path, use_queens=use_queens)
        current_seed = rng.randint(1, 10000)
        data = page.generate_puzzle_data(current_seed)
        puzzle_data_list.append(data)
    
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
            dummy_page = PuzzlePage(grid_radius, output_path, use_queens)
            dummy_page._plot_puzzle(ax_puzzle, *puzzle_data_list[puzzle_index], title=f"Puzzle {puzzle_index+1}")
            dummy_page._plot_solution(ax_solution, *puzzle_data_list[puzzle_index], title=f"Solution {puzzle_index+1}")
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
    parser = argparse.ArgumentParser(description="Batch generate hexagonal puzzle pages on 8x11 paper. Use --queens for queen placement puzzles. Use --pdf for PDF output with multiple puzzles per page.")
    parser.add_argument("--num_puzzles", type=int, default=1, help="Number of puzzles to generate (each yields two pages)")
    parser.add_argument("--grid_radius", type=int, default=3, help="Radius for each puzzle's hex grid")
    parser.add_argument("--output", type=str, default=".", help="Output directory for generated pages")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--queens", action="store_true", help="Generate puzzles using queen placements")
    parser.add_argument("--pdf", action="store_true", help="Generate puzzles as PDFs with multiple puzzles per page")
    parser.add_argument("--rows", type=int, default=1, help="Number of rows per PDF page (only used with --pdf)")
    parser.add_argument("--columns", type=int, default=1, help="Number of columns per PDF page (only used with --pdf)")
    args = parser.parse_args()
    
    if args.pdf:
        batch_generate_puzzles_pdf(args.num_puzzles, args.grid_radius, args.output, args.seed, use_queens=args.queens, rows=args.rows, columns=args.columns)
    else:
        batch_generate_puzzles(args.num_puzzles, args.grid_radius, args.output, args.seed, use_queens=args.queens)