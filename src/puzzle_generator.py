"""
Puzzle generator for creating hexagonal grid puzzles with region expansion.
"""
import random
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from .hex_grid import HexGrid, HexCoord

class PuzzleGenerator:
    """
    Generates puzzles on a hexagonal grid by creating and growing regions.
    """
    def __init__(self, grid: HexGrid, num_pieces: int, seed: Optional[int] = None):
        """
        Initialize the puzzle generator.
        
        Args:
            grid: The hexagonal grid to use
            num_regions: Number of pieces/regions to create
            seed: Random seed for reproducibility
        """
        self.grid = grid
        self.num_regions = num_pieces
        self.rng = random.Random(seed)
        self.debug = True
        
        
        # Puzzle state
        self.region_seeds = {}  # Maps region_id -> HexCoord
        self.cell_regions = {}     # Maps HexCoord -> region_id
        self.regions = defaultdict(set)  # Maps region_id -> set of HexCoord
        self.region_frontiers = defaultdict(set)  # Maps region_id -> frontier cells
        # Tracking for puzzle generation
        self.max_retries = 100
        self.retry_count = 0
    
    def reset(self):
        """Reset the puzzle state."""
        self.region_seeds = {}
        self.cell_regions = {}
        self.regions = defaultdict(set)
        self.region_frontiers = defaultdict(set)
        self.retry_count = 0
    
    def place_pieces(self) -> bool:
        """
        Place pieces randomly on the grid.
        
        Returns:
            bool: True if pieces were placed successfully, False otherwise
        """
        self.reset()
        all_cells = list(self.grid.get_all_cells())
        
        # Shuffle cells for random placement
        self.rng.shuffle(all_cells)
        
        # Place pieces with minimum distance between them
        min_distance = max(1, self.grid.radius // (self.num_pieces ** 0.5))
        placed_pieces = []
        
        for cell in all_cells:
            # Check if this cell is far enough from existing pieces
            if all(self.grid.get_distance(cell, pos) >= min_distance for pos in placed_pieces):
                piece_id = len(placed_pieces)
                self.region_seeds[piece_id] = cell
                placed_pieces.append(cell)
                
                # Initialize region with the piece's cell
                self.regions[piece_id].add(cell)
                self.cell_regions[cell] = piece_id
                
                # Add neighbors to frontier
                for neighbor in self.grid.get_neighbors(cell):
                    if neighbor not in self.cell_regions:
                        self.region_frontiers[piece_id].add(neighbor)
                
                # Check if we've placed all pieces
                if len(placed_pieces) == self.num_pieces:
                    return True
        
        # If we get here, we couldn't place all pieces
        return False
    
    def grow_regions(self) -> bool:
        """
        Grow regions until the entire board is covered.
        
        Returns:
            bool: True if regions were grown successfully, False otherwise
        """
        # Continue until all cells are assigned to a region
        while len(self.cell_regions) < len(self.grid.get_all_cells()):
            # If any region has no frontier, the puzzle can't be completed
            if any(not frontier for frontier in self.region_frontiers.values()):
                return False
            
            # Choose a random region to grow
            active_regions = [r for r, f in self.region_frontiers.items() if f]
            if not active_regions:
                return False
            
            region_id = self.rng.choice(active_regions)
            frontier = list(self.region_frontiers[region_id])
            
            # Choose a random frontier cell
            if not frontier:
                return False
            
            cell = self.rng.choice(frontier)
            
            # Add the cell to the region
            self.regions[region_id].add(cell)
            self.cell_regions[cell] = region_id
            self.region_frontiers[region_id].remove(cell)
            
            # Update frontiers
            for neighbor in self.grid.get_neighbors(cell):
                if neighbor not in self.cell_regions:
                    self.region_frontiers[region_id].add(neighbor)
                elif self.cell_regions[neighbor] != region_id:
                    # If neighbor belongs to another region, ensure it's not in our frontier
                    if neighbor in self.region_frontiers[region_id]:
                        self.region_frontiers[region_id].remove(neighbor)
        
        return True
    
    def is_region_contiguous(self, region_id: int) -> bool:
        """
        Check if a region is contiguous.
        
        Args:
            region_id: The ID of the region to check
            
        Returns:
            bool: True if the region is contiguous, False otherwise
        """
        region_cells = self.regions[region_id]
        if not region_cells:
            return True
        
        # Start BFS from the region seed
        start = self.region_seeds[region_id]
        visited = {start}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            for neighbor in self.grid.get_neighbors(current):
                if neighbor in region_cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # If all cells are visited, the region is contiguous
        return len(visited) == len(region_cells)
    
    def are_all_regions_contiguous(self) -> bool:
        """Check if all regions are contiguous."""
        return all(self.is_region_contiguous(region_id) for region_id in range(self.num_pieces))
    
    def check_puzzle_properties(self) -> Tuple[bool, bool]:
        """
        Check if the puzzle has a unique solution and is logically solvable.
        
        Returns:
            Tuple[bool, bool]: (is_unique, is_logically_solvable)
        """
        from .solver import PuzzleSolver
        
        # Create a solver with only piece positions as clues
        solver = PuzzleSolver(self.grid, self.num_regions)
        solver.initialize_from_clues(self.region_seeds)
        
        # Check for uniqueness
        solution_count = solver.count_solutions(2)
        is_unique = solution_count == 1
        
        # Check for logical solvability
        # Create a new solver instance to ensure clean state
        logical_solver = PuzzleSolver(self.grid, self.num_regions)
        logical_solver.initialize_from_clues(self.region_seeds)
        
        # Apply only logical techniques
        logical_solver.apply_deduction_techniques()
        
        # Check if the puzzle is solved using only logical techniques
        is_logically_solvable = logical_solver.is_solved()
        
        return is_unique, is_logically_solvable
    
    def generate_puzzle(self, ensure_unique: bool = True, ensure_logical: bool = True) -> Optional['HexQueenPuzzle']:
        """
        Generate a complete puzzle and return a HexQueenPuzzle object.
        
        Args:
            ensure_unique: Whether to ensure the puzzle has a unique solution
            ensure_logical: Whether to ensure the puzzle is solvable using only logical techniques
            
        Returns:
            Optional[HexQueenPuzzle]: HexQueenPuzzle object if puzzle generation is successful, None otherwise
        """
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            if not self.place_pieces():
                self.retry_count += 1
                continue
            
            if not self.grow_regions():
                self.retry_count += 1
                continue
            
            if not self.are_all_regions_contiguous():
                self.retry_count += 1
                continue
            
            # Check puzzle properties if requested
            if ensure_unique or ensure_logical:
                is_unique, is_logically_solvable = self.check_puzzle_properties()
                
                if ensure_unique and not is_unique:
                    self.retry_count += 1
                    continue
                    
                if ensure_logical and not is_logically_solvable:
                    self.retry_count += 1
                    continue
            
            # If we get here, the puzzle is valid and meets all requirements
            from .hex_queen_puzzle import HexQueenPuzzle
            return HexQueenPuzzle(self.grid, self.region_seeds, self.cell_regions)
        
        # If we've exceeded max retries, return None
        return None
    
    def get_puzzle_state(self) -> Dict:
        """
        Get the current state of the puzzle.
        
        Returns:
            Dict containing the puzzle state
        """
        # Check puzzle properties
        is_unique, is_logically_solvable = self.check_puzzle_properties()
        
        return {
            'grid_radius': self.grid.radius,
            'num_regions': self.num_regions,
            'region_seeds': {pid: (pos.x, pos.y, pos.z) for pid, pos in self.region_seeds.items()},
            'cell_regions': {(cell.x, cell.y, cell.z): region_id for cell, region_id in self.cell_regions.items()},
            'retry_count': self.retry_count,
            'is_unique': is_unique,
            'is_logically_solvable': is_logically_solvable
        }
    
    def get_region_sizes(self) -> Dict[int, int]:
        """Get the size of each region."""
        return {region_id: len(cells) for region_id, cells in self.regions.items()}