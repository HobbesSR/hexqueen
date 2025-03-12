"""
HexQueenPuzzle class to represent hexagonal queen puzzles.
"""
from typing import Dict, List, Set, Tuple, Optional
import matplotlib.pyplot as plt
from .hex_grid import HexGrid, HexCoord
from .puzzle_visualizer import draw_hex_grid

class HexQueenPuzzle:
    """
    Represents a HexQueen puzzle with its grid, queen positions, and cell regions.
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

    def visualize_puzzle(self, show_pieces: bool = True, title: str = "Hexagonal Puzzle"):
        """
        Visualize the puzzle with regions and pieces.

        Args:
            show_pieces: Whether to display queen pieces on the visualization.
            title: Title for the plot.
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
        """
        import json
        
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
        
        return json.dumps(data, indent=4)