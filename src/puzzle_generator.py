"""
Puzzle generator for creating hexagonal grid puzzles with region expansion.
"""
import random
from typing import Dict, List, Set, Tuple, Optional

from .hex_grid import HexGrid, HexCoord
from .hex_queen_puzzle import HexQueenPuzzle
from .interfaces import IRegionGenerator, PuzzleSpecification
from .queen_placer import QueenPlacer

class PuzzleGenerator:
    """
    Generates puzzles on a hexagonal grid using a region generation strategy.
    
    This class follows the dependency injection pattern, accepting an IRegionGenerator
    implementation to handle the region generation logic.
    """
    def __init__(self, region_generator: IRegionGenerator):
        """
        Initialize the puzzle generator with a region generation strategy.
        
        Args:
            region_generator: The region generator to use for creating regions
        """
        self.region_generator = region_generator
        self.max_retries = 500  # Increased from 100 to give more chances for larger grids
    
    def generate_puzzle(self, spec: PuzzleSpecification) -> Optional[HexQueenPuzzle]:
        """
        Generate a complete puzzle based on the provided specification.
        
        Args:
            spec: The puzzle specification containing grid, number of regions, etc.
            
        Returns:
            HexQueenPuzzle object if puzzle generation is successful, None otherwise
        """
        grid = spec.grid
        num_regions = spec.num_regions
        rng = random.Random(spec.seed)
        
        # If queen positions are provided, use them
        if spec.queen_positions:
            queen_positions = spec.queen_positions
        else:
            # Otherwise, generate queen positions
            queen_positions = self._place_queens(grid, num_regions, rng)
            if not queen_positions:
                return None
        
        # Generate regions using the region generator
        cell_regions = self.region_generator.generate_regions(grid, queen_positions)
        if not cell_regions:
            return None
        
        # Create and return the puzzle
        puzzle = HexQueenPuzzle(grid, queen_positions, cell_regions)
        if not puzzle.validate():
            return None
            
        return puzzle
    
    def _place_queens(self, grid: HexGrid, num_regions: int, rng: random.Random) -> Dict[int, HexCoord]:
        """
        Place queens randomly on the grid ensuring they can't see each other.
        
        Uses the QueenPlacer class to place queens consistently across the application.
        
        Args:
            grid: The hexagonal grid
            num_regions: Number of queens/regions to create
            rng: Random number generator
            
        Returns:
            Dictionary mapping region IDs to queen positions, or empty dict if placement failed
        """
        print(f"Attempting to place {num_regions} queens on a grid with radius {grid.radius}")
        print(f"Total cells in grid: {len(grid.get_all_cells())}")
        
        # Create a seed from the random number generator's state
        seed_value = None
        if rng is not None:
            # Get a value from the RNG to use as a seed
            seed_value = rng.randint(0, 1000000)
        
        # Create a QueenPlacer instance
        placer = QueenPlacer(grid, num_regions, seed_value)
        
        # Try to place queens using the QueenPlacer
        if placer.place_queens(max_attempts=self.max_retries):
            queen_positions = placer.get_queen_positions()
            
            # Verify that all queens are correctly placed
            from .rule_validator import RuleValidator
            if RuleValidator.check_queen_visibility(grid, queen_positions):
                print(f"Successfully placed all {num_regions} queens")
                return queen_positions
            else:
                print(f"Queen visibility validation failed after placing all queens")
        
        # If we've exceeded max retries, return empty dict
        print(f"Failed to place queens after {self.max_retries} retries")
        print(f"Grid radius: {grid.radius}, Number of queens: {num_regions}")
        return {}


def generate_puzzle_with_queens(grid: HexGrid, seed: Optional[int] = None, max_attempts: int = 3):
    """
    Generate a puzzle using queen placements.
    
    This function uses the PuzzleGenerator class to ensure consistent puzzle generation
    across the application.
    
    Args:
        grid: The hexagonal grid
        seed: Random seed for reproducibility
        max_attempts: Maximum number of attempts to generate a valid puzzle
        
    Returns:
        Tuple of (success, grid, cell_regions, queen_positions)
    """
    from .growth_region_generator import GrowthRegionGenerator
    from .interfaces import PuzzleSpecification
    
    # Import calculate_recommended_queens from puzzle_visualizer
    # This avoids circular imports
    from .puzzle_visualizer import calculate_recommended_queens
    
    # Scale max_attempts based on grid radius for larger grids
    if grid.radius > 8:
        max_attempts = max(max_attempts, grid.radius * 2)
    
    print(f"Attempting to generate puzzle with radius {grid.radius}, "
          f"queens {calculate_recommended_queens(grid.radius)}, max attempts {max_attempts}")
    
    # Create region generator and puzzle generator
    region_generator = GrowthRegionGenerator(seed)
    generator = PuzzleGenerator(region_generator)
    
    # Set max retries for the generator
    generator.max_retries = max_attempts * 100  # Give it plenty of attempts
    
    # Calculate recommended number of queens
    num_queens = calculate_recommended_queens(grid.radius)
    
    # Create puzzle specification
    spec = PuzzleSpecification(
        grid=grid,
        num_regions=num_queens,
        seed=seed,
        ensure_unique=True,
        ensure_logical=True
    )
    
    # Generate a puzzle
    puzzle = generator.generate_puzzle(spec)
    
    if puzzle:
        print(f"Successfully generated puzzle")
        return True, grid, puzzle.cell_regions, puzzle.queen_positions
    else:
        print(f"Failed to generate puzzle after {max_attempts} attempts")
        return False, grid, {}, {}