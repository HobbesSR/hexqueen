"""
HexQueenPuzzle class to represent hexagonal queen puzzles.
"""
from typing import Dict, List, Set, Tuple, Optional
import json
import matplotlib.pyplot as plt
from .hex_grid import HexGrid, HexCoord
from .puzzle_visualizer import draw_hex_grid

class HexQueenPuzzle:
    """
    Represents a HexQueen puzzle with its grid, queen positions, and cell regions.
    
    This class is a simple data container for HexQueen puzzles with basic validation
    and serialization capabilities.
    """

    def __init__(self, grid: HexGrid, queen_positions: Dict[int, HexCoord], cell_regions: Dict[HexCoord, int]):
        """
        Initializes a HexQueenPuzzle.

        Args:
            grid: The HexGrid for the puzzle.
            queen_positions: Dictionary of queen positions (piece_id -> HexCoord).
            cell_regions: Dictionary of cell regions (HexCoord -> region_id).
        """
        self.grid = grid
        self.queen_positions = queen_positions
        self.cell_regions = cell_regions
        # Hardest deduction (set size k, 1=easy .. 4=hard) needed to solve the
        # puzzle by logic alone. None if it was never rated.
        self.difficulty: Optional[int] = None

    def validate(self) -> bool:
        """
        Validates that the puzzle meets basic constraints.
        
        Checks:
        - All queen positions are within the grid
        - All cells in cell_regions are within the grid
        - All queen positions have a corresponding region
        
        Returns:
            bool: True if the puzzle is valid, False otherwise
        """
        # Check that all queen positions are within the grid
        for queen_pos in self.queen_positions.values():
            if not self.grid.is_valid_cell(queen_pos):
                return False
        
        # Check that all cells in cell_regions are within the grid
        for cell in self.cell_regions.keys():
            if not self.grid.is_valid_cell(cell):
                return False
        
        # Check that all queen positions have a corresponding region
        for region_id, queen_pos in self.queen_positions.items():
            if queen_pos not in self.cell_regions or self.cell_regions[queen_pos] != region_id:
                return False
        
        return True

    def visualize_puzzle(self, show_pieces: bool = True, title: str = "Hexagonal Puzzle"):
        """
        Visualize the puzzle with regions and pieces.

        Args:
            show_pieces: Whether to display queen pieces on the visualization.
            title: Title for the plot.
            
        Returns:
            matplotlib.figure.Figure: The figure containing the visualization
        """
        fig, ax = plt.subplots(figsize=(10, 10))
        draw_hex_grid(ax, self.grid, self.cell_regions, self.queen_positions if show_pieces else {}, show_pieces=show_pieces, title=title)
        plt.tight_layout()
        return fig

    def to_json(self) -> str:
        """
        Serializes the HexQueenPuzzle to a JSON string according to the specification.
        
        The puzzle is uniquely defined by:
        - The grid radius (size of the hexagonal grid)
        - The number of regions (equal to the number of queens)
        - The queen positions (represented as region_seeds - each queen is the seed of a region)
        - The mapping of cells to regions
        
        Returns a JSON string with the following structure:
        {
            "grid_radius": <int>,
            "num_regions": <int>,
            "region_seeds": {
                "<region_id>": [<x>, <y>, <z>],  // Cube coordinates of queen positions
                ...
            },
            "cell_regions": {
                "[<x>, <y>, <z>]": <region_id>,  // Mapping of cells to their regions
                ...
            }
        }
        
        Note: The "region_seeds" field represents the queen positions, which serve
        as the seed cells from which each region grows in the puzzle.
        
        Returns:
            str: JSON string representation of the puzzle
        """
        # Format region seeds (queen positions) as [x, y, z] arrays
        region_seeds = {
            str(region_id): [coord.x, coord.y, coord.z]
            for region_id, coord in self.queen_positions.items()
        }
        
        # Format cell regions with string coordinates as keys
        formatted_cell_regions = {
            f"[{cell.x}, {cell.y}, {cell.z}]": region_id
            for cell, region_id in self.cell_regions.items()
        }
        
        data = {
            'grid_radius': self.grid.radius,
            'num_regions': len(self.queen_positions),
            'region_seeds': region_seeds,
            'cell_regions': formatted_cell_regions
        }
        if self.difficulty is not None:
            data['difficulty'] = self.difficulty
        
        return json.dumps(data, indent=4)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'HexQueenPuzzle':
        """
        Creates a HexQueenPuzzle from a JSON string.
        
        Args:
            json_str: JSON string representation of a puzzle
            
        Returns:
            HexQueenPuzzle: The puzzle created from the JSON string
        """
        data = json.loads(json_str)
        
        # Create grid
        grid = HexGrid(data['grid_radius'])
        
        # Parse queen positions
        queen_positions = {}
        for region_id_str, coords in data['region_seeds'].items():
            region_id = int(region_id_str)
            queen_positions[region_id] = HexCoord(coords[0], coords[1], coords[2])
        
        # Parse cell regions
        cell_regions = {}
        for coord_str, region_id in data['cell_regions'].items():
            # Parse the string "[x, y, z]" to get the coordinates
            coords = coord_str.strip('[]').split(',')
            x, y, z = int(coords[0]), int(coords[1]), int(coords[2])
            cell_regions[HexCoord(x, y, z)] = region_id
        
        puzzle = cls(grid, queen_positions, cell_regions)
        puzzle.difficulty = data.get('difficulty')
        return puzzle