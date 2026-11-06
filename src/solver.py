"""
Puzzle solvers for HexQueen.

Two complementary solvers live here:

* ``count_solutions`` / ``find_solutions`` - an exhaustive solver used to prove
  that a puzzle has exactly one solution (requirement 213).
* ``LogicalSolver`` - a human-style deduction engine used to prove that a
  puzzle can be solved without guessing (requirement 214). It also reports
  the hardest technique it needed, which doubles as a difficulty rating.

Puzzle rules
------------
A puzzle with radius ``r`` has ``2r+1`` regions. Exactly one queen goes in each
region, and no two queens may share an x, y or z cube-coordinate line. Because
there are also exactly ``2r+1`` lines on each axis, *every* line holds exactly
one queen. (Adjacent cells always share a line, so "queens may not touch" is
implied.)
"""
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from .hex_grid import HexCoord, HexGrid

AXES = ("x", "y", "z")


def _regions_to_cells(cell_regions: Dict[HexCoord, int]) -> Dict[int, List[HexCoord]]:
    by_region: Dict[int, List[HexCoord]] = {}
    for cell, region in cell_regions.items():
        by_region.setdefault(region, []).append(cell)
    return by_region


# --------------------------------------------------------------------------
# Exhaustive solver
# --------------------------------------------------------------------------
def find_solutions(cell_regions: Dict[HexCoord, int], limit: Optional[int] = 2
                   ) -> List[Dict[int, HexCoord]]:
    """
    Find up to ``limit`` solutions (all of them if ``limit`` is None).

    Each solution maps region id -> queen cell. The search always branches on
    the region with the fewest still-legal cells, so it stays fast for the
    board sizes this project cares about.
    """
    by_region = _regions_to_cells(cell_regions)
    solutions: List[Dict[int, HexCoord]] = []
    chosen: Dict[int, HexCoord] = {}

    def search(remaining: Set[int], ux: FrozenSet[int], uy: FrozenSet[int], uz: FrozenSet[int]):
        if limit is not None and len(solutions) >= limit:
            return
        if not remaining:
            solutions.append(dict(chosen))
            return
        best_region, best_options = None, None
        for region in remaining:
            options = [c for c in by_region[region]
                       if c.x not in ux and c.y not in uy and c.z not in uz]
            if not options:
                return  # dead end
            if best_options is None or len(options) < len(best_options):
                best_region, best_options = region, options
                if len(options) == 1:
                    break
        remaining.discard(best_region)
        for cell in best_options:
            chosen[best_region] = cell
            search(remaining, ux | {cell.x}, uy | {cell.y}, uz | {cell.z})
            if limit is not None and len(solutions) >= limit:
                break
        del chosen[best_region]
        remaining.add(best_region)

    search(set(by_region), frozenset(), frozenset(), frozenset())
    return solutions


def count_solutions(cell_regions: Dict[HexCoord, int], limit: Optional[int] = 2) -> int:
    """Count solutions, stopping early once ``limit`` have been found."""
    return len(find_solutions(cell_regions, limit))


def has_unique_solution(cell_regions: Dict[HexCoord, int]) -> bool:
    return count_solutions(cell_regions, limit=2) == 1


# --------------------------------------------------------------------------
# Logical solver
# --------------------------------------------------------------------------
@dataclass
class LogicResult:
    """Outcome of a logical solve attempt."""
    solved: bool
    difficulty: int                      # largest set size k that was required (0 = nothing needed)
    remaining_candidates: int            # candidate cells left; == number of regions when solved
    contradiction: bool = False
    steps: List[str] = field(default_factory=list)
    solution: Dict[int, HexCoord] = field(default_factory=dict)


class LogicalSolver:
    """
    Solves a puzzle by deduction only.

    Every technique is one pattern, parameterised by a set size ``k``:

    * **Region set** - if ``k`` regions can only put their queens on ``k``
      lines of one axis, those lines are used up, so no *other* region may
      use them.
    * **Line set** - if ``k`` lines of one axis can only receive their queens
      from ``k`` regions, those regions must spend their queens there, so
      they can't use any other line of that axis.

    k=1 covers the beginner rules (a lone candidate is a queen; a region
    confined to a line clears that line; a line fed by one region pins that
    region), k=2 the pair rules and so on. The solver always uses the smallest
    k that makes progress, so ``difficulty`` is the hardest k needed.
    """

    def __init__(self, grid: HexGrid, cell_regions: Dict[HexCoord, int], max_k: int = 4):
        self.grid = grid
        self.max_k = max_k
        self.regions = sorted(set(cell_regions.values()))
        self.region_of = dict(cell_regions)
        self.cand: Dict[int, Set[HexCoord]] = {r: set() for r in self.regions}
        for cell, region in cell_regions.items():
            self.cand[region].add(cell)
        radius = grid.radius
        self.line_values = list(range(-radius, radius + 1))

    @staticmethod
    def _coord(cell: HexCoord, axis: str) -> int:
        return getattr(cell, axis)

    def _remaining(self) -> int:
        return sum(len(c) for c in self.cand.values())

    # -- one elimination pass for a given k ---------------------------------
    def _region_sets(self, axis: str, k: int) -> Optional[str]:
        for group in combinations(self.regions, k):
            lines = {self._coord(c, axis) for r in group for c in self.cand[r]}
            if len(lines) != k:
                continue
            members = set(group)
            changed = False
            for other in self.regions:
                if other in members:
                    continue
                doomed = {c for c in self.cand[other] if self._coord(c, axis) in lines}
                if doomed:
                    self.cand[other] -= doomed
                    changed = True
            if changed:
                return f"k={k}: regions {sorted(group)} occupy {axis}-lines {sorted(lines)}"
        return None

    def _line_sets(self, axis: str, k: int) -> Optional[str]:
        feeders: Dict[int, Set[int]] = {v: set() for v in self.line_values}
        for region, cells in self.cand.items():
            for c in cells:
                feeders[self._coord(c, axis)].add(region)
        for group in combinations(self.line_values, k):
            sources = set().union(*(feeders[v] for v in group))
            if len(sources) != k:
                continue
            lines = set(group)
            changed = False
            for region in sources:
                doomed = {c for c in self.cand[region] if self._coord(c, axis) not in lines}
                if doomed:
                    self.cand[region] -= doomed
                    changed = True
            if changed:
                return f"k={k}: {axis}-lines {sorted(lines)} are served only by regions {sorted(sources)}"
        return None

    def _contradiction(self) -> bool:
        if any(not cells for cells in self.cand.values()):
            return True
        for axis in AXES:
            covered = {self._coord(c, axis) for cells in self.cand.values() for c in cells}
            if len(covered) < len(self.line_values):
                return True
        return False

    # -- driver --------------------------------------------------------------
    def solve(self, record_steps: bool = False) -> LogicResult:
        difficulty = 0
        steps: List[str] = []
        progress = True
        while progress and not self._contradiction():
            progress = False
            for k in range(1, self.max_k + 1):
                for axis in AXES:
                    for rule in (self._region_sets, self._line_sets):
                        note = rule(axis, k)
                        if note:
                            difficulty = max(difficulty, k)
                            if record_steps:
                                steps.append(note)
                            progress = True
                            break
                    if progress:
                        break
                if progress:
                    break

        contradiction = self._contradiction()
        solved = not contradiction and all(len(c) == 1 for c in self.cand.values())
        solution = {r: next(iter(c)) for r, c in self.cand.items()} if solved else {}
        return LogicResult(solved, difficulty, self._remaining(), contradiction, steps, solution)


def logical_solve(grid: HexGrid, cell_regions: Dict[HexCoord, int], max_k: int = 4,
                  record_steps: bool = False) -> LogicResult:
    return LogicalSolver(grid, cell_regions, max_k).solve(record_steps)
