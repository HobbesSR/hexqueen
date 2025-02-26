"""
Tests for the reverse engineering solver.
"""
import unittest
import random
import sys
import os
import time
import traceback

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath('..'))

from src.hex_grid import HexGrid, HexCoord
from src.puzzle_generator import PuzzleGenerator
from src.solver import PuzzleSolver
from src.advanced_solver import AdvancedPuzzleSolver
from src.reverse_engineering_solver import ReverseEngineeringSolver

class TestReverseEngineeringSolver(unittest.TestCase):
    """Test cases for the reverse engineering solver."""
    
    def setUp(self):
        """Set up test fixtures."""
        print("\nSetting up test...")
        start_time = time.time()
        
        self.seed = 42
        self.grid_radius = 2  # Reduced from 3 to make tests faster
        self.num_pieces = 3   # Reduced from 5 to make tests faster
        
        # Create a grid
        self.grid = HexGrid(self.grid_radius)
        print(f"Grid created with radius {self.grid_radius}, {len(self.grid.get_all_cells())} cells")
        
        # Generate a puzzle
        print(f"Generating puzzle with {self.num_pieces} pieces...")
        self.generator = PuzzleGenerator(self.grid, self.num_pieces, self.seed)
        try:
            self.generator.generate_puzzle()
            print(f"Puzzle generation completed in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            print(f"Error during puzzle generation: {e}")
            traceback.print_exc()
            raise
        
        # Get the solution
        self.solution = self.generator.cell_regions
        self.piece_positions = self.generator.piece_positions
        print(f"Setup completed in {time.time() - start_time:.2f} seconds")
    
    def test_initialization(self):
        """Test initialization of the reverse engineering solver."""
        print("\nTesting initialization...")
        start_time = time.time()
        
        solver = ReverseEngineeringSolver(self.grid, self.num_pieces, self.seed)
        solver.initialize_from_solution(self.solution, self.piece_positions)
        
        # Check that the solution and piece positions are correctly stored
        self.assertEqual(solver.solution, self.solution)
        self.assertEqual(solver.piece_positions, self.piece_positions)
        
        # Check that all non-piece cells are initially fixed
        expected_fixed_cells = {cell: region_id for cell, region_id in self.solution.items()
                               if cell not in self.piece_positions.values()}
        self.assertEqual(solver.fixed_cells, expected_fixed_cells)
        
        print(f"Initialization test completed in {time.time() - start_time:.2f} seconds")
    
    def test_is_uniquely_solvable(self):
        """Test checking if a puzzle is uniquely solvable."""
        print("\nTesting is_uniquely_solvable...")
        start_time = time.time()
        
        solver = ReverseEngineeringSolver(self.grid, self.num_pieces, self.seed)
        solver.initialize_from_solution(self.solution, self.piece_positions)
        
        # With all cells fixed, the puzzle should be uniquely solvable
        print("Checking with all cells fixed...")
        self.assertTrue(solver.is_uniquely_solvable(timeout_seconds=3))
        
        # Remove all fixed cells
        solver.fixed_cells = {}
        
        # With only piece positions, the puzzle might not be uniquely solvable
        # (depends on the specific puzzle, but we can at least run the method)
        print("Checking with only piece positions...")
        result = solver.is_uniquely_solvable(timeout_seconds=3)
        print(f"Result with only piece positions: {result}")
        
        print(f"is_uniquely_solvable test completed in {time.time() - start_time:.2f} seconds")
    
    def test_find_minimal_clues(self):
        """Test finding the minimal set of clues needed for a unique solution."""
        print("\nTesting find_minimal_clues...")
        start_time = time.time()
        
        solver = ReverseEngineeringSolver(self.grid, self.num_pieces, self.seed)
        solver.initialize_from_solution(self.solution, self.piece_positions)
        
        # Find minimal clues with reduced parameters for testing
        print("Finding minimal clues...")
        minimal_clues = solver.find_minimal_clues(
            max_cells=10,  # Reduced from default
            total_timeout=15  # Short timeout for testing
        )
        print(f"Found {len(minimal_clues)} minimal clues")
        
        # Check that the minimal clues are a subset of the original fixed cells
        original_fixed_cells = {cell: region_id for cell, region_id in self.solution.items()
                               if cell not in self.piece_positions.values()}
        for cell, region_id in minimal_clues.items():
            self.assertIn(cell, original_fixed_cells)
            self.assertEqual(region_id, original_fixed_cells[cell])
        
        # Check that the puzzle is still uniquely solvable with minimal clues
        solver.fixed_cells = minimal_clues
        print("Verifying unique solvability...")
        self.assertTrue(solver.is_uniquely_solvable(timeout_seconds=3))
        
        # Check metrics
        metrics = solver.get_metrics()
        self.assertGreaterEqual(metrics['initial_clues'], metrics['final_clues'])
        self.assertEqual(metrics['removed_clues'], metrics['initial_clues'] - metrics['final_clues'])
        
        print(f"find_minimal_clues test completed in {time.time() - start_time:.2f} seconds")
    
    def test_find_minimal_clues_by_importance(self):
        """Test finding the minimal set of clues by importance."""
        print("\nTesting find_minimal_clues_by_importance...")
        start_time = time.time()
        
        solver = ReverseEngineeringSolver(self.grid, self.num_pieces, self.seed)
        solver.initialize_from_solution(self.solution, self.piece_positions)
        
        # Find minimal clues by importance with reduced parameters for testing
        print("Finding minimal clues by importance...")
        minimal_clues = solver.find_minimal_clues_by_importance(
            max_cells=10,  # Reduced from default
            total_timeout=15  # Short timeout for testing
        )
        print(f"Found {len(minimal_clues)} minimal clues")
        
        # Check that the minimal clues are a subset of the original fixed cells
        original_fixed_cells = {cell: region_id for cell, region_id in self.solution.items()
                               if cell not in self.piece_positions.values()}
        for cell, region_id in minimal_clues.items():
            self.assertIn(cell, original_fixed_cells)
            self.assertEqual(region_id, original_fixed_cells[cell])
        
        # Check that the puzzle is still uniquely solvable with minimal clues
        solver.fixed_cells = minimal_clues
        print("Verifying unique solvability...")
        self.assertTrue(solver.is_uniquely_solvable(timeout_seconds=3))
        
        # Check metrics
        metrics = solver.get_metrics()
        self.assertGreaterEqual(metrics['initial_clues'], metrics['final_clues'])
        self.assertEqual(metrics['removed_clues'], metrics['initial_clues'] - metrics['final_clues'])
        
        print(f"find_minimal_clues_by_importance test completed in {time.time() - start_time:.2f} seconds")
    
    def test_generate_challenging_puzzle(self):
        """Test generating a challenging puzzle."""
        print("\nTesting generate_challenging_puzzle...")
        start_time = time.time()
        
        solver = ReverseEngineeringSolver(self.grid, self.num_pieces, self.seed)
        solver.initialize_from_solution(self.solution, self.piece_positions)
        
        # Generate a challenging puzzle with reduced parameters for testing
        print("Generating challenging puzzle...")
        piece_positions, fixed_cells = solver.generate_challenging_puzzle(
            max_cells=10,  # Reduced from default
            total_timeout=15  # Short timeout for testing
        )
        print(f"Generated puzzle with {len(fixed_cells)} fixed cells")
        
        # Check that the piece positions match
        self.assertEqual(piece_positions, self.piece_positions)
        
        # Check that the fixed cells are a subset of the original solution
        for cell, region_id in fixed_cells.items():
            self.assertIn(cell, self.solution)
            self.assertEqual(region_id, self.solution[cell])
        
        # Check that the puzzle is uniquely solvable
        solver.fixed_cells = fixed_cells
        print("Verifying unique solvability...")
        self.assertTrue(solver.is_uniquely_solvable(timeout_seconds=3))
        
        print(f"generate_challenging_puzzle test completed in {time.time() - start_time:.2f} seconds")

if __name__ == '__main__':
    unittest.main()