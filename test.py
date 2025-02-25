"""
Test script for the hexagonal puzzle solver.
"""
import unittest
import random
from hex_grid import HexGrid, HexCoord
from puzzle_generator import PuzzleGenerator
from solver import PuzzleSolver

class TestHexGrid(unittest.TestCase):
    """Tests for the HexGrid class."""
    
    def test_grid_creation(self):
        """Test that grids of different sizes are created correctly."""
        for radius in range(1, 5):
            grid = HexGrid(radius)
            # Expected number of cells in a hexagonal grid of radius r is 3r(r+1)+1
            expected_cells = 3 * radius * (radius + 1) + 1
            self.assertEqual(len(grid.get_all_cells()), expected_cells)
    
    def test_neighbors(self):
        """Test that neighbors are calculated correctly."""
        grid = HexGrid(3)
        center = HexCoord(0, 0, 0)
        
        # Center should have 6 neighbors
        neighbors = grid.get_neighbors(center)
        self.assertEqual(len(neighbors), 6)
        
        # Check that all neighbors are at distance 1
        for neighbor in neighbors:
            self.assertEqual(center.distance(neighbor), 1)
        
        # Edge cell should have fewer neighbors
        edge = HexCoord(3, -3, 0)
        edge_neighbors = grid.get_neighbors(edge)
        self.assertLess(len(edge_neighbors), 6)
    
    def test_distance(self):
        """Test distance calculation."""
        grid = HexGrid(5)
        a = HexCoord(0, 0, 0)
        b = HexCoord(3, -1, -2)
        
        self.assertEqual(grid.get_distance(a, b), 3)
        self.assertEqual(a.distance(b), 3)


class TestPuzzleGenerator(unittest.TestCase):
    """Tests for the PuzzleGenerator class."""
    
    def test_piece_placement(self):
        """Test that pieces are placed correctly."""
        grid = HexGrid(3)
        generator = PuzzleGenerator(grid, 4, seed=42)
        
        success = generator.place_pieces()
        self.assertTrue(success)
        self.assertEqual(len(generator.piece_positions), 4)
        
        # Check that pieces are at least 1 cell apart
        positions = list(generator.piece_positions.values())
        for i in range(len(positions)):
            for j in range(i+1, len(positions)):
                self.assertGreater(positions[i].distance(positions[j]), 0)
    
    def test_region_growth(self):
        """Test that regions grow correctly."""
        grid = HexGrid(2)
        generator = PuzzleGenerator(grid, 3, seed=42)
        
        generator.place_pieces()
        success = generator.grow_regions()
        self.assertTrue(success)
        
        # Check that all cells are assigned to a region
        self.assertEqual(len(generator.cell_regions), len(grid.get_all_cells()))
        
        # Check that all regions are contiguous
        self.assertTrue(generator.are_all_regions_contiguous())
    
    def test_puzzle_generation(self):
        """Test complete puzzle generation."""
        grid = HexGrid(2)
        generator = PuzzleGenerator(grid, 3, seed=42)
        
        success = generator.generate_puzzle()
        self.assertTrue(success)
        
        # Check puzzle state
        state = generator.get_puzzle_state()
        self.assertEqual(state['grid_radius'], 2)
        self.assertEqual(state['num_pieces'], 3)
        self.assertEqual(len(state['piece_positions']), 3)
        self.assertEqual(len(state['cell_regions']), len(grid.get_all_cells()))


class TestPuzzleSolver(unittest.TestCase):
    """Tests for the PuzzleSolver class."""
    
    def test_naked_singles(self):
        """Test the naked singles technique."""
        grid = HexGrid(2)
        solver = PuzzleSolver(grid, 3)
        
        # Create a simple puzzle with known piece positions
        piece_positions = {
            0: HexCoord(0, 0, 0),
            1: HexCoord(2, -1, -1),
            2: HexCoord(-2, 1, 1)
        }
        
        solver.initialize_from_clues(piece_positions)
        
        # Apply naked singles
        progress = solver.apply_naked_singles()
        
        # Should make some progress on a simple puzzle
        self.assertTrue(progress)
    
    def test_solver_with_generated_puzzle(self):
        """Test the solver with a generated puzzle."""
        # Use a small grid for faster testing
        grid = HexGrid(2)
        generator = PuzzleGenerator(grid, 3, seed=42)
        
        success = generator.generate_puzzle()
        self.assertTrue(success)
        
        # Create a solver with only piece positions as clues
        solver = PuzzleSolver(grid, 3)
        solver.initialize_from_clues(generator.piece_positions)
        
        # Solve the puzzle
        solved = solver.solve()
        self.assertTrue(solved)
        
        # Check that the solution is complete
        solution = solver.get_solution()
        self.assertEqual(len(solution), len(grid.get_all_cells()))
    
    def test_solution_uniqueness(self):
        """Test that generated puzzles have unique solutions."""
        # Use a small grid for faster testing
        grid = HexGrid(2)
        generator = PuzzleGenerator(grid, 3, seed=42)
        
        success = generator.generate_puzzle()
        self.assertTrue(success)
        
        # Check solution uniqueness
        solver = PuzzleSolver(grid, 3)
        solver.initialize_from_clues(generator.piece_positions)
        
        solution_count = solver.count_solutions(2)
        self.assertEqual(solution_count, 1)


if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    
    # Run the tests
    unittest.main()