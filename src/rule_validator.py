"""
Rule validator for HexQueen puzzles.
"""
from typing import Dict, List, Set, Tuple, Optional
from collections import deque

from .hex_grid import HexGrid, HexCoord

import logging
logger = logging.getLogger(__name__)

class RuleValidator:
    """
    Validates rules and constraints for HexQueen puzzles.
    
    This class provides methods to check if a puzzle configuration
    meets the required constraints, such as queen visibility and
    region contiguity.
    """
    
    @staticmethod
    def check_queen_visibility(grid: HexGrid, queen_positions: Dict[int, HexCoord]) -> bool:
        """
        Check if queens can see each other (are in the same line).
        
        Args:
            grid: The hexagonal grid
            queen_positions: Dictionary mapping region IDs to queen positions
            
        Returns:
            True if no queens can see each other, False otherwise
        """
        queens = list(queen_positions.values())
        logger.debug(f"Checking visibility for {len(queens)} queens")
        
        # Check each pair of queens
        for i in range(len(queens)):
            for j in range(i + 1, len(queens)):
                queen1 = queens[i]
                queen2 = queens[j]
                
                # Check if queens are in the same line (same x, y, or z coordinate)
                if queen1.x == queen2.x:
                    #logger.debug(f"Queens at {queen1} and {queen2} share x-coordinate: {queen1.x}")
                    return False
                if queen1.y == queen2.y:
                    #logger.debug(f"Queens at {queen1} and {queen2} share y-coordinate: {queen1.y}")
                    return False
                if queen1.z == queen2.z:
                    #logger.debug(f"Queens at {queen1} and {queen2} share z-coordinate: {queen1.z}")
                    return False
        
        logger.debug("All queens are correctly placed - no visibility conflicts")
        return True
    
    @staticmethod
    def check_region_contiguity(grid: HexGrid, cell_regions: Dict[HexCoord, int]) -> bool:
        """
        Check if all regions in the puzzle are contiguous.
        
        A region is contiguous if all cells in the region are connected.
        
        Args:
            grid: The hexagonal grid
            cell_regions: Dictionary mapping cells to their region IDs
            
        Returns:
            True if all regions are contiguous, False otherwise
        """
        # Group cells by region
        regions = {}
        for cell, region_id in cell_regions.items():
            if region_id not in regions:
                regions[region_id] = set()
            regions[region_id].add(cell)
        
        # Check each region for contiguity
        for region_id, cells in regions.items():
            if not cells:
                continue
            
            # Start BFS from any cell in the region
            start = next(iter(cells))
            visited = {start}
            queue = deque([start])
            
            while queue:
                current = queue.popleft()
                for neighbor in grid.get_neighbors(current):
                    if neighbor in cells and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            # If not all cells are visited, the region is not contiguous
            if len(visited) != len(cells):
                return False
        
        return True
    
    @staticmethod
    def check_hex_grid_constraints(grid: HexGrid, cell_regions: Dict[HexCoord, int]) -> bool:
        """
        Check if the puzzle meets the hexagonal grid constraints.
        
        Args:
            grid: The hexagonal grid
            cell_regions: Dictionary mapping cells to their region IDs
            
        Returns:
            True if the puzzle meets all grid constraints, False otherwise
        """
        # Check if all cells in the grid are assigned to a region
        all_cells = grid.get_all_cells()
        assigned_cells = set(cell_regions.keys())
        
        if all_cells != assigned_cells:
            return False
        
        # Check if all cells are valid (within the grid)
        for cell in cell_regions.keys():
            if not grid.is_valid_cell(cell):
                return False
        
        return True