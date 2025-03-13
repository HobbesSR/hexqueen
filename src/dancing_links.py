"""
Implementation of Knuth's Algorithm X using Dancing Links (DLX).

This module provides an efficient implementation of Algorithm X
for solving exact cover problems, specifically adapted for
hexagonal grid queen placement.
"""
from typing import List, Dict, Set, Optional, Tuple, Callable


class DancingNode:
    """A node in the Dancing Links matrix."""
    
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self.up = self
        self.down = self
        self.left = self
        self.right = self
        self.column = None


class ColumnNode(DancingNode):
    """A special node that serves as a column header."""
    
    def __init__(self, col: int, name: str):
        super().__init__(-1, col)
        self.name = name
        self.size = 0
        self.column = self


class DancingLinks:
    """
    Implementation of Knuth's Algorithm X using Dancing Links.
    
    This class provides methods to solve exact cover problems efficiently.
    """
    
    def __init__(self, num_columns: int, column_names: List[str] = None):
        """
        Initialize the Dancing Links structure.
        
        Args:
            num_columns: Number of columns in the matrix
            column_names: Optional names for the columns
        """
        # Create the header node
        self.header = ColumnNode(-1, "header")
        
        # Create column nodes
        self.columns = []
        for i in range(num_columns):
            name = column_names[i] if column_names and i < len(column_names) else str(i)
            column = ColumnNode(i, name)
            
            # Link the column to the header row
            column.right = self.header
            column.left = self.header.left
            self.header.left.right = column
            self.header.left = column
            
            self.columns.append(column)
        
        # Initialize solution
        self.solution = []
        self.solution_callback = None
    
    def add_row(self, row_index: int, columns: List[int]) -> None:
        """
        Add a row to the matrix.
        
        Args:
            row_index: Index of the row
            columns: List of column indices where this row has 1s
        """
        if not columns:
            return
        
        # Create nodes for each 1 in the row
        first_node = None
        prev_node = None
        
        for col_index in columns:
            if col_index >= len(self.columns):
                raise ValueError(f"Column index {col_index} out of range")
            
            column = self.columns[col_index]
            node = DancingNode(row_index, col_index)
            node.column = column
            
            # Link the node vertically
            node.up = column.up
            node.down = column
            column.up.down = node
            column.up = node
            
            # Increment column size
            column.size += 1
            
            # Link the node horizontally
            if prev_node:
                node.left = prev_node
                node.right = prev_node.right
                prev_node.right.left = node
                prev_node.right = node
            else:
                first_node = node
                node.left = node
                node.right = node
            
            prev_node = node
    
    def cover_column(self, column: ColumnNode) -> None:
        """
        Cover a column in the matrix.
        
        This removes the column from the header list and removes all rows
        that have a 1 in this column from other columns they have 1s in.
        
        Args:
            column: The column to cover
        """
        # Remove the column from the header list
        column.right.left = column.left
        column.left.right = column.right
        
        # Remove all rows that have a 1 in this column
        i = column.down
        while i != column:
            j = i.right
            while j != i:
                j.down.up = j.up
                j.up.down = j.down
                j.column.size -= 1
                j = j.right
            i = i.down
    
    def uncover_column(self, column: ColumnNode) -> None:
        """
        Uncover a column in the matrix.
        
        This reverses the cover operation, restoring the column and all affected rows.
        
        Args:
            column: The column to uncover
        """
        # Restore all rows that have a 1 in this column
        i = column.up
        while i != column:
            j = i.left
            while j != i:
                j.column.size += 1
                j.down.up = j
                j.up.down = j
                j = j.left
            i = i.up
        
        # Restore the column to the header list
        column.right.left = column
        column.left.right = column
    
    def search(self, k: int, solution_callback: Callable[[List[int]], bool] = None) -> bool:
        """
        Search for a solution using Algorithm X.
        
        Args:
            k: Current depth in the search
            solution_callback: Optional callback function that receives the solution
                               and returns True to continue searching or False to stop
        
        Returns:
            True if a solution was found, False otherwise
        """
        if solution_callback:
            self.solution_callback = solution_callback
        
        # If the matrix is empty, we've found a solution
        if self.header.right == self.header:
            print(f"Found a solution with {len(self.solution)} rows")
            if self.solution_callback:
                return self.solution_callback(self.solution)
            return True
        
        # Choose the column with the fewest 1s (heuristic to minimize branching)
        column = self.choose_column()
        
        if column.size == 0:
            # If the column has no 1s, we can't cover it, so this branch is a dead end
            print(f"Column {column.name} has size 0, backtracking")
            return False
        
        # Cover the chosen column
        self.cover_column(column)
        
        # Try each row in the column
        r = column.down
        while r != column:
            # Add this row to the solution
            self.solution.append(r.row)
            
            # Cover all columns that have 1s in this row
            j = r.right
            while j != r:
                self.cover_column(j.column)
                j = j.right
            
            # Recursively search for the rest of the solution
            if self.search(k + 1):
                return True
            
            # If we get here, we need to backtrack
            # Remove this row from the solution
            self.solution.pop()
            
            # Uncover all columns that have 1s in this row (in reverse order)
            j = r.left
            while j != r:
                self.uncover_column(j.column)
                j = j.left
            
            r = r.down
        
        # Uncover the chosen column
        self.uncover_column(column)
        
        return False
    
    def choose_column(self) -> ColumnNode:
        """
        Choose the column with the fewest 1s.
        
        This is a heuristic to minimize branching in the search.
        With randomization to avoid deterministic solutions.
        
        Returns:
            The chosen column
        """
        min_size = float('inf')
        min_columns = []
        
        j = self.header.right
        while j != self.header:
            if j.size < min_size:
                min_size = j.size
                min_columns = [j]
            elif j.size == min_size:
                min_columns.append(j)
            j = j.right
        
        # If we have multiple columns with the same minimum size,
        # choose one randomly to introduce non-determinism
        if len(min_columns) > 1:
            import random
            return random.choice(min_columns)
        elif min_columns:
            return min_columns[0]
        else:
            return None