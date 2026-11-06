"""
Interfaces and data classes for the HexQueen puzzle architecture.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .hex_grid import HexGrid, HexCoord

class IRegionGenerator(ABC):
    """
    Interface for region generation strategies in HexQueen puzzles.
    
    Region generators are responsible for creating and validating the regions
    in a HexQueen puzzle based on queen positions.
    """
    
    @abstractmethod
    def generate_regions(self, grid: HexGrid, queen_positions: Dict[int, HexCoord]) -> Dict[HexCoord, int]:
        """
        Generate regions for a HexQueen puzzle.
        
        Args:
            grid: The hexagonal grid for the puzzle
            queen_positions: Dictionary mapping region IDs to queen positions
            
        Returns:
            Dictionary mapping cells to their region IDs
        """
        pass
    
    @abstractmethod
    def validate_regions(self, grid: HexGrid, cell_regions: Dict[HexCoord, int]) -> bool:
        """
        Validate that the regions in a puzzle meet all constraints.
        
        Args:
            grid: The hexagonal grid for the puzzle
            cell_regions: Dictionary mapping cells to their region IDs
            
        Returns:
            True if the regions are valid, False otherwise
        """
        pass


@dataclass
class PuzzleSpecification:
    """
    Data class containing the specifications for generating a HexQueen puzzle.
    """
    grid: HexGrid
    num_regions: int
    queen_positions: Dict[int, HexCoord] = field(default_factory=dict)
    region_constraints: Dict = field(default_factory=dict)
    seed: Optional[int] = None
    # Quality guarantees (requirements 213 / 214). Both are enforced by
    # refining the region layout, not by rejection sampling.
    require_unique: bool = True
    require_logical: bool = True
    # Largest deduction set size the player may need (1=easy ... 4=hard).
    max_difficulty: int = 3
    max_attempts: int = 20