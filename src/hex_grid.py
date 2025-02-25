"""
HexGrid class for managing a hexagonal grid using cube coordinates.
"""
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

class HexCoord:
    """
    Represents a hexagonal cell using cube coordinates (x, y, z).
    In cube coordinates: x + y + z = 0
    """
    def __init__(self, x: int, y: int, z: int):
        assert x + y + z == 0, f"Invalid cube coordinates: {x}, {y}, {z}. Sum must be 0."
        self.x = x
        self.y = y
        self.z = z
    
    def __eq__(self, other):
        if not isinstance(other, HexCoord):
            return False
        return self.x == other.x and self.y == other.y and self.z == other.z
    
    def __hash__(self):
        return hash((self.x, self.y, self.z))
    
    def __repr__(self):
        return f"HexCoord({self.x}, {self.y}, {self.z})"
    
    def neighbor(self, direction: int) -> 'HexCoord':
        """
        Get the neighbor in the specified direction (0-5).
        Directions:
        0: East (+x, -z)
        1: Northeast (+y, -z)
        2: Northwest (-x, +y)
        3: West (-x, +z)
        4: Southwest (-y, +z)
        5: Southeast (+x, -y)
        """
        # Cube coordinate direction vectors
        directions = [
            (1, 0, -1),  # East
            (0, 1, -1),  # Northeast
            (-1, 1, 0),  # Northwest
            (-1, 0, 1),  # West
            (0, -1, 1),  # Southwest
            (1, -1, 0)   # Southeast
        ]
        
        dx, dy, dz = directions[direction % 6]
        return HexCoord(self.x + dx, self.y + dy, self.z + dz)
    
    def distance(self, other: 'HexCoord') -> int:
        """Calculate the distance between two hex coordinates."""
        return max(
            abs(self.x - other.x),
            abs(self.y - other.y),
            abs(self.z - other.z)
        )


class HexGrid:
    """
    Manages a hexagonal grid with cube coordinates.
    """
    def __init__(self, radius: int):
        """
        Initialize a hexagonal grid with the given radius.
        The radius determines the size of the grid (distance from center to edge).
        """
        self.radius = radius
        self.cells = self._generate_grid(radius)
        self._neighbors_cache = {}
        
    def _generate_grid(self, radius: int) -> Set[HexCoord]:
        """Generate all cells in a hexagonal grid with the given radius."""
        cells = set()
        for x in range(-radius, radius + 1):
            for y in range(max(-radius, -x - radius), min(radius, -x + radius) + 1):
                z = -x - y
                cells.add(HexCoord(x, y, z))
        return cells
    
    def get_neighbors(self, coord: HexCoord) -> List[HexCoord]:
        """Get all valid neighbors of a cell."""
        if coord in self._neighbors_cache:
            return self._neighbors_cache[coord]
        
        neighbors = []
        for direction in range(6):
            neighbor = coord.neighbor(direction)
            if neighbor in self.cells:
                neighbors.append(neighbor)
        
        self._neighbors_cache[coord] = neighbors
        return neighbors
    
    def get_all_cells(self) -> Set[HexCoord]:
        """Return all cells in the grid."""
        return self.cells
    
    def is_valid_cell(self, coord: HexCoord) -> bool:
        """Check if a coordinate is within the grid."""
        return coord in self.cells
    
    def get_random_cell(self, rng) -> HexCoord:
        """Get a random cell from the grid."""
        return rng.choice(list(self.cells))
    
    def get_center(self) -> HexCoord:
        """Get the center cell of the grid."""
        return HexCoord(0, 0, 0)
    
    def get_distance(self, coord1: HexCoord, coord2: HexCoord) -> int:
        """Get the distance between two cells."""
        return coord1.distance(coord2)