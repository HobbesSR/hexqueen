"""
Solver for hexagonal grid puzzles with logical techniques and recursive solving.
"""
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import copy
import time

from .hex_grid import HexGrid, HexCoord
from .puzzle_generator import PuzzleGenerator

class PuzzleSolver:
    """
    Solver for hexagonal grid puzzles using logical techniques and recursion.
    This solver now supports an option to solve puzzles using only logical techniques,
    without recursing. Set the logic_only flag in the solve() method to enforce this.
    """
    def __init__(self, grid: HexGrid, num_regions: int):
        """
        Initialize the puzzle solver.
        
        Args:
            grid: The hexagonal grid
            num_regions: Number of pieces/regions
        """
        self.grid = grid
        self.num_regions = num_regions
        
        # Solver state
        self.cell_candidates = {}  # Maps HexCoord -> set of possible region IDs
        self.assigned_cells = {}   # Maps HexCoord -> assigned region ID
        self.region_cells = defaultdict(set)  # Maps region_id -> set of assigned cells
        
        # Piece positions (fixed cells)
        self.piece_positions = {}  # Maps piece_id -> HexCoord
        
        # Memoization for recursive solver
        self.memo = {}
        self.solution_count = 0
        self.solution = None
        
        # Performance metrics
        self.metrics = {
            'naked_singles': 0,
            'hidden_singles': 0,
            'hidden_pairs': 0,
            'region_contiguity': 0,
            'recursive_calls': 0,
            'memo_hits': 0,
            'time_taken': 0
        }
        
        # New flags to control solving behavior
        self.use_recursion = True
        self.recursion_used = False

    def initialize_from_generator(self, generator: PuzzleGenerator):
        """
        Initialize the solver state from a puzzle generator.
        
        Args:
            generator: The puzzle generator with a generated puzzle
        """
        self.piece_positions = generator.piece_positions.copy()
        
        # Initialize all cells with all possible candidates
        all_regions = set(range(self.num_regions))
        for cell in self.grid.get_all_cells():
            self.cell_candidates[cell] = all_regions.copy()
        
        # Set piece positions as fixed
        for piece_id, pos in self.piece_positions.items():
            self.assign_cell(pos, piece_id)
    
    def initialize_from_clues(self, piece_positions: Dict[int, HexCoord], fixed_cells: Dict[HexCoord, int] = None):
        """
        Initialize the solver state from clues.
        
        Args:
            piece_positions: Mapping of piece IDs to their positions
            fixed_cells: Additional fixed cells (optional)
        """
        self.piece_positions = piece_positions.copy()
        
        # Initialize all cells with all possible candidates
        all_regions = set(range(self.num_regions))
        for cell in self.grid.get_all_cells():
            self.cell_candidates[cell] = all_regions.copy()
        
        # Set piece positions as fixed
        for piece_id, pos in self.piece_positions.items():
            self.assign_cell(pos, piece_id)
        
        # Set additional fixed cells
        if fixed_cells:
            for cell, region_id in fixed_cells.items():
                self.assign_cell(cell, region_id)
    
    def assign_cell(self, cell: HexCoord, region_id: int) -> bool:
        """
        Assign a cell to a region and update candidates.
        
        Args:
            cell: The cell to assign
            region_id: The region ID to assign to the cell
            
        Returns:
            bool: True if assignment was successful, False if it leads to a contradiction
        """
        if cell in self.assigned_cells:
            # Cell already assigned
            return self.assigned_cells[cell] == region_id
        
        if region_id not in self.cell_candidates[cell]:
            # Region not in candidates
            return False
        
        # Assign the cell
        self.assigned_cells[cell] = region_id
        self.region_cells[region_id].add(cell)
        
        # Update candidates
        self.cell_candidates[cell] = {region_id}
        
        # Remove this region from candidates of cells that would break contiguity
        if not self.update_contiguity_constraints(cell, region_id):
            return False
        
        return True
    
    def update_contiguity_constraints(self, cell: HexCoord, region_id: int) -> bool:
        """
        Update candidates based on contiguity constraints after assigning a cell.
        
        Args:
            cell: The newly assigned cell
            region_id: The region ID assigned to the cell
            
        Returns:
            bool: True if constraints were applied successfully, False if contradiction
        """
        # For each region, ensure it can still form a contiguous area
        for other_region in range(self.num_regions):
            if other_region == region_id:
                continue
            
            # Check if assigning this cell would isolate parts of other regions
            if not self.check_region_contiguity(other_region, cell):
                return False
        
        return True
    
    def check_region_contiguity(self, region_id: int, excluded_cell: HexCoord) -> bool:
        """
        Check if a region can still be contiguous after excluding a cell.
        
        Args:
            region_id: The region ID to check
            excluded_cell: The cell to exclude (newly assigned to another region)
            
        Returns:
            bool: True if the region can still be contiguous, False otherwise
        """
        # Get cells already assigned to this region
        assigned = self.region_cells[region_id]
        if not assigned:
            return True  # No cells assigned yet, trivially contiguous
        
        # If only one cell is assigned, it's also trivially contiguous
        if len(assigned) == 1:
            return True
        
        # Get cells that could be part of this region (candidates)
        potential_cells = {c for c, candidates in self.cell_candidates.items()
                          if region_id in candidates and c != excluded_cell and c not in assigned}
        
        # If no potential cells and more than one assigned cell,
        # we need to check if assigned cells themselves form a contiguous region
        if not potential_cells:
            # Use BFS to check if all assigned cells are connected
            start = next(iter(assigned)) # Start BFS from any assigned cell
            visited = {start}
            queue = deque([start])
            
            while queue:
                current = queue.popleft()
                for neighbor in self.grid.get_neighbors(current):
                    if neighbor in assigned and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            # If not all assigned cells are visited, the region is not contiguous
            return len(visited) == len(assigned)
        
        # For regions with potential cells, we need to check if all assigned cells
        # can be connected through the potential cells
        
        # Create a graph including assigned and potential cells for contiguity check
        graph = {}
        for cell in assigned | potential_cells:
            graph[cell] = []
            for neighbor in self.grid.get_neighbors(cell):
                if (neighbor in assigned or neighbor in potential_cells) and neighbor != excluded_cell:
                    graph[cell].append(neighbor)
        
        # Use BFS to check connectivity in the graph
        start = next(iter(assigned)) # Start BFS from any assigned cell
        visited = {start}
        queue = deque([start])
        visited_assigned = {start} # Track visited assigned cells
        
        while queue:
            current = queue.popleft()
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    if neighbor in assigned:
                        visited_assigned.add(neighbor)
        
        # Check if all assigned cells are reachable
        return len(visited_assigned) == len(assigned)
    
    def apply_naked_singles_technique(self) -> bool:
        """
        Apply the naked singles technique: if a cell has only one candidate, assign it.
        
        Returns:
            bool: True if any assignments were made, False otherwise
        """
        made_progress = False
        
        for cell, candidates in list(self.cell_candidates.items()):
            if cell in self.assigned_cells:
                continue
            
            if len(candidates) == 1:
                region_id = next(iter(candidates))
                if self.assign_cell(cell, region_id):
                    made_progress = True
                    self.metrics['naked_singles'] += 1
                else:
                    # Contradiction found
                    return False
        
        return made_progress
    
    def apply_hidden_singles_technique(self) -> bool:
        """
        Apply the hidden singles technique: if a region can only go in one cell in a local area,
        assign that cell to the region.
        
        Returns:
            bool: True if any assignments were made, False otherwise
        """
        made_progress = False
        
        # For each unassigned cell
        for cell in list(self.cell_candidates.keys()):
            if cell in self.assigned_cells:
                continue
            
            # Get neighbors
            neighbors = self.grid.get_neighbors(cell)
            
            # For each candidate in this cell
            for region_id in list(self.cell_candidates[cell]):
                # Check if this is the only cell in the neighborhood that can have this region
                only_possible = True
                for neighbor in neighbors:
                    if (neighbor not in self.assigned_cells and 
                        region_id in self.cell_candidates[neighbor]):
                        only_possible = False
                        break
                
                if only_possible:
                    if self.assign_cell(cell, region_id):
                        made_progress = True
                        self.metrics['hidden_singles'] += 1
                    else:
                        # Contradiction found
                        return False
        
        return made_progress
    
    def apply_hidden_pairs_technique(self) -> bool:
        """
        Apply the hidden pairs technique: if two cells in a local area can only have the same
        two regions, those regions must be in those cells.
        
        Returns:
            bool: True if any candidates were eliminated, False otherwise
        """
        made_progress = False
        
        # For each unassigned cell
        for cell in list(self.cell_candidates.keys()):
            if cell in self.assigned_cells or len(self.cell_candidates[cell]) <= 2:
                continue
            
            # Get neighbors
            neighbors = [n for n in self.grid.get_neighbors(cell) 
                        if n not in self.assigned_cells]
            
            # For each neighbor
            for neighbor in neighbors:
                if len(self.cell_candidates[neighbor]) <= 2:
                    continue
                
                # Find common candidates
                common_candidates = self.cell_candidates[cell] & self.cell_candidates[neighbor]
                if len(common_candidates) != 2:
                    continue
                
                # Check if these candidates only appear in these two cells in the local area
                local_area = set(self.grid.get_neighbors(cell) + self.grid.get_neighbors(neighbor))
                local_area = {c for c in local_area if c not in self.assigned_cells and c != cell and c != neighbor}
                
                exclusive = True
                for other_cell in local_area:
                    if any(region_id in self.cell_candidates[other_cell] for region_id in common_candidates):
                        exclusive = False
                        break
                
                if exclusive:
                    # These two regions must be in these two cells
                    old_candidates_cell = self.cell_candidates[cell].copy()
                    old_candidates_neighbor = self.cell_candidates[neighbor].copy()
                    
                    self.cell_candidates[cell] = common_candidates.copy()
                    self.cell_candidates[neighbor] = common_candidates.copy()
                    
                    if (old_candidates_cell != self.cell_candidates[cell] or 
                        old_candidates_neighbor != self.cell_candidates[neighbor]):
                        made_progress = True
                        self.metrics['hidden_pairs'] += 1
        
        return made_progress
    
    def apply_region_contiguity_technique(self) -> bool:
        """
        Apply the region contiguity technique: eliminate candidates that would break region contiguity.
        
        Returns:
            bool: True if any candidates were eliminated, False otherwise
        """
        made_progress = False
        
        # For each region
        for region_id in range(self.num_regions):
            # Get cells already assigned to this region
            assigned = self.region_cells[region_id]
            if len(assigned) <= 1:
                continue  # Skip regions with 0 or 1 cells (trivially contiguous)
            
            # For each unassigned cell
            for cell in list(self.cell_candidates.keys()):
                if cell in self.assigned_cells:
                    continue
                
                # If this cell is a candidate for this region
                if region_id in self.cell_candidates[cell]:
                    # Check if assigning this cell to another region would break contiguity
                    # by creating isolated cells in the current region
                    
                    # Temporarily remove this cell from candidates for this region
                    old_candidates = self.cell_candidates[cell].copy()
                    self.cell_candidates[cell] = self.cell_candidates[cell] - {region_id}
                    
                    # Check if the region can still be contiguous without this cell
                    if not self.check_region_contiguity(region_id, cell):
                        # If not, this cell must be part of this region
                        if self.assign_cell(cell, region_id):
                            made_progress = True
                            self.metrics['region_contiguity'] += 1
                        else:
                            # Contradiction found
                            return False
                    else:
                        # Restore candidates
                        self.cell_candidates[cell] = old_candidates
        
        return made_progress
    
    def apply_deduction_techniques(self) -> bool:
        """
        Apply all deduction techniques until no more progress is made.
        
        Returns:
            bool: True if the puzzle is still valid, False if contradiction found
        """
        while True:
            progress = False
            
            # Naked Singles: If a cell has only one candidate, assign it.
            result = self.apply_naked_singles_technique()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            # Hidden Singles: If a region can only go in one cell in a local area, assign it.
            result = self.apply_hidden_singles_technique()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            # Hidden Pairs: If two cells in a local area can only have the same two regions, assign them.
            result = self.apply_hidden_pairs_technique()
            progress = progress or result
            
            # Region Contiguity: Eliminate candidates that would break region contiguity.
            result = self.apply_region_contiguity_technique()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            if not progress:
                break
        
        return True
    
    def is_solved(self) -> bool:
        """Check if the puzzle is solved."""
        return len(self.assigned_cells) == len(self.grid.get_all_cells())
    
    def get_next_cell(self) -> Optional[HexCoord]:
        """Get the next cell to try in the recursive solver (minimum remaining values)."""
        min_candidates = float('inf')
        best_cell = None
        
        for cell, candidates in self.cell_candidates.items():
            if cell in self.assigned_cells:
                continue
            
            if 1 < len(candidates) < min_candidates:
                min_candidates = len(candidates)
                best_cell = cell
        
        return best_cell
    
    def get_state_key(self) -> Tuple:
        """Get a hashable key representing the current state for memoization."""
        # Sort to ensure consistent ordering
        assigned = tuple(sorted((cell.x, cell.y, cell.z, region_id) 
                               for cell, region_id in self.assigned_cells.items()))
        return assigned
    
    def recursive_solver(self) -> bool:
        """
        Solve the puzzle using recursive backtracking with memoization.
        
        Returns:
            bool: True if a solution was found, False otherwise
        """
        self.metrics['recursive_calls'] += 1
        
        # Check memoization
        state_key = self.get_state_key()
        if state_key in self.memo:
            self.metrics['memo_hits'] += 1
            return self.memo[state_key]
        
        # Apply logical techniques
        if not self.apply_deduction_techniques():
            self.memo[state_key] = False
            return False
        
        # Check if solved
        if self.is_solved():
            self.solution = copy.deepcopy(self.assigned_cells)
            self.solution_count += 1
            self.memo[state_key] = True
            return True
        
        # Get next cell to try
        cell = self.get_next_cell()
        if not cell:
            self.memo[state_key] = False
            return False
        
        # Try each candidate, starting with the most promising ones
        # (those that have the most cells already assigned to that region)
        candidates = list(self.cell_candidates[cell])
        candidates.sort(key=lambda r: len(self.region_cells[r]), reverse=True)
        
        for region_id in candidates:
            # Skip if this region already has enough cells
            # (this helps balance region sizes)
            total_cells = len(self.grid.get_all_cells())
            expected_size = total_cells // self.num_regions
            # Use a more relaxed constraint to avoid pruning valid solutions
            if len(self.region_cells[region_id]) > expected_size * 2.0:
                continue
            
            # Save state
            saved_assigned = self.assigned_cells.copy()
            saved_region_cells = copy.deepcopy(self.region_cells)
            saved_candidates = copy.deepcopy(self.cell_candidates)
            
            # Try assignment
            if self.assign_cell(cell, region_id):
                if self.recursive_solver():
                    return True
            
            # Restore state
            self.assigned_cells = saved_assigned
            self.region_cells = saved_region_cells
            self.cell_candidates = saved_candidates
        
        # No solution found
        self.memo[state_key] = False
        return False
    
    def solve(self, logic_only: bool = False) -> bool:
        """
        Solve the puzzle using logical techniques and recursive backtracking if needed.
        
        Args:
            logic_only: If True, only apply logical techniques without recursion.
        
        Returns:
            bool: True if a solution was found, False otherwise
        """
        start_time = time.time()
        
        # Reset metrics
        self.metrics = {
            'naked_singles': 0,
            'hidden_singles': 0,
            'hidden_pairs': 0,
            'region_contiguity': 0,
            'recursive_calls': 0,
            'memo_hits': 0,
            'time_taken': 0
        }
        
        # Reset solution
        self.solution = None
        self.solution_count = 0
        self.memo = {}
        self.recursion_used = False
        
        try:
            # Apply deduction techniques first
            self.apply_deduction_techniques()
            
            # Check if solved by logic alone
            if self.is_solved():
                self.solution = self.assigned_cells.copy()
                self.solution_count = 1
                self.metrics['time_taken'] = time.time() - start_time
                return True
            
            # If only logical techniques are allowed, return failure
            if logic_only:
                self.metrics['time_taken'] = time.time() - start_time
                return False
            
            # Use recursive solver
            self.recursion_used = True
            result = self.recursive_solver()
            self.metrics['time_taken'] = time.time() - start_time
            return result
        except Exception as e:
            print(f"Error during solving: {e}")
            self.metrics['time_taken'] = time.time() - start_time
            return False
    
    def count_solutions(self, limit: int = 2) -> int:
        """
        Count the number of solutions up to a limit.
        
        Args:
            limit: Maximum number of solutions to find
            
        Returns:
            int: Number of solutions found (up to limit)
        """
        start_time = time.time()
        
        # Reset metrics
        self.metrics = {
            'naked_singles': 0,
            'hidden_singles': 0,
            'hidden_pairs': 0,
            'region_contiguity': 0,
            'recursive_calls': 0,
            'memo_hits': 0,
            'time_taken': 0
        }
        
        # Reset solution
        self.solution_count = 0
        self.memo = {}
        
        # Apply deduction techniques first
        if not self.apply_deduction_techniques():
            self.metrics['time_taken'] = time.time() - start_time
            return 0
        
        # Check if solved by logic alone
        if self.is_solved():
            self.solution_count = 1
            self.metrics['time_taken'] = time.time() - start_time
            return 1
        
        # Use recursive counting
        self._count_solutions_recursive(limit)
        self.metrics['time_taken'] = time.time() - start_time
        return self.solution_count
    
    def _count_solutions_recursive(self, limit: int) -> bool:
        """
        Recursively count solutions up to a limit.
        
        Args:
            limit: Maximum number of solutions to find
            
        Returns:
            bool: True if limit reached, False otherwise
        """
        self.metrics['recursive_calls'] += 1
        
        # Apply deduction techniques
        if not self.apply_deduction_techniques():
            return False
        
        # Check if solved
        if self.is_solved():
            self.solution_count += 1
            return self.solution_count >= limit
        
        # Get next cell to try
        cell = self.get_next_cell()
        if not cell:
            return False
        
        # Try each candidate
        candidates = list(self.cell_candidates[cell])
        for region_id in candidates:
            # Save state
            saved_assigned = self.assigned_cells.copy()
            saved_region_cells = copy.deepcopy(self.region_cells)
            saved_candidates = copy.deepcopy(self.cell_candidates)
            
            # Try assignment
            if self.assign_cell(cell, region_id):
                if self._count_solutions_recursive(limit):
                    return True
            
            # Restore state
            self.assigned_cells = saved_assigned
            self.region_cells = saved_region_cells
            self.cell_candidates = saved_candidates
        
        return False
    
    def get_solution(self) -> Dict[HexCoord, int]:
        """Get the solution if one was found."""
        return self.solution
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get solver metrics."""
        return self.metrics