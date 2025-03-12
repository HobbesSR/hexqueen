"""
Puzzle generator for creating hexagonal grid puzzles with region expansion.
"""
import random
from typing import Dict, List, Set, Tuple, Optional

from .hex_grid import HexGrid, HexCoord
from .hex_queen_puzzle import HexQueenPuzzle
from .interfaces import IRegionGenerator, PuzzleSpecification

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
        
        Queens can see each other if they share the same x, y, or z coordinate.
        
        Args:
            grid: The hexagonal grid
            num_regions: Number of queens/regions to create
            rng: Random number generator
            
        Returns:
            Dictionary mapping region IDs to queen positions, or empty dict if placement failed
        """
        retry_count = 0
        
        while retry_count < self.max_retries:
            queen_positions = {}
            all_cells = list(grid.get_all_cells())
            
            # Shuffle cells for random placement
            rng.shuffle(all_cells)
            
            # Place queens with minimum distance between them
            min_distance = max(1, grid.radius // (num_regions ** 0.5))
            placed_queens = []
            
            for cell in all_cells:
                # Check if this cell is far enough from existing queens
                if all(cell.distance(pos) >= min_distance for pos in placed_queens):
                    # Check if queens can see each other (share same x, y, or z coordinate)
                    if not any(cell.x == pos.x or cell.y == pos.y or cell.z == pos.z for pos in placed_queens):
                        region_id = len(placed_queens)
                        queen_positions[region_id] = cell
                        placed_queens.append(cell)
                        
                        # Check if we've placed all queens
                        if len(placed_queens) == num_regions:
                            # Verify that all queens are correctly placed
                            from .rule_validator import RuleValidator
                            if RuleValidator.check_queen_visibility(grid, queen_positions):
                                return queen_positions
                            else:
                                # If validation fails, try again
                                break
            
            # If we get here, we couldn't place all queens, so try again
            retry_count += 1
            if retry_count % 10 == 0:
                print(f"Retry {retry_count}: Placed {len(placed_queens)}/{num_regions} queens")
        
        # If we've exceeded max retries, return empty dict
        print(f"Failed to place queens after {self.max_retries} retries")
        return {}