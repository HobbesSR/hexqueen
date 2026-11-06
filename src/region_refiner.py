"""
Region refiner: turns a random region layout into a unique, logically
solvable one by making small boundary edits.

Rejection sampling (grow random regions, hope for a unique puzzle) collapses
as the board grows - at radius 5 fewer than 2% of random layouts qualify. A
local search is far more effective: move one boundary cell to a neighbouring
region, keep the move if the puzzle did not get worse, repeat.

Phase 1 minimises the number of solutions (target: exactly 1).
Phase 2 keeps the solution unique while minimising the candidates the
logical solver cannot eliminate (target: fully solved by deduction).
"""
import random
from typing import Dict, List, Optional, Tuple

from .hex_grid import HexCoord, HexGrid
from .solver import count_solutions, logical_solve

SOLUTION_CAP = 64  # counting beyond this adds no useful gradient


class RegionRefiner:
    def __init__(self, grid: HexGrid, queen_positions: Dict[int, HexCoord],
                 seed: Optional[int] = None, min_region_size: int = 2,
                 max_k: int = 3):
        self.grid = grid
        self.queens = set(queen_positions.values())
        self.rng = random.Random(seed)
        self.min_region_size = min_region_size
        self.max_k = max_k

    # -- region edits --------------------------------------------------------
    def _is_connected_without(self, cell_regions: Dict[HexCoord, int], region: int,
                              removed: HexCoord) -> bool:
        cells = [c for c, r in cell_regions.items() if r == region and c != removed]
        if not cells:
            return False
        seen = {cells[0]}
        stack = [cells[0]]
        members = set(cells)
        while stack:
            for n in self.grid.get_neighbors(stack.pop()):
                if n in members and n not in seen:
                    seen.add(n)
                    stack.append(n)
        return len(seen) == len(members)

    def _random_move(self, cell_regions: Dict[HexCoord, int],
                     sizes: Dict[int, int]) -> Optional[Tuple[HexCoord, int, int]]:
        """Pick a legal (cell, from_region, to_region) boundary move, or None."""
        cells = list(cell_regions)
        for _ in range(60):
            cell = self.rng.choice(cells)
            if cell in self.queens:
                continue
            src = cell_regions[cell]
            if sizes[src] <= self.min_region_size:
                continue
            targets = sorted({cell_regions[n] for n in self.grid.get_neighbors(cell)} - {src})
            if not targets:
                continue
            if not self._is_connected_without(cell_regions, src, cell):
                continue
            return cell, src, self.rng.choice(targets)
        return None

    # -- scoring -------------------------------------------------------------
    def _score(self, cell_regions: Dict[HexCoord, int], need_logic: bool) -> Tuple[int, int]:
        """Lower is better. (extra solutions, undeduced candidates)."""
        extra = count_solutions(cell_regions, limit=SOLUTION_CAP) - 1
        if extra > 0 or not need_logic:
            return extra, 0
        result = logical_solve(self.grid, cell_regions, max_k=self.max_k)
        return 0, result.remaining_candidates - len(self.queens)

    # -- main loop -----------------------------------------------------------
    def refine(self, cell_regions: Dict[HexCoord, int], require_logical: bool = True,
               max_steps: int = 4000) -> Optional[Dict[HexCoord, int]]:
        """
        Return an improved copy of ``cell_regions`` that satisfies the
        requested guarantees, or None if ``max_steps`` was not enough.
        """
        regions = dict(cell_regions)
        sizes: Dict[int, int] = {}
        for r in regions.values():
            sizes[r] = sizes.get(r, 0) + 1

        score = self._score(regions, require_logical)
        for _ in range(max_steps):
            if score == (0, 0):
                return regions
            move = self._random_move(regions, sizes)
            if move is None:
                return None
            cell, src, dst = move
            regions[cell] = dst
            new_score = self._score(regions, require_logical)
            if new_score <= score:               # accept sideways moves to cross plateaus
                score = new_score
                sizes[src] -= 1
                sizes[dst] += 1
            else:
                regions[cell] = src
        return regions if score == (0, 0) else None
