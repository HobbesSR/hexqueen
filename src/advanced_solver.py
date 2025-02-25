"""
Advanced solver for hexagonal grid puzzles with higher-order logical techniques.
This extends the basic PuzzleSolver with more sophisticated deduction methods.
"""
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import copy
import time

from .hex_grid import HexGrid, HexCoord
from .solver import PuzzleSolver

class AdvancedPuzzleSolver(PuzzleSolver):
    """
    Advanced solver for hexagonal grid puzzles using higher-order logical techniques.
    Extends the basic PuzzleSolver with more sophisticated deduction methods.
    """
    def __init__(self, grid: HexGrid, num_pieces: int):
        """
        Initialize the advanced puzzle solver.
        
        Args:
            grid: The hexagonal grid
            num_pieces: Number of pieces/regions
        """
        super().__init__(grid, num_pieces)
        
        # Add metrics for advanced techniques
        self.metrics.update({
            'region_bridging': 0,
            'critical_cut_detection': 0,
            'forcing_chains': 0,
            'connectivity_analysis': 0
        })
    
    def apply_logical_techniques(self) -> bool:
        """
        Apply all logical techniques until no more progress is made.
        Extends the basic solver with advanced techniques.
        
        Returns:
            bool: True if the puzzle is still valid, False if contradiction found
        """
        while True:
            progress = False
            
            # Apply basic techniques first
            result = self.apply_naked_singles()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            result = self.apply_hidden_singles()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            result = self.apply_hidden_pairs()
            progress = progress or result
            
            result = self.apply_region_contiguity_technique()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            # Apply advanced techniques
            result = self.apply_region_bridging_technique()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            result = self.apply_critical_cut_detection()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            result = self.apply_connectivity_analysis()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            # Apply forcing chains (more expensive, so apply last)
            result = self.apply_forcing_chains()
            if result is False:  # Contradiction
                return False
            progress = progress or result
            
            if not progress:
                break
        
        return True
    
    def apply_region_bridging_technique(self) -> bool:
        """
        Apply the region bridging technique: if removing a candidate cell would
        disconnect a region's assigned cells, that cell must be part of the region.
        
        Returns:
            bool: True if any assignments were made, False if contradiction found
        """
        made_progress = False
        
        for region_id in range(self.num_pieces):
            assigned = self.region_cells[region_id]
            if len(assigned) <= 1:
                continue
            
            candidate_cells = self._get_region_candidate_cells(region_id, assigned)
            if not candidate_cells:
                continue
            
            components = self._find_connected_components(assigned)
            
            if len(components) == 1:
                if self._apply_single_component_bridging(region_id, assigned, candidate_cells):
                    made_progress = True
            else:
                if self._apply_multiple_components_bridging(region_id, components, candidate_cells):
                    made_progress = True
                    
        return made_progress

    def _get_region_candidate_cells(self, region_id: int, assigned: Set[HexCoord]) -> Set[HexCoord]:
        """
        Helper function to get candidate cells for a specific region.
        """
        return {c for c, candidates in self.cell_candidates.items()
                if region_id in candidates and c not in assigned}

    def _apply_single_component_bridging(self, region_id: int, assigned: Set[HexCoord], candidate_cells: Set[HexCoord]) -> bool:
        """
        Helper function to apply bridging technique when there's a single connected component.
        """
        made_progress = False
        for cell in list(candidate_cells):
            remaining_candidates = candidate_cells - {cell}
            if not assigned or not remaining_candidates:
                continue
            if not self._can_connect_all_assigned_cells(region_id, assigned, remaining_candidates):
                if self.assign_cell(cell, region_id):
                    made_progress = True
                    self.metrics['region_bridging'] += 1
                else:
                    return False # Contradiction
        return made_progress

    def _apply_multiple_components_bridging(self, region_id: int, components: List[Set[HexCoord]], candidate_cells: Set[HexCoord]) -> bool:
        """
        Helper function to apply bridging technique when there are multiple connected components.
        """
        made_progress = False
        for i in range(len(components)):
            for j in range(i+1, len(components)):
                comp1, comp2 = components[i], components[j]
                connecting_cells = set()
                for cell in candidate_cells:
                    if self._is_connecting_cell(cell, comp1, comp2):
                        connecting_cells.add(cell)
                if len(connecting_cells) == 1:
                    cell = next(iter(connecting_cells))
                    if self.assign_cell(cell, region_id):
                        made_progress = True
                        self.metrics['region_bridging'] += 1
                    else:
                        return False # Contradiction
        return made_progress

    def _is_connecting_cell(self, cell: HexCoord, comp1: Set[HexCoord], comp2: Set[HexCoord]) -> bool:
        """
        Helper function to check if a candidate cell connects two components.
        """
        connects_to_comp1 = any(neighbor in comp1 for neighbor in self.grid.get_neighbors(cell))
        connects_to_comp2 = any(neighbor in comp2 for neighbor in self.grid.get_neighbors(cell))
        return connects_to_comp1 and connects_to_comp2
    
    def _can_connect_all_assigned_cells(self, region_id: int, assigned: Set[HexCoord], 
                                       candidates: Set[HexCoord]) -> bool:
        """
        Check if all assigned cells of a region can be connected through the given candidate cells.
        
        Args:
            region_id: The region ID to check
            assigned: Set of cells already assigned to the region
            candidates: Set of candidate cells that could be part of the region
            
        Returns:
            bool: True if all assigned cells can be connected, False otherwise
        """
        if not assigned:
            return True
        
        if len(assigned) == 1:
            return True
        
        # Create a graph including assigned and candidate cells
        graph = {}
        for cell in assigned | candidates:
            graph[cell] = []
            for neighbor in self.grid.get_neighbors(cell):
                if neighbor in assigned or neighbor in candidates:
                    graph[cell].append(neighbor)
        
        # Use BFS to check if all assigned cells are connected through the graph
        start = next(iter(assigned))
        visited = {start}
        queue = deque([start])
        visited_assigned = {start}
        
        while queue:
            current = queue.popleft()
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    if neighbor in assigned:
                        visited_assigned.add(neighbor)
        
        # Check if all assigned cells are in the visited set
        return len(visited_assigned) == len(assigned)
    
    def apply_critical_cut_detection(self) -> bool:
        """
        Apply critical cut detection: if there's a set of candidate cells that form
        the only possible path between two parts of a region, all those cells must
        belong to that region.
        
        Returns:
            bool: True if any assignments were made, False if contradiction found
        """
        made_progress = False
        
        # For each region
        for region_id in range(self.num_pieces):
            # Get cells already assigned to this region
            assigned = self.region_cells[region_id]
            if len(assigned) <= 1:
                continue  # Skip regions with 0 or 1 cells (trivially contiguous)
            
            # Get cells that could be part of this region (candidates)
            candidate_cells = {c for c, candidates in self.cell_candidates.items()
                              if region_id in candidates and c not in assigned}
            
            if not candidate_cells:
                continue # No candidate cells to form critical cuts
            
            # Find connected components of assigned cells for this region
            components = self._find_connected_components(assigned)
            
            # If there's only one component or no components, no critical cut detection needed
            if len(components) <= 1:
                continue # Need at least two components to have a critical cut
            
            # Find potential bridges (paths of candidate cells) between components
            bridges = self._find_potential_bridges(components, candidate_cells)
            
            # For each pair of components
            for i in range(len(components)):
                for j in range(i+1, len(components)):
                    comp1, comp2 = components[i], components[j]
                    
                    # Find all possible paths (bridges) between these components
                    key = (frozenset(comp1), frozenset(comp2))
                    if key not in bridges or not bridges[key]:
                        # No path exists between these components through candidate cells - contradiction!
                        return False
                    
                    # If there's only one possible path (bridge) between these components,
                    # then all cells in that path must be assigned to this region
                    if len(bridges[key]) == 1:
                        path = bridges[key][0] # Get the single bridge path
                        for cell in path: # For each cell in the critical path
                            if cell not in assigned and region_id in self.cell_candidates[cell]:
                                if self.assign_cell(cell, region_id): # Force assign cell to region
                                    made_progress = True
                                    self.metrics['critical_cut_detection'] += 1
                                else:
                                    # Contradiction found during assignment
                                    return False
        
        return made_progress
    
    def _find_connected_components(self, cells: Set[HexCoord]) -> List[Set[HexCoord]]:
        """
        Find connected components in a set of cells.
        
        Args:
            cells: Set of cells to find components in
            
        Returns:
            List of sets, each set being a connected component
        """
        components = []
        unvisited = cells.copy()
        
        while unvisited:
            # Start a new component
            start = next(iter(unvisited))
            component = set()
            queue = deque([start])
            component.add(start)
            unvisited.remove(start)
            
            # BFS to find all cells in this component
            while queue:
                current = queue.popleft()
                for neighbor in self.grid.get_neighbors(current):
                    if neighbor in unvisited:
                        component.add(neighbor)
                        queue.append(neighbor)
                        unvisited.remove(neighbor)
            
            components.append(component)
        
        return components
    
    def _find_potential_bridges(self, components: List[Set[HexCoord]], 
                               candidates: Set[HexCoord]) -> Dict[Tuple[frozenset, frozenset], List[List[HexCoord]]]:
        """
        Find potential bridges (paths through candidate cells) between components.
        
        Args:
            components: List of connected components
            candidates: Set of candidate cells
            
        Returns:
            Dictionary mapping (component1, component2) to list of possible paths
        """
        bridges = {}
        
        # For each pair of components
        for i in range(len(components)):
            for j in range(i+1, len(components)):
                comp1, comp2 = components[i], components[j]
                key = (frozenset(comp1), frozenset(comp2))
                bridges[key] = []
                
                # Find all possible paths between these components
                # This is a simplified approach - in a real implementation,
                # you might want to use a more efficient algorithm
                
                # Start from each cell in comp1
                for start in comp1:
                    # Try to reach any cell in comp2
                    visited = set()
                    paths = [[start]]
                    
                    while paths:
                        new_paths = []
                        for path in paths:
                            current = path[-1]
                            
                            # If we've reached comp2, add this path to bridges
                            if current in comp2:
                                # Extract just the candidate cells from the path
                                bridge = [c for c in path[1:-1] if c in candidates]
                                if bridge and bridge not in bridges[key]:
                                    bridges[key].append(bridge)
                                continue
                            
                            # Otherwise, continue the search
                            for neighbor in self.grid.get_neighbors(current):
                                if (neighbor in candidates or neighbor in comp2) and neighbor not in visited and neighbor not in path:
                                    new_path = path + [neighbor]
                                    new_paths.append(new_path)
                                    visited.add(neighbor)
                        
                        paths = new_paths
        
        return bridges
    
    def apply_connectivity_analysis(self) -> bool:
        """
        Apply connectivity analysis: analyze the connectivity graph of each region
        to make deductions about cell assignments.
        
        Returns:
            bool: True if any assignments were made, False if contradiction found
        """
        made_progress = False
        
        # For each region
        for region_id in range(self.num_pieces):
            # Get cells already assigned to this region
            assigned = self.region_cells[region_id]
            if not assigned:
                continue # Skip if no cells are assigned yet
            
            # Get cells that could be part of this region (candidates)
            candidate_cells = {c for c, candidates in self.cell_candidates.items()
                              if region_id in candidates and c not in assigned}
            
            if not candidate_cells:
                continue # No candidate cells to analyze connectivity
            
            # For each unassigned cell in the grid
            for cell in list(self.cell_candidates.keys()):
                if cell in self.assigned_cells or cell in candidate_cells:
                    continue # Skip assigned and candidate cells
                
                # Check if assigning this cell to any region other than region_id
                # would isolate parts of region_id, making it a critical connection point
                
                # Get neighbors of this cell that are candidates for region_id
                region_neighbors = [n for n in self.grid.get_neighbors(cell)
                                   if n in candidate_cells]
                
                if len(region_neighbors) <= 1:
                    continue # Need at least two region neighbors to be a critical connection
                
                # Check if this cell is a critical connection point for region contiguity
                # Temporarily remove region_id from this cell's candidates
                saved_candidates = self.cell_candidates[cell].copy()
                
                # Simulate assigning this cell to a different region
                self.cell_candidates[cell] = self.cell_candidates[cell] - {region_id}
                
                # Check if the region would still be contiguous if this cell is not part of it
                if not self.check_region_contiguity(region_id, cell):
                    # If region contiguity is broken, this cell must be part of region_id
                    self.cell_candidates[cell] = saved_candidates # Restore original candidates
                    if self.assign_cell(cell, region_id): # Force assign cell to region_id
                        made_progress = True
                        self.metrics['connectivity_analysis'] += 1
                    else:
                        # Contradiction found during assignment
                        return False
                else:
                    # If region remains contiguous, restore original candidates and continue
                    self.cell_candidates[cell] = saved_candidates # Restore original candidates
        
        return made_progress
    
    def apply_forcing_chains(self, max_depth: int = 2) -> bool:
        """
        Apply forcing chains: make a temporary assignment and see if it leads to a contradiction.
        
        Args:
            max_depth: Maximum depth of the forcing chain
            
        Returns:
            bool: True if any assignments were made, False if contradiction found
        """
        made_progress = False
        
        # For each unassigned cell
        for cell in list(self.cell_candidates.keys()):
            if cell in self.assigned_cells:
                continue # Skip already assigned cells
            
            # For each candidate region for this cell
            for region_id in list(self.cell_candidates[cell]):
                # Start a forcing chain by temporarily assigning this cell to this region
                saved_assigned = self.assigned_cells.copy()
                saved_region_cells = copy.deepcopy(self.region_cells)
                saved_candidates = copy.deepcopy(self.cell_candidates)
                
                # Try assigning the cell to the region
                contradiction = False # Assume no contradiction initially
                if self.assign_cell(cell, region_id):
                    # If assignment is valid, propagate constraints using logical techniques
                    if not self.apply_logical_techniques(): # If logical techniques lead to contradiction
                        contradiction = True # Mark contradiction
                else:
                    contradiction = True # Mark contradiction if initial assignment failed
                
                # Restore state after the chain reaction
                self.assigned_cells = saved_assigned
                self.region_cells = saved_region_cells
                self.cell_candidates = saved_candidates
                
                # If a contradiction was found, then this candidate (region_id) must be invalid for this cell
                if contradiction:
                    self.cell_candidates[cell].remove(region_id) # Eliminate the candidate
                    made_progress = True
                    self.metrics['forcing_chains'] += 1
                    
                    # If eliminating this candidate leads to no candidates left for the cell, it's a hard contradiction
                    if not self.cell_candidates[cell]:
                        return False # Hard contradiction, puzzle is unsolvable
                    
                    # If eliminating this candidate leaves only one candidate, assign it as a naked single
                    if len(self.cell_candidates[cell]) == 1:
                        remaining_region = next(iter(self.cell_candidates[cell]))
                        if not self.assign_cell(cell, remaining_region): # Assign the last remaining candidate
                            return False # Contradiction during assignment
        
        return made_progress