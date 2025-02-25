"""
Queen placer for hexagonal grid puzzles.
"""
import random
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from hex_grid import HexGrid, HexCoord

class QueenPlacer:
    """
    Places queens on a hexagonal grid such that no two queens attack each other.
    Queens attack along straight lines (like rooks in chess) and cannot be adjacent.
    """
    def __init__(self, grid: HexGrid, num_queens: int, seed: Optional[int] = None):
        """
        Initialize the queen placer.
        
        Args:
            grid: The hexagonal grid
            num_queens: Number of queens to place
            seed: Random seed for reproducibility
        """
        self.grid = grid
        self.num_queens = num_queens
        self.rng = random.Random(seed)
        
        # Queen positions
        self.queen_positions = {}  # Maps queen_id -> HexCoord
        
        # Cells that are under attack
        self.attacked_cells = set()
    
    def is_cell_attacked(self, cell: HexCoord, exclude_queen: Optional[int] = None) -> bool:
        """
        Check if a cell is under attack by any queen.
        
        Args:
            cell: The cell to check
            exclude_queen: Optional queen ID to exclude from the check
            
        Returns:
            bool: True if the cell is under attack, False otherwise
        """
        # Check if the cell is already occupied by a queen
        for queen_id, pos in self.queen_positions.items():
            if queen_id == exclude_queen:
                continue
            if pos == cell:
                return True
        
        # Check if the cell is adjacent to any queen
        for queen_id, pos in self.queen_positions.items():
            if queen_id == exclude_queen:
                continue
            if pos.distance(cell) == 1:
                return True
        
        # Check if the cell is in line with any queen
        for queen_id, pos in self.queen_positions.items():
            if queen_id == exclude_queen:
                continue
            
            # Check if they're in the same line (same x, y, or z coordinate)
            if pos.x == cell.x or pos.y == cell.y or pos.z == cell.z:
                return True
        
        return False
    
    def update_attacked_cells(self):
        """Update the set of cells that are under attack."""
        self.attacked_cells = set()
        
        for cell in self.grid.get_all_cells():
            if self.is_cell_attacked(cell):
                self.attacked_cells.add(cell)
    
    def get_available_cells(self) -> List[HexCoord]:
        """
        Get cells that are not under attack.
        
        Returns:
            List of cells that are not under attack
        """
        return [cell for cell in self.grid.get_all_cells() if cell not in self.attacked_cells]
    
    def place_queens_random(self) -> bool:
        """
        Place queens randomly on the grid.
        
        Returns:
            bool: True if all queens were placed successfully, False otherwise
        """
        self.queen_positions = {}
        self.attacked_cells = set()
        
        # Try to place each queen
        for queen_id in range(self.num_queens):
            available_cells = self.get_available_cells()
            
            if not available_cells:
                return False
            
            # Choose a random available cell
            cell = self.rng.choice(available_cells)
            
            # Place the queen
            self.queen_positions[queen_id] = cell
            
            # Update attacked cells
            self.update_attacked_cells()
        
        return True
    
    def place_queens_backtracking(self) -> bool:
        """
        Place queens using backtracking.
        
        Returns:
            bool: True if all queens were placed successfully, False otherwise
        """
        self.queen_positions = {}
        return self._place_queens_recursive(0)
    
    def _place_queens_recursive(self, queen_id: int) -> bool:
        """
        Recursively place queens using backtracking.
        
        Args:
            queen_id: The ID of the queen to place
            
        Returns:
            bool: True if the queen and all subsequent queens were placed successfully,
                 False otherwise
        """
        if queen_id == self.num_queens:
            return True
        
        # Get available cells
        available_cells = self.get_available_cells()
        
        if not available_cells:
            return False
        
        # Shuffle available cells for randomness
        available_cells = list(available_cells)
        self.rng.shuffle(available_cells)
        
        for cell in available_cells:
            # Place the queen
            self.queen_positions[queen_id] = cell
            self.update_attacked_cells()
            
            # Recursively place the next queen
            if self._place_queens_recursive(queen_id + 1):
                return True
            
            # Backtrack
            del self.queen_positions[queen_id]
            self.update_attacked_cells()
        
        return False
    
    def place_queens(self, max_attempts: int = 100) -> bool:
        """
        Place queens on the grid.
        
        Args:
            max_attempts: Maximum number of attempts for random placement
            
        Returns:
            bool: True if queens were placed successfully, False otherwise
        """
        # Try random placement first (faster for small grids)
        for _ in range(max_attempts):
            if self.place_queens_random():
                return True
        
        # If random placement fails, use backtracking
        return self.place_queens_backtracking()
    
    def get_queen_positions(self) -> Dict[int, HexCoord]:
        """Get the positions of the queens."""
        return self.queen_positions.copy()