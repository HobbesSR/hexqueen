"""
Reverse Engineering Solver for hexagonal grid puzzles.
This module implements a solver that starts from a fully solved board and works backward
to find the minimal set of clues needed for a unique solution.
"""
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import copy
import time
import random
import signal

from .hex_grid import HexGrid, HexCoord
from .solver import PuzzleSolver
from .advanced_solver import AdvancedPuzzleSolver

# Define a timeout handler for long-running operations
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

class ReverseEngineeringSolver:
    """
    A solver that starts from a fully solved board and works backward to find
    the minimal set of clues needed for a unique solution.
    """
    def __init__(self, grid: HexGrid, num_pieces: int, seed: Optional[int] = None):
        """
        Initialize the reverse engineering solver.
        
        Args:
            grid: The hexagonal grid
            num_pieces: Number of pieces/regions
            seed: Random seed for reproducibility
        """
        self.grid = grid
        self.num_pieces = num_pieces
        self.rng = random.Random(seed)
        
        # The complete solution (mapping of cells to regions)
        self.solution = {}  # Maps HexCoord -> region_id
        
        # The piece positions (fixed cells)
        self.piece_positions = {}  # Maps piece_id -> HexCoord
        
        # Additional clues (cells with known region assignments)
        self.fixed_cells = {}  # Maps HexCoord -> region_id
        
        # Metrics for tracking the reverse engineering process
        self.metrics = {
            'initial_clues': 0,
            'final_clues': 0,
            'removed_clues': 0,
            'solver_calls': 0,
            'time_taken': 0
        }
    
    def initialize_from_solution(self, solution: Dict[HexCoord, int], piece_positions: Dict[int, HexCoord]):
        """
        Initialize the solver with a complete solution and piece positions.
        
        Args:
            solution: The complete solution (mapping of cells to regions)
            piece_positions: The piece positions (mapping of piece IDs to positions)
        """
        self.solution = solution.copy()
        self.piece_positions = piece_positions.copy()
        
        # Initially, all cells are fixed (we'll remove them one by one)
        self.fixed_cells = {cell: region_id for cell, region_id in solution.items() 
                           if cell not in piece_positions.values()}
        
        self.metrics['initial_clues'] = len(self.fixed_cells)
    
    def is_uniquely_solvable(self, use_advanced_solver: bool = True, timeout_seconds: int = 5) -> bool:
        """
        Check if the puzzle is uniquely solvable with the current clues.
        
        Args:
            use_advanced_solver: Whether to use the advanced solver
            timeout_seconds: Maximum time to spend checking solvability
            
        Returns:
            bool: True if the puzzle has a unique solution, False otherwise
        """
        self.metrics['solver_calls'] += 1
        
        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            # Create a solver with the current clues
            if use_advanced_solver:
                solver = AdvancedPuzzleSolver(self.grid, self.num_pieces)
            else:
                solver = PuzzleSolver(self.grid, self.num_pieces)
            
            solver.initialize_from_clues(self.piece_positions, self.fixed_cells)
            
            # Count solutions
            solution_count = solver.count_solutions(2)
            
            # Disable the alarm
            signal.alarm(0)
            
            return solution_count == 1
        except TimeoutException:
            # If we timeout, assume the puzzle is too complex and keep the clue
            signal.alarm(0)  # Disable the alarm
            return False
        except Exception as e:
            # If any other error occurs, disable the alarm and re-raise
            signal.alarm(0)
            raise e
    
    def is_logically_solvable(self, use_advanced_solver: bool = True, timeout_seconds: int = 5) -> bool:
        """
        Check if the puzzle is solvable using only logical techniques.
        
        Args:
            use_advanced_solver: Whether to use the advanced solver
            timeout_seconds: Maximum time to spend checking solvability
            
        Returns:
            bool: True if the puzzle is logically solvable, False otherwise
        """
        self.metrics['solver_calls'] += 1
        
        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            # Create a solver with the current clues
            if use_advanced_solver:
                solver = AdvancedPuzzleSolver(self.grid, self.num_pieces)
            else:
                solver = PuzzleSolver(self.grid, self.num_pieces)
            
            solver.initialize_from_clues(self.piece_positions, self.fixed_cells)
            
            # Apply logical techniques
            solver.apply_deduction_techniques()
            
            # Check if the puzzle is solved
            result = solver.is_solved()
            
            # Disable the alarm
            signal.alarm(0)
            
            return result
        except TimeoutException:
            # If we timeout, assume the puzzle is too complex and keep the clue
            signal.alarm(0)  # Disable the alarm
            return False
        except Exception as e:
            # If any other error occurs, disable the alarm and re-raise
            signal.alarm(0)
            raise e
    
    def find_minimal_clues(self, ensure_logical: bool = False, use_advanced_solver: bool = True,
                          max_cells: int = 30, total_timeout: int = 60) -> Dict[HexCoord, int]:
        """
        Find the minimal set of clues needed for a unique solution.
        
        Args:
            ensure_logical: Whether to ensure the puzzle is solvable using only logical techniques
            use_advanced_solver: Whether to use the advanced solver
            max_cells: Maximum number of cells to try removing
            total_timeout: Maximum total time in seconds for the entire operation
            
        Returns:
            Dict[HexCoord, int]: The minimal set of fixed cells (clues)
        """
        start_time = time.time()
        
        # Start with all cells fixed
        self.fixed_cells = {cell: region_id for cell, region_id in self.solution.items()
                           if cell not in self.piece_positions.values()}
        
        self.metrics['initial_clues'] = len(self.fixed_cells)
        
        # Try removing clues one by one
        cells_to_try = list(self.fixed_cells.keys())
        self.rng.shuffle(cells_to_try)  # Randomize the order
        
        # Limit the number of cells to try to avoid exponential complexity
        max_cells_to_try = min(len(cells_to_try), max_cells)
        cells_to_try = cells_to_try[:max_cells_to_try]
        
        # Set up global timeout
        global_timeout = start_time + total_timeout
        
        for cell in cells_to_try:
            # Check if we've exceeded the global timeout
            if time.time() > global_timeout:
                break
                
            # Temporarily remove this clue
            region_id = self.fixed_cells.pop(cell)
            
            # Check if the puzzle is still uniquely solvable
            still_unique = self.is_uniquely_solvable(use_advanced_solver)
            
            # If ensuring logical solvability, also check that
            still_logical = True
            if ensure_logical and still_unique:
                still_logical = self.is_logically_solvable(use_advanced_solver)
            
            # If removing this clue breaks uniqueness or logical solvability, put it back
            if not still_unique or (ensure_logical and not still_logical):
                self.fixed_cells[cell] = region_id
        
        self.metrics['final_clues'] = len(self.fixed_cells)
        self.metrics['removed_clues'] = self.metrics['initial_clues'] - self.metrics['final_clues']
        self.metrics['time_taken'] = time.time() - start_time
        
        return self.fixed_cells
    
    def find_minimal_clues_by_importance(self, ensure_logical: bool = False, use_advanced_solver: bool = True,
                                        max_cells: int = 30, total_timeout: int = 60) -> Dict[HexCoord, int]:
        """
        Find the minimal set of clues needed for a unique solution, prioritizing by importance.
        This method uses a more sophisticated approach that tries to identify critical cells first.
        
        Args:
            ensure_logical: Whether to ensure the puzzle is solvable using only logical techniques
            use_advanced_solver: Whether to use the advanced solver
            max_cells: Maximum number of cells to try removing
            total_timeout: Maximum total time in seconds for the entire operation
            
        Returns:
            Dict[HexCoord, int]: The minimal set of fixed cells (clues)
        """
        start_time = time.time()
        
        # Start with all cells fixed
        self.fixed_cells = {cell: region_id for cell, region_id in self.solution.items()
                           if cell not in self.piece_positions.values()}
        
        self.metrics['initial_clues'] = len(self.fixed_cells)
        
        # Calculate cell importance based on connectivity and region boundaries
        cell_importance = self._calculate_cell_importance()
        
        # Sort cells by importance (least important first)
        cells_to_try = sorted(self.fixed_cells.keys(), key=lambda c: cell_importance.get(c, 0))
        
        # Limit the number of cells to try to avoid exponential complexity
        max_cells_to_try = min(len(cells_to_try), max_cells)
        cells_to_try = cells_to_try[:max_cells_to_try]
        
        # Set up global timeout
        global_timeout = start_time + total_timeout
        
        for cell in cells_to_try:
            # Check if we've exceeded the global timeout
            if time.time() > global_timeout:
                break
                
            # Temporarily remove this clue
            region_id = self.fixed_cells.pop(cell)
            
            # Check if the puzzle is still uniquely solvable
            still_unique = self.is_uniquely_solvable(use_advanced_solver)
            
            # If ensuring logical solvability, also check that
            still_logical = True
            if ensure_logical and still_unique:
                still_logical = self.is_logically_solvable(use_advanced_solver)
            
            # If removing this clue breaks uniqueness or logical solvability, put it back
            if not still_unique or (ensure_logical and not still_logical):
                self.fixed_cells[cell] = region_id
        
        self.metrics['final_clues'] = len(self.fixed_cells)
        self.metrics['removed_clues'] = self.metrics['initial_clues'] - self.metrics['final_clues']
        self.metrics['time_taken'] = time.time() - start_time
        
        return self.fixed_cells
    
    def _calculate_cell_importance(self) -> Dict[HexCoord, float]:
        """
        Calculate the importance of each cell based on connectivity and region boundaries.
        
        Returns:
            Dict[HexCoord, float]: Mapping of cells to their importance scores
        """
        importance = {}
        
        # Group cells by region
        regions = defaultdict(set)
        for cell, region_id in self.solution.items():
            regions[region_id].add(cell)
        
        # For each cell, calculate its importance
        for cell, region_id in self.solution.items():
            if cell in self.piece_positions.values():
                # Piece positions are fixed and have maximum importance
                importance[cell] = float('inf')
                continue
            
            # Initialize importance score
            score = 0
            
            # Factor 1: Is this cell on a region boundary?
            is_boundary = False
            for neighbor in self.grid.get_neighbors(cell):
                if neighbor in self.solution and self.solution[neighbor] != region_id:
                    is_boundary = True
                    score += 1  # Increase score for each different neighboring region
            
            # Factor 2: Is this cell a critical connection point for its region?
            # Only check for critical connection points if the cell is on a boundary
            # and the region has more than a few cells (optimization)
            if is_boundary and len(regions[region_id]) > 3:
                # Use a simpler heuristic to estimate if this might be a critical connection
                # Count how many region neighbors this cell has
                region_neighbors = sum(1 for neighbor in self.grid.get_neighbors(cell)
                                     if neighbor in self.solution and self.solution[neighbor] == region_id)
                
                # If this cell has region neighbors in different directions, it might be critical
                if region_neighbors >= 2:
                    score += 3  # Potentially critical connection points are important
            
            # Factor 3: Distance from piece position
            piece_pos = self.piece_positions.get(region_id)
            if piece_pos:
                distance = self.grid.get_distance(cell, piece_pos)
                score += distance * 0.5  # Cells farther from the piece are more important
            
            importance[cell] = score
        
        return importance
    
    def _is_region_contiguous(self, cells: Set[HexCoord]) -> bool:
        """
        Check if a set of cells forms a contiguous region.
        
        Args:
            cells: Set of cells to check
            
        Returns:
            bool: True if the cells form a contiguous region, False otherwise
        """
        if not cells:
            return True
        
        # Start BFS from any cell
        start = next(iter(cells))
        visited = {start}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            for neighbor in self.grid.get_neighbors(current):
                if neighbor in cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # If all cells are visited, the region is contiguous
        return len(visited) == len(cells)
    
    def generate_challenging_puzzle(self, ensure_logical: bool = True, use_advanced_solver: bool = True,
                                   max_cells: int = 30, total_timeout: int = 60) -> Tuple[Dict[int, HexCoord], Dict[HexCoord, int]]:
        """
        Generate a challenging puzzle by finding the minimal set of clues needed for a unique solution.
        
        Args:
            ensure_logical: Whether to ensure the puzzle is solvable using only logical techniques
            use_advanced_solver: Whether to use the advanced solver
            max_cells: Maximum number of cells to try removing
            total_timeout: Maximum total time in seconds for the entire operation
            
        Returns:
            Tuple[Dict[int, HexCoord], Dict[HexCoord, int]]: The piece positions and fixed cells (clues)
        """
        # Find minimal clues using the importance-based approach
        fixed_cells = self.find_minimal_clues_by_importance(
            ensure_logical,
            use_advanced_solver,
            max_cells,
            total_timeout
        )
        
        return self.piece_positions, fixed_cells
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get solver metrics."""
        return self.metrics