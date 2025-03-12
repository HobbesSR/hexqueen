"""
Growth-based region generator for HexQueen puzzles.
"""
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque
import heapq
import random

from .hex_grid import HexGrid, HexCoord
from .interfaces import IRegionGenerator
from .rule_validator import RuleValidator

class GrowthRegionGenerator(IRegionGenerator):
    """
    Generates regions for HexQueen puzzles using a growth-based algorithm.
    
    This generator starts with queen positions as seeds and grows regions
    outward until the entire grid is covered, prioritizing smaller frontiers
    to ensure balanced region sizes.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the growth region generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.rng = random.Random(seed)
        self.validator = RuleValidator()
        
        # State for region generation
        self.regions = defaultdict(set)  # Maps region_id -> set of HexCoord
        self.region_frontiers = defaultdict(set)  # Maps region_id -> frontier cells
    
    def generate_regions(self, grid: HexGrid, queen_positions: Dict[int, HexCoord]) -> Dict[HexCoord, int]:
        """
        Generate regions for a HexQueen puzzle using a growth-based algorithm.
        
        Args:
            grid: The hexagonal grid for the puzzle
            queen_positions: Dictionary mapping region IDs to queen positions
            
        Returns:
            Dictionary mapping cells to their region IDs
        """
        # Reset state
        self.regions = defaultdict(set)
        self.region_frontiers = defaultdict(set)
        cell_regions = {}
        
        print(f"Generating regions for {len(queen_positions)} queens")
        
        # Initialize regions with queen positions
        for region_id, queen_pos in queen_positions.items():
            self.regions[region_id].add(queen_pos)
            cell_regions[queen_pos] = region_id
            
            # Add neighbors to frontier
            for neighbor in grid.get_neighbors(queen_pos):
                if neighbor not in cell_regions:
                    self.region_frontiers[region_id].add(neighbor)
        
        print(f"Initial frontiers: {[len(f) for f in self.region_frontiers.values()]}")
        
        # Grow regions until the entire board is covered
        if not self._grow_regions(grid, queen_positions, cell_regions):
            print("Failed to grow regions: _grow_regions returned False")
            return {}  # Failed to grow regions
        
        # Validate the generated regions
        if not self.validate_regions(grid, cell_regions):
            print("Failed to validate regions")
            return {}  # Regions are not valid
        
        print(f"Successfully generated regions for all {len(grid.get_all_cells())} cells")
        return cell_regions
    
    def _grow_regions(self, grid: HexGrid, queen_positions: Dict[int, HexCoord],
                     cell_regions: Dict[HexCoord, int]) -> bool:
        """
        Grow regions until the entire board is covered using a simple adjacency-based approach.
        
        Args:
            grid: The hexagonal grid
            queen_positions: Dictionary mapping region IDs to queen positions
            cell_regions: Dictionary mapping cells to their region IDs (modified in-place)
            
        Returns:
            True if regions were grown successfully, False otherwise
        """
        print(f"Starting region growth. Total cells: {len(grid.get_all_cells())}, Assigned cells: {len(cell_regions)}")
        
        # Initialize regions with queen positions
        self.regions = defaultdict(set)
        for region_id, queen_pos in queen_positions.items():
            self.regions[region_id].add(queen_pos)
            cell_regions[queen_pos] = region_id
        
        # Set of unaffiliated cells (not assigned to any region)
        unaffiliated_cells = set(grid.get_all_cells()) - set(queen_positions.values())
        
        # For each region, maintain a set of adjacent unaffiliated cells
        region_adjacency = defaultdict(set)
        for region_id, queen_pos in queen_positions.items():
            for neighbor in grid.get_neighbors(queen_pos):
                if neighbor in unaffiliated_cells:
                    region_adjacency[region_id].add(neighbor)
        
        # Continue until all cells are assigned to a region
        iteration = 0
        max_iterations = len(grid.get_all_cells()) * 2  # Prevent infinite loops
        
        while unaffiliated_cells and iteration < max_iterations:
            iteration += 1
            if iteration % 10 == 0:
                print(f"Iteration {iteration}: Assigned {len(cell_regions)}/{len(grid.get_all_cells())} cells")
            
            # Find regions with non-empty adjacency sets
            active_regions = [r for r, adj in region_adjacency.items() if adj]
            if not active_regions:
                print("Error: No regions have adjacent unaffiliated cells")
                return False
            
            # Randomly pick a region
            region_id = self.rng.choice(active_regions)
            
            # Randomly pick an adjacent cell
            cell = self.rng.choice(list(region_adjacency[region_id]))
            
            # Add the cell to the region
            self.regions[region_id].add(cell)
            cell_regions[cell] = region_id
            unaffiliated_cells.remove(cell)
            
            # Remove this cell from all regions' adjacency sets
            for r in region_adjacency:
                if cell in region_adjacency[r]:
                    region_adjacency[r].remove(cell)
            
            # Add any unaffiliated cells adjacent to this newly added cell to the region's adjacency set
            for neighbor in grid.get_neighbors(cell):
                if neighbor in unaffiliated_cells:
                    region_adjacency[region_id].add(neighbor)
        
        # Check if we've assigned all cells
        if unaffiliated_cells:
            print(f"Failed to assign all cells after {iteration} iterations")
            return False
        
        # Verify that all regions are contiguous
        for region_id, cells in self.regions.items():
            if len(cells) <= 1:
                continue  # Regions with 0 or 1 cells are trivially contiguous
                
            # Start BFS from any cell in the region
            start = next(iter(cells))
            visited = {start}
            queue = deque([start])
            
            while queue:
                current = queue.popleft()
                for neighbor in grid.get_neighbors(current):
                    if (neighbor in cells and
                        neighbor not in visited):
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            # If not all cells are visited, the region is not contiguous
            if len(visited) != len(cells):
                print(f"Region {region_id} is not contiguous after growth")
                return False
        
        print("All regions are contiguous after growth")
        return True
    
    def validate_regions(self, grid: HexGrid, cell_regions: Dict[HexCoord, int]) -> bool:
        """
        Validate that the regions in a puzzle meet all constraints.
        
        Args:
            grid: The hexagonal grid for the puzzle
            cell_regions: Dictionary mapping cells to their region IDs
            
        Returns:
            True if the regions are valid, False otherwise
        """
        print(f"Validating regions. Total cells: {len(grid.get_all_cells())}, Assigned cells: {len(cell_regions)}")
        
        # Check if all regions are contiguous
        is_contiguous = RuleValidator.check_region_contiguity(grid, cell_regions)
        if not is_contiguous:
            print("Validation failed: Regions are not contiguous")
            return False
        
        # Check if the puzzle meets the hexagonal grid constraints
        meets_constraints = RuleValidator.check_hex_grid_constraints(grid, cell_regions)
        if not meets_constraints:
            print("Validation failed: Puzzle does not meet hexagonal grid constraints")
            return False
        
        print("Validation successful: All regions are valid")
        return True
    
    def get_region_sizes(self) -> Dict[int, int]:
        """
        Get the size of each region.
        
        Returns:
            Dictionary mapping region IDs to their sizes
        """
        return {region_id: len(cells) for region_id, cells in self.regions.items()}