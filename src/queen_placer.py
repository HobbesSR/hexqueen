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
                print(f"Failed at queen {queen_id}/{self.num_queens}: No available cells left")
                if queen_id > 0:
                    print(f"Last queen placed at: {self.queen_positions[queen_id-1]}")
                return False
            
            # Choose a random available cell
            cell = self.rng.choice(available_cells)
            
            # Place the queen
            self.queen_positions[queen_id] = cell
            
            # Update attacked cells
            self.update_attacked_cells()
            
            # Debug: print the number of available cells after each queen placement
            if queen_id < self.num_queens - 1:  # Not the last queen
                cells_left = len(self.get_available_cells())
                total_cells = len(self.grid.get_all_cells())
                print(f"Placed queen {queen_id} at {cell}. Available cells: {cells_left}/{total_cells}")
        
        # Verify queen placement
        for queen_id, pos in self.queen_positions.items():
            for other_id, other_pos in self.queen_positions.items():
                if queen_id != other_id:
                    if pos.x == other_pos.x or pos.y == other_pos.y or pos.z == other_pos.z:
                        print(f"ERROR: Queens at {pos} and {other_pos} can see each other!")
                        return False
        
        print(f"Successfully placed all {self.num_queens} queens randomly")
        return True
    
    def place_queens_backtracking(self) -> bool:
        """
        Place queens using backtracking.
        
        Returns:
            bool: True if all queens were placed successfully, False otherwise
        """
        self.queen_positions = {}
        self.attacked_cells = set()  # Start with no attacked cells
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
        
        # Get cells that are not under attack directly
        # This is more efficient than using get_available_cells() which relies on self.attacked_cells
        available_cells = []
        for cell in self.grid.get_all_cells():
            if not self.is_cell_attacked(cell):
                available_cells.append(cell)
        
        if not available_cells:
            return False
        
        # Shuffle available cells for randomness
        self.rng.shuffle(available_cells)
        
        for cell in available_cells:
            # Save current state of attacked cells
            old_attacked_cells = self.attacked_cells.copy()
            
            # Place the queen
            self.queen_positions[queen_id] = cell
            
            # Update attacked cells
            self.update_attacked_cells()
            
            # Recursively place the next queen
            if self._place_queens_recursive(queen_id + 1):
                return True
            
            # Backtrack - restore previous state
            del self.queen_positions[queen_id]
            self.attacked_cells = old_attacked_cells  # Restore previous attacked cells
        
        return False
    
    def place_queens_set_based(self, max_retries: int = 10) -> bool:
        """
        Place queens using a set-based approach.
        
        This method:
        1. Adds all cells to a set of available cells
        2. Picks a random cell for a queen
        3. Removes that cell and all cells that share a cube coordinate with it
        4. Repeats until all queens are placed or the set is empty
        5. Retries if the set is prematurely empty
        
        Args:
            max_retries: Maximum number of retries if the set becomes empty
            
        Returns:
            bool: True if all queens were placed successfully, False otherwise
        """
        print(f"Attempting set-based placement of {self.num_queens} queens")
        
        for retry in range(max_retries):
            # Reset queen positions
            self.queen_positions = {}
            
            # Start with all cells available
            available_cells = set(self.grid.get_all_cells())
            
            # Try to place each queen
            for queen_id in range(self.num_queens):
                if not available_cells:
                    print(f"Retry {retry+1}/{max_retries}: Set empty after placing {queen_id}/{self.num_queens} queens")
                    break
                
                # Choose a random available cell
                cell = self.rng.choice(list(available_cells))
                
                # Place the queen
                self.queen_positions[queen_id] = cell
                
                # Remove this cell from available cells
                available_cells.remove(cell)
                
                # Remove all cells that share a cube coordinate with this cell
                cells_to_remove = set()
                for available_cell in available_cells:
                    if (available_cell.x == cell.x or
                        available_cell.y == cell.y or
                        available_cell.z == cell.z or
                        available_cell.distance(cell) == 1):  # Also remove adjacent cells
                        cells_to_remove.add(available_cell)
                
                available_cells -= cells_to_remove
                
                # Debug info
                if queen_id < self.num_queens - 1:  # Not the last queen
                    pass
                    #print(f"Placed queen {queen_id} at {cell}. Available cells: {len(available_cells)}")
            
            # Check if we placed all queens
            if len(self.queen_positions) == self.num_queens:
                print(f"Successfully placed all {self.num_queens} queens using set-based approach on retry {retry+1}")
                
                # Verify queen placement
                for queen_id, pos in self.queen_positions.items():
                    for other_id, other_pos in self.queen_positions.items():
                        if queen_id != other_id:
                            if (pos.x == other_pos.x or pos.y == other_pos.y or
                                pos.z == other_pos.z or pos.distance(other_pos) == 1):
                                print(f"ERROR: Queens at {pos} and {other_pos} can attack each other!")
                                return False
                
                # Update attacked cells for consistency
                self.update_attacked_cells()
                return True
        
        print(f"Set-based placement failed after {max_retries} retries")
        return False
    
    def place_queens_row_based(self, max_retries: int = 10) -> bool:
        """
        Place queens using a row-based approach.
        
        This method:
        1. Chooses a dimension (x, y, or z) to iterate across
        2. For each value in that dimension, only picks from cells in that row
        3. Ensures queens are placed on the edges to avoid missing edge queens
        
        Args:
            max_retries: Maximum number of retries if placement fails
            
        Returns:
            bool: True if all queens were placed successfully, False otherwise
        """
        print(f"Attempting row-based placement of {self.num_queens} queens")
        
        # Get the grid radius
        radius = self.grid.radius
        
        # Track edge placement to ensure we have queens on all edges
        edge_dimensions = {'x': False, 'y': False, 'z': False}
        edge_values = {-radius, radius}
        
        for retry in range(max_retries):
            # Reset queen positions
            self.queen_positions = {}
            
            # Start with all cells available
            available_cells = set(self.grid.get_all_cells())
            
            # Choose a dimension to iterate across (x, y, or z)
            dimensions = ['x', 'y', 'z']
            self.rng.shuffle(dimensions)
            chosen_dimension = dimensions[0]
            
            print(f"Retry {retry+1}/{max_retries}: Using dimension {chosen_dimension}")
            
            # Reset edge tracking
            for dim in edge_dimensions:
                edge_dimensions[dim] = False
            
            # Get the range of values for the chosen dimension
            dimension_values = list(range(-radius, radius + 1))
            
            # Prioritize edge values by moving them to the front
            # This ensures we try to place queens on edges first
            for edge_value in edge_values:
                if edge_value in dimension_values:
                    dimension_values.remove(edge_value)
                    dimension_values.insert(0, edge_value)
            
            # Try to place each queen
            queens_placed = 0
            
            # First pass: try to place queens on edges
            for value in dimension_values:
                # Skip if we've placed all queens
                if queens_placed >= self.num_queens:
                    break
                
                # Get cells in this row
                row_cells = []
                for cell in available_cells:
                    cell_value = getattr(cell, chosen_dimension)
                    # Check if this cell is on an edge for any dimension
                    is_edge_cell = (cell.x in edge_values or
                                   cell.y in edge_values or
                                   cell.z in edge_values)
                    
                    if cell_value == value and is_edge_cell:
                        row_cells.append(cell)
                
                if row_cells:
                    # Choose a random cell from this row
                    cell = self.rng.choice(row_cells)
                    
                    # Place the queen
                    self.queen_positions[queens_placed] = cell
                    queens_placed += 1
                    
                    # Mark edge dimensions as covered
                    if cell.x in edge_values:
                        edge_dimensions['x'] = True
                    if cell.y in edge_values:
                        edge_dimensions['y'] = True
                    if cell.z in edge_values:
                        edge_dimensions['z'] = True
                    
                    # Remove this cell from available cells
                    available_cells.remove(cell)
                    
                    # Remove all cells that share a cube coordinate with this cell
                    cells_to_remove = set()
                    for available_cell in available_cells:
                        if (available_cell.x == cell.x or
                            available_cell.y == cell.y or
                            available_cell.z == cell.z or
                            available_cell.distance(cell) == 1):  # Also remove adjacent cells
                            cells_to_remove.add(available_cell)
                    
                    available_cells -= cells_to_remove
            
            # Second pass: place remaining queens in any available cells
            for value in dimension_values:
                # Skip if we've placed all queens
                if queens_placed >= self.num_queens:
                    break
                
                # Get cells in this row
                row_cells = []
                for cell in available_cells:
                    cell_value = getattr(cell, chosen_dimension)
                    if cell_value == value:
                        row_cells.append(cell)
                
                if row_cells:
                    # Choose a random cell from this row
                    cell = self.rng.choice(row_cells)
                    
                    # Place the queen
                    self.queen_positions[queens_placed] = cell
                    queens_placed += 1
                    
                    # Mark edge dimensions as covered
                    if cell.x in edge_values:
                        edge_dimensions['x'] = True
                    if cell.y in edge_values:
                        edge_dimensions['y'] = True
                    if cell.z in edge_values:
                        edge_dimensions['z'] = True
                    
                    # Remove this cell from available cells
                    available_cells.remove(cell)
                    
                    # Remove all cells that share a cube coordinate with this cell
                    cells_to_remove = set()
                    for available_cell in available_cells:
                        if (available_cell.x == cell.x or
                            available_cell.y == cell.y or
                            available_cell.z == cell.z or
                            available_cell.distance(cell) == 1):  # Also remove adjacent cells
                            cells_to_remove.add(available_cell)
                    
                    available_cells -= cells_to_remove
            
            # Check if we placed all queens and covered all edge dimensions
            if queens_placed == self.num_queens and all(edge_dimensions.values()):
                print(f"Successfully placed all {self.num_queens} queens using row-based approach on retry {retry+1}")
                
                # Verify queen placement
                for queen_id, pos in self.queen_positions.items():
                    for other_id, other_pos in self.queen_positions.items():
                        if queen_id != other_id:
                            if (pos.x == other_pos.x or pos.y == other_pos.y or
                                pos.z == other_pos.z or pos.distance(other_pos) == 1):
                                print(f"ERROR: Queens at {pos} and {other_pos} can attack each other!")
                                return False
                
                # Update attacked cells for consistency
                self.update_attacked_cells()
                return True
            elif queens_placed == self.num_queens:
                print(f"Placed all queens but missed some edge dimensions: {edge_dimensions}")
                # Continue to next retry since we didn't cover all edges
        
        print(f"Row-based placement failed after {max_retries} retries")
        return False
    
    def place_queens_row_based_backtracking(self, max_depth: int = 100) -> bool:
        """
        Place queens using a row-based approach with limited backtracking.
        
        This method:
        1. Chooses a dimension (x, y, or z) to iterate across
        2. For each value in that dimension, only picks from cells in that row
        3. Uses backtracking with a depth limit to try different combinations
        4. Ensures queens are placed on the edges to avoid missing edge queens
        
        Args:
            max_depth: Maximum recursion depth for backtracking to prevent infinite loops
            
        Returns:
            bool: True if all queens were placed successfully, False otherwise
        """
        print(f"Attempting row-based backtracking placement of {self.num_queens} queens")
        
        # Get the grid radius
        radius = self.grid.radius
        
        # Track edge placement to ensure we have queens on all edges
        edge_values = {-radius, radius}
        
        # Choose a dimension to iterate across (x, y, or z)
        dimensions = ['x', 'y', 'z']
        self.rng.shuffle(dimensions)
        chosen_dimension = dimensions[0]
        
        print(f"Using dimension {chosen_dimension}")
        
        # Get the range of values for the chosen dimension
        dimension_values = list(range(-radius, radius + 1))
        
        # Prioritize edge values by moving them to the front
        # This ensures we try to place queens on edges first
        for edge_value in edge_values:
            if edge_value in dimension_values:
                dimension_values.remove(edge_value)
                dimension_values.insert(0, edge_value)
        
        # Reset queen positions
        self.queen_positions = {}
        
        # Start the recursive backtracking
        result = self._place_queens_row_based_recursive(0, chosen_dimension, dimension_values, edge_values, max_depth)
        
        if result:
            print(f"Successfully placed all {self.num_queens} queens using row-based backtracking")
            
            # Update attacked cells for consistency
            self.update_attacked_cells()
        else:
            print(f"Row-based backtracking placement failed")
        
        return result
    
    def _place_queens_row_based_recursive(self, queen_id: int, chosen_dimension: str,
                                         dimension_values: list, edge_values: set,
                                         max_depth: int, current_depth: int = 0) -> bool:
        """
        Recursively place queens using row-based backtracking with a depth limit.
        
        Args:
            queen_id: The ID of the queen to place
            chosen_dimension: The dimension to iterate across (x, y, or z)
            dimension_values: The values to iterate over for the chosen dimension
            edge_values: The values that represent edges of the grid
            max_depth: Maximum recursion depth to prevent infinite loops
            current_depth: Current recursion depth
            
        Returns:
            bool: True if the queen and all subsequent queens were placed successfully,
                 False otherwise
        """
        # Base case: all queens placed successfully
        if queen_id == self.num_queens:
            # Check if all edge dimensions are covered
            edge_dimensions = {'x': False, 'y': False, 'z': False}
            
            for pos in self.queen_positions.values():
                if pos.x in edge_values:
                    edge_dimensions['x'] = True
                if pos.y in edge_values:
                    edge_dimensions['y'] = True
                if pos.z in edge_values:
                    edge_dimensions['z'] = True
            
            # Return True only if all edge dimensions are covered
            return all(edge_dimensions.values())
        
        # Check if we've reached the maximum depth
        if current_depth >= max_depth:
            return False
        
        # Try each dimension value
        for value in dimension_values:
            # Get cells in this row that are not under attack
            row_cells = []
            for cell in self.grid.get_all_cells():
                cell_value = getattr(cell, chosen_dimension)
                if cell_value == value and not self.is_cell_attacked(cell):
                    row_cells.append(cell)
            
            # Prioritize edge cells
            edge_cells = []
            non_edge_cells = []
            
            for cell in row_cells:
                if (cell.x in edge_values or cell.y in edge_values or cell.z in edge_values):
                    edge_cells.append(cell)
                else:
                    non_edge_cells.append(cell)
            
            # Shuffle the cells for randomness within each category
            self.rng.shuffle(edge_cells)
            self.rng.shuffle(non_edge_cells)
            
            # Combine edge cells and non-edge cells, with edge cells first
            row_cells = edge_cells + non_edge_cells
            
            # Try each cell in this row
            for cell in row_cells:
                # Place the queen
                self.queen_positions[queen_id] = cell
                
                # Recursively place the next queen
                if self._place_queens_row_based_recursive(queen_id + 1, chosen_dimension,
                                                        dimension_values, edge_values,
                                                        max_depth, current_depth + 1):
                    return True
                
                # Backtrack - remove the queen
                del self.queen_positions[queen_id]
        
        # If we've tried all cells in all rows and couldn't place the queen, return False
        return False
    
    def place_queens(self, max_attempts: int = 100) -> bool:
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
        
        # Try row-based backtracking next
        print("Dancing Links failed, trying row-based backtracking")
        if self.place_queens_row_based_backtracking(max_depth=200):
            return True
        
        # Try regular row-based placement next
        print("Row-based backtracking failed, trying regular row-based placement")
        if self.place_queens_row_based(max_retries=100):
            return True
        
        # Try set-based placement next
        print("Row-based placement failed, trying set-based placement")
        if self.place_queens_set_based(max_retries=100):
            return True
        
        # If set-based placement fails, try random placement
        print("Set-based placement failed, trying random placement")
        for attempt in range(max_attempts):
            if attempt % 10 == 0:
                print(f"Random placement attempt {attempt}/{max_attempts}")
            if self.place_queens_random():
                print(f"Successfully placed queens using random strategy after {attempt+1} attempts")
                return True
        
        print(f"Random placement failed after {max_attempts} attempts, trying backtracking")
        
        # If all else fails, use backtracking
        backtracking_result = self.place_queens_backtracking()
        if backtracking_result:
            print("Successfully placed queens using backtracking strategy")
        else:
            print("Backtracking strategy also failed to place queens")
            print(f"Grid radius: {self.grid.radius}, Number of queens: {self.num_queens}")
        
        return backtracking_result
    
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