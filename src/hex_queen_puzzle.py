"""
HexQueenPuzzle class to represent hexagonal queen puzzles.
"""
from typing import Dict, List, Set, Tuple, Optional

from .hex_grid import HexGrid, HexCoord

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
        import matplotlib.pyplot as plt
        from .puzzle_visualizer import draw_hex_grid

        fig, ax = plt.subplots(figsize=(10, 10))
        draw_hex_grid(ax, self.grid, self.cell_regions, self.queen_positions if show_pieces else {}, show_pieces=show_pieces, title=title)
        plt.tight_layout()
        return fig