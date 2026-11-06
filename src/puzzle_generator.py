"""
Puzzle generator: queens -> regions -> refinement.

Pipeline
--------
1. ``QueenPlacer`` picks a legal queen layout (the hidden solution).
2. A region generator grows one contiguous region around each queen.
3. ``RegionRefiner`` nudges region boundaries until the puzzle has exactly one
   solution and can be solved by deduction alone.
"""
import logging
import random
from typing import Dict, Optional, Tuple

from .hex_grid import HexGrid, HexCoord
from .hex_queen_puzzle import HexQueenPuzzle
from .interfaces import IRegionGenerator, PuzzleSpecification
from .queen_placer import QueenPlacer
from .region_refiner import RegionRefiner
from .rule_validator import RuleValidator
from .solver import logical_solve

logger = logging.getLogger(__name__)


class PuzzleGenerator:
    """
    Generates puzzles on a hexagonal grid using an injected region generation
    strategy (see ``IRegionGenerator``).
    """

    def __init__(self, region_generator: IRegionGenerator):
        self.region_generator = region_generator

    def generate_puzzle(self, spec: PuzzleSpecification) -> Optional[HexQueenPuzzle]:
        """
        Generate a puzzle that honours ``spec``.

        Returns None only if every one of ``spec.max_attempts`` attempts failed
        to produce a puzzle satisfying the requested guarantees.
        """
        grid = spec.grid
        rng = random.Random(spec.seed)

        for attempt in range(spec.max_attempts):
            if spec.queen_positions:
                queens = spec.queen_positions
            else:
                queens = self._place_queens(grid, spec.num_regions, rng)
                if not queens:
                    continue

            cell_regions = self.region_generator.generate_regions(grid, queens)
            if not cell_regions:
                continue

            if spec.require_unique or spec.require_logical:
                refiner = RegionRefiner(grid, queens, seed=rng.randint(0, 2**31),
                                        max_k=spec.max_difficulty)
                cell_regions = refiner.refine(cell_regions, require_logical=spec.require_logical)
                if cell_regions is None:
                    logger.debug("attempt %d: refinement failed", attempt)
                    continue

            puzzle = HexQueenPuzzle(grid, queens, cell_regions)
            if not puzzle.validate() or not RuleValidator.check_region_contiguity(grid, cell_regions):
                continue

            puzzle.difficulty = logical_solve(grid, cell_regions, max_k=4).difficulty
            return puzzle

        return None

    @staticmethod
    def _place_queens(grid: HexGrid, num_regions: int, rng: random.Random) -> Dict[int, HexCoord]:
        """Place mutually non-attacking queens; returns {} on failure."""
        placer = QueenPlacer(grid, num_regions, rng.randint(0, 2**31))
        if not placer.place_queens():
            return {}
        queens = placer.get_queen_positions()
        return queens if RuleValidator.check_queen_visibility(grid, queens) else {}


def generate_puzzle_with_queens(grid: HexGrid, seed: Optional[int] = None,
                                max_attempts: int = 20
                                ) -> Tuple[bool, HexGrid, Dict[HexCoord, int], Dict[int, HexCoord]]:
    """
    Convenience wrapper used by the page/PDF generator.

    Returns (success, grid, cell_regions, queen_positions).
    """
    from .growth_region_generator import GrowthRegionGenerator
    from .puzzle_visualizer import calculate_recommended_queens

    spec = PuzzleSpecification(
        grid=grid,
        num_regions=calculate_recommended_queens(grid.radius),
        seed=seed,
        max_attempts=max_attempts,
    )
    puzzle = PuzzleGenerator(GrowthRegionGenerator(seed)).generate_puzzle(spec)
    if puzzle is None:
        return False, grid, {}, {}
    return True, grid, puzzle.cell_regions, puzzle.queen_positions
