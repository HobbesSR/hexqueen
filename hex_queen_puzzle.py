"""
Shared functionality for hexagonal queen puzzles.
This module contains common code used by both main.py and puzzle_page_generator.py.
"""
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from hex_grid import HexGrid, HexCoord

def hex_to_pixel(coord: HexCoord, size: float = 1.0) -> Tuple[float, float]:
    """
    Convert hex coordinates to pixel coordinates.
    
    Args:
        coord: The hex coordinate
        size: The size of the hexagon
        
    Returns:
        Tuple of (x, y) pixel coordinates
    """
    x = size * (3/2 * coord.x)
    y = size * (np.sqrt(3)/2 * coord.x + np.sqrt(3) * coord.z)
    return (x, y)

def draw_hexagon(ax, center: Tuple[float, float], size: float, color: str, alpha=0.8, edgecolor='black', linewidth=0.5):
    """
    Draw a hexagon on the given axes.
    
    Args:
        ax: Matplotlib axes
        center: Center coordinates (x, y)
        size: Size of the hexagon
        color: Fill color
        alpha: Transparency (0-1)
        edgecolor: Edge color
        linewidth: Width of the edge line
    """
    angles = np.linspace(0, 2*np.pi, 7)[:-1]
    x = center[0] + size * np.cos(angles)
    y = center[1] + size * np.sin(angles)
    
    hex_patch = patches.Polygon(np.column_stack([x, y]), closed=True, 
                               fill=True, color=color, alpha=alpha, 
                               edgecolor=edgecolor, linewidth=linewidth)
    ax.add_patch(hex_patch)

def draw_queen(ax, center: Tuple[float, float], markersize=10, color='black'):
    """
    Draw a queen marker on the given axes.
    
    Args:
        ax: Matplotlib axes
        center: Center coordinates (x, y)
        markersize: Size of the marker
        color: Color of the marker
    """
    ax.plot(center[0], center[1], 'o', markersize=markersize, color=color)

def get_region_color(region_id: int, cmap_name='tab20') -> str:
    """
    Get a color for a region using a colormap.
    
    Args:
        region_id: The ID of the region
        cmap_name: Name of the colormap to use
        
    Returns:
        Color string or RGBA tuple
    """
    cmap = plt.cm.get_cmap(cmap_name, 20)
    return cmap(region_id % 20)

def grow_regions_from_queens(grid: HexGrid, queen_positions: Dict[int, HexCoord], rng: random.Random):
    """
    Grow regions from queen positions using a randomized approach.
    
    Args:
        grid: The hexagonal grid.
        queen_positions: Mapping of queen IDs to their positions.
        rng: Random number generator.
        
    Returns:
        Tuple of (success, cell_regions, regions)
    """
    regions = defaultdict(set)
    cell_regions = {}
    
    # Initialize regions with queen positions
    for queen_id, pos in queen_positions.items():
        regions[queen_id].add(pos)
        cell_regions[pos] = queen_id
    
    # Unassigned cells
    unassigned_cells = set(grid.get_all_cells()) - set(queen_positions.values())
    bordering_cells = defaultdict(set)
    
    # Initialize bordering cells for each region
    for queen_id, pos in queen_positions.items():
        for neighbor in grid.get_neighbors(pos):
            if neighbor in unassigned_cells:
                bordering_cells[queen_id].add(neighbor)
    
    # Grow regions until all cells are assigned
    while unassigned_cells:
        active_regions = [r for r, cells in bordering_cells.items() if cells]
        if not active_regions:
            return False, cell_regions, regions
        
        region_id = rng.choice(active_regions)
        if not bordering_cells[region_id]:
            continue
        
        cell = rng.choice(list(bordering_cells[region_id]))
        regions[region_id].add(cell)
        cell_regions[cell] = region_id
        unassigned_cells.remove(cell)
        
        # Update bordering cells
        for r in bordering_cells:
            if cell in bordering_cells[r]:
                bordering_cells[r].remove(cell)
        
        for neighbor in grid.get_neighbors(cell):
            if neighbor in unassigned_cells:
                bordering_cells[region_id].add(neighbor)
    
    return True, cell_regions, regions

def check_regions_contiguity(grid: HexGrid, regions: Dict[int, set]) -> bool:
    """
    Check that every region is contiguous using BFS.
    
    Args:
        grid: The hexagonal grid.
        regions: Mapping of region id to set of cells.
        
    Returns:
        True if all regions are contiguous, False otherwise.
    """
    for region_id, cells in regions.items():
        if not cells:
            continue
        
        start = next(iter(cells))
        visited = {start}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            for neighbor in grid.get_neighbors(current):
                if neighbor in cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        if len(visited) != len(cells):
            return False
    
    return True

def calculate_recommended_queens(radius: int) -> int:
    """
    Calculate the recommended number of queens for a hexagonal grid of given radius.
    
    For a hex grid of radius r:
    - r=0 means 1 central hex
    - r=1 means 7 hexes (1 central + 6 around it)
    - r=2 means 19 hexes (7 from r=1 + 12 in the outer ring)
    
    The formula for the total number of cells is 3r(r+1)+1.
    For queen placement, the formula is r*2+1:
    - r=0: 1 queen
    - r=1: 3 queens
    - r=2: 5 queens
    - r=3: 7 queens
    - r=4: 9 queens
    
    Args:
        radius: The radius of the hexagonal grid
        
    Returns:
        int: Recommended number of queens
    """
    if radius == 0:
        return 1
    else:
        return radius * 2 + 1

def generate_puzzle_with_queens(grid: HexGrid, seed: Optional[int] = None, max_attempts: int = 3):
    """
    Generate a puzzle using queen placements.
    
    Args:
        grid: The hexagonal grid
        seed: Random seed for reproducibility
        max_attempts: Maximum number of attempts to generate a valid puzzle
        
    Returns:
        Tuple of (success, grid, cell_regions, queen_positions)
    """
    from queen_placer import QueenPlacer
    
    attempt = 0
    valid = False
    current_seed = seed
    rng = random.Random(seed)
    
    while attempt < max_attempts and not valid:
        num_queens = calculate_recommended_queens(grid.radius)
        placer = QueenPlacer(grid, num_queens, current_seed)
        
        if not placer.place_queens():
            attempt += 1
            if current_seed is not None:
                current_seed += 1
            continue
        
        queen_positions = placer.get_queen_positions()
        valid, cell_regions, regions = grow_regions_from_queens(grid, queen_positions, rng)
        
        if valid and not check_regions_contiguity(grid, regions):
            valid = False
        
        if not valid:
            attempt += 1
            if current_seed is not None:
                current_seed += 1
    
    if not valid:
        return False, grid, {}, {}
    
    return True, grid, cell_regions, queen_positions

def draw_hex_grid(ax, grid: HexGrid, cell_regions: Dict[HexCoord, int], 
                 piece_positions: Dict[int, HexCoord], show_pieces: bool = True, 
                 hex_size: float = 0.5, title: Optional[str] = None):
    """
    Draw the hex grid with regions and optionally queen markers.
    
    Args:
        ax: Matplotlib axes
        grid: The hexagonal grid
        cell_regions: Mapping of cells to their regions
        piece_positions: Mapping of piece IDs to their positions
        show_pieces: Whether to show the pieces (queens)
        hex_size: Size of the hexagons
        title: Optional title for the plot
    """
    # Clear the axes
    ax.clear()
    ax.set_facecolor('white')
    ax.axis('off')
    
    # Draw cells with region colors
    for cell in grid.get_all_cells():
        pixel = hex_to_pixel(cell, hex_size)
        if cell in cell_regions:
            region_id = cell_regions[cell]
            if region_id < 0:
                if region_id == -1:
                    draw_hexagon(ax, pixel, hex_size, 'lightgray', alpha=0.5)
                elif region_id == -2:
                    draw_hexagon(ax, pixel, hex_size, 'whitesmoke', alpha=0.5)
                else:
                    draw_hexagon(ax, pixel, hex_size, 'white', alpha=0.3)
            else:
                color = get_region_color(region_id)
                draw_hexagon(ax, pixel, hex_size, color)
        else:
            draw_hexagon(ax, pixel, hex_size, 'white')
    
    # Draw pieces (queens)
    if show_pieces:
        for piece_id, pos in piece_positions.items():
            pixel = hex_to_pixel(pos, hex_size)
            draw_queen(ax, pixel)
    
    # Set plot properties
    ax.set_aspect('equal')
    ax.set_xlim([-2*grid.radius, 2*grid.radius])
    ax.set_ylim([-2*grid.radius, 2*grid.radius])
    
    if title:
        ax.set_title(title)