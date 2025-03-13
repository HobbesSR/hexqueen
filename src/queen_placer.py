"""
Queen placer for hexagonal grid puzzles.
"""
import random
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from .hex_grid import HexGrid, HexCoord

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
    
    def place_queens(self) -> bool:
        """
        Place queens on the grid.
        
        Args:
            max_attempts: Maximum number of attempts for random placement
            
        Returns:
            bool: True if queens were placed successfully, False otherwise
        """
        print(f"Attempting to place {self.num_queens} queens on a grid with radius {self.grid.radius}")
        print(f"Total cells in grid: {len(self.grid.get_all_cells())}")
        
        # Try Dancing Links first (most efficient approach)
        try:
            if self.place_queens_dlx():
                print("Successfully placed queens using Dancing Links (Algorithm X)")
                return True
        except Exception as e:
            print(f"Dancing Links approach failed with error: {e}")                   
        
        return False
    
    def place_queens_dlx(self) -> bool:
        """
        Place queens using Knuth's Algorithm X with Dancing Links.
        
        This method formulates the hexagonal queen placement as an exact cover problem
        and solves it using the Dancing Links technique.
        
        In a hexagonal grid with cube coordinates (x, y, z), queens attack along straight lines
        (same x, y, or z coordinate) and cannot be adjacent.
        
        Returns:
            bool: True if all queens were placed successfully, False otherwise
        """
        from .dancing_links import DancingLinks
        
        print(f"Attempting to place {self.num_queens} queens using Dancing Links")
        
        # Reset queen positions
        self.queen_positions = {}
        
        # Get all cells in the grid
        all_cells = list(self.grid.get_all_cells())
        
        # Shuffle the cells to introduce randomness
        self.rng.shuffle(all_cells)
        
        # Get the range of coordinates
        radius = self.grid.radius
        
        # For a hexagonal grid with radius r, we need to place 2r+1 queens
        # If the user specified a different number, adjust it
        expected_queens = radius * 2 + 1
        if self.num_queens != expected_queens:
            print(f"Warning: For a grid with radius {radius}, we should place {expected_queens} queens, not {self.num_queens}")
            print(f"Adjusting num_queens to {expected_queens}")
            self.num_queens = expected_queens
        
        # Define our primary constraints:
        # 1. Each queen must be placed exactly once
        # 2. Each row (x, y, z coordinate) must have at most one queen
        
        # Create a matrix where:
        # - Each row represents placing a queen at a specific cell
        # - Each column represents a constraint
        
        # First, create a list of all possible rows (queen placements)
        rows = []
        for cell in all_cells:
            # Check if this cell is valid for a queen
            # (not sharing coordinates with existing queens)
            valid = True
            for existing_queen_id, existing_pos in self.queen_positions.items():
                if (cell.x == existing_pos.x or
                    cell.y == existing_pos.y or
                    cell.z == existing_pos.z):
                    valid = False
                    break
            
            if not valid:
                continue
            
            # This cell is valid, add it as a possible queen placement
            rows.append(cell)
        
        # If we don't have enough valid cells, we can't place all queens
        if len(rows) < self.num_queens:
            print(f"Not enough valid cells ({len(rows)}) to place {self.num_queens} queens")
            return False
        
        # Create a binary matrix for the exact cover problem
        # Rows: Each row represents placing a queen at a specific cell
        # Columns:
        # - One column for each queen (to ensure we place exactly N queens)
        # - One column for each x-coordinate (to ensure no two queens share an x-coordinate)
        # - One column for each y-coordinate (to ensure no two queens share a y-coordinate)
        # - One column for each z-coordinate (to ensure no two queens share a z-coordinate)
        
        # Create a set of all x, y, z coordinates used by valid cells
        x_coords = set()
        y_coords = set()
        z_coords = set()
        for cell in rows:
            x_coords.add(cell.x)
            y_coords.add(cell.y)
            z_coords.add(cell.z)
        
        # Create a list of queen IDs and shuffle it to introduce randomness
        queen_ids = list(range(self.num_queens))
        self.rng.shuffle(queen_ids)
        
        # Create column indices
        queen_cols = {queen_id: i for i, queen_id in enumerate(queen_ids)}
        x_cols = list(range(self.num_queens, self.num_queens + len(x_coords)))
        y_cols = list(range(self.num_queens + len(x_coords), self.num_queens + len(x_coords) + len(y_coords)))
        z_cols = list(range(self.num_queens + len(x_coords) + len(y_coords), self.num_queens + len(x_coords) + len(y_coords) + len(z_coords)))
        
        # Create mappings from coordinates to column indices
        x_to_col = {x: self.num_queens + i for i, x in enumerate(sorted(x_coords))}
        y_to_col = {y: self.num_queens + len(x_coords) + i for i, y in enumerate(sorted(y_coords))}
        z_to_col = {z: self.num_queens + len(x_coords) + len(y_coords) + i for i, z in enumerate(sorted(z_coords))}
        
        # Total number of columns
        num_columns = self.num_queens + len(x_coords) + len(y_coords) + len(z_coords)
        
        # Create column names for debugging
        column_names = []
        for queen_id in queen_ids:
            column_names.append(f"Queen_{queen_id}")
        for x in sorted(x_coords):
            column_names.append(f"X={x}")
        for y in sorted(y_coords):
            column_names.append(f"Y={y}")
        for z in sorted(z_coords):
            column_names.append(f"Z={z}")
        
        # Create the Dancing Links matrix
        dlx = DancingLinks(num_columns, column_names)
        
        # Add rows to the matrix
        # Each row represents placing a specific queen at a specific cell
        row_to_queen_and_cell = {}  # Maps row index to (queen_id, cell) tuple
        
        # Generate all possible placements
        row_idx = 0
        for queen_id in queen_ids:
            # Shuffle the rows again for each queen to introduce more randomness
            shuffled_rows = rows.copy()
            self.rng.shuffle(shuffled_rows)
            
            for cell in shuffled_rows:
                # For each row, we add a 1 in the columns for:
                # 1. The queen being placed
                # 2. The x-coordinate being used
                # 3. The y-coordinate being used
                # 4. The z-coordinate being used
                columns = [
                    queen_cols[queen_id],  # Queen constraint
                    x_to_col[cell.x],      # X-coordinate constraint
                    y_to_col[cell.y],      # Y-coordinate constraint
                    z_to_col[cell.z]       # Z-coordinate constraint
                ]
                
                # Add the row to the matrix
                dlx.add_row(row_idx, columns)
                row_to_queen_and_cell[row_idx] = (queen_id, cell)
                row_idx += 1
        
        print(f"Created DLX matrix with {row_idx} rows and {num_columns} columns")
        
        # Define a callback to process the solution
        def solution_callback(solution):
            # Convert solution rows to queen positions
            self.queen_positions = {}
            for row_idx in solution:
                queen_id, cell = row_to_queen_and_cell[row_idx]
                self.queen_positions[queen_id] = cell
            
            # Print the solution for debugging
            print(f"Found solution with {len(self.queen_positions)} queens:")
            for queen_id, pos in sorted(self.queen_positions.items()):
                print(f"  Queen {queen_id}: {pos}")
            
            # Verify the solution
            valid = True
            for queen_id, pos in self.queen_positions.items():
                for other_id, other_pos in self.queen_positions.items():
                    if queen_id != other_id:
                        if (pos.x == other_pos.x or pos.y == other_pos.y or pos.z == other_pos.z):
                            print(f"Invalid solution: Queens at {pos} and {other_pos} can attack each other!")
                            valid = False
                            break
                if not valid:
                    break
            
            if valid:
                print("Solution is valid!")
            else:
                print("Solution is invalid!")
            
            # Only return True if the solution is valid and we have the right number of queens
            return valid and len(self.queen_positions) == self.num_queens
        
        # Search for a solution
        success = dlx.search(0, solution_callback)
        
        if success:
            print(f"Successfully placed {self.num_queens} queens using Dancing Links")
            
            # Update attacked cells for consistency
            self.update_attacked_cells()
            return True
        else:
            print(f"Failed to place queens using Dancing Links")
            return False
    
    def get_queen_positions(self) -> Dict[int, HexCoord]:
        """Get the positions of the queens."""
        return self.queen_positions.copy()