"""Tests for the HexQueen generation pipeline. Run with: python -m unittest discover tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.growth_region_generator import GrowthRegionGenerator
from src.hex_grid import HexGrid, HexCoord
from src.hex_queen_puzzle import HexQueenPuzzle
from src.interfaces import PuzzleSpecification
from src.puzzle_generator import PuzzleGenerator
from src.queen_placer import QueenPlacer
from src.rule_validator import RuleValidator
from src.solver import count_solutions, find_solutions, logical_solve


def make_puzzle(radius, seed, **spec_kwargs):
    grid = HexGrid(radius)
    spec = PuzzleSpecification(grid=grid, num_regions=2 * radius + 1, seed=seed, **spec_kwargs)
    return PuzzleGenerator(GrowthRegionGenerator(seed)).generate_puzzle(spec)


class TestGrid(unittest.TestCase):
    def test_cell_count(self):
        for r in range(1, 6):
            self.assertEqual(len(HexGrid(r).get_all_cells()), 3 * r * (r + 1) + 1)


class TestQueenPlacer(unittest.TestCase):
    def test_placement_is_valid_and_seeded(self):
        for r in (2, 3, 4, 5):
            grid = HexGrid(r)
            runs = []
            for _ in range(2):
                placer = QueenPlacer(grid, 2 * r + 1, seed=7)
                self.assertTrue(placer.place_queens())
                queens = placer.get_queen_positions()
                self.assertEqual(len(queens), 2 * r + 1)
                self.assertTrue(RuleValidator.check_queen_visibility(grid, queens))
                runs.append(queens)
            self.assertEqual(runs[0], runs[1], "same seed must give same queens")


class TestSolver(unittest.TestCase):
    def test_counts_multiple_solutions(self):
        # Raw layouts are often ambiguous; the solver must report every solution
        # and each one must be a legal queen placement.
        for seed in range(40):
            raw = make_puzzle(2, seed, require_unique=False, require_logical=False)
            sols = find_solutions(raw.cell_regions, limit=None)
            if len(sols) > 1:
                self.assertEqual(count_solutions(raw.cell_regions, limit=None), len(sols))
                self.assertEqual(count_solutions(raw.cell_regions, limit=2), 2)  # early stop
                for sol in sols:
                    self.assertTrue(RuleValidator.check_queen_visibility(raw.grid, sol))
                    self.assertTrue(all(raw.cell_regions[c] == r for r, c in sol.items()))
                return
        self.fail("expected at least one ambiguous raw layout in 40 seeds")

    def test_unsolvable_layout_has_zero_solutions(self):
        grid = HexGrid(1)
        a, b = HexCoord(0, 0, 0), HexCoord(0, 1, -1)   # share x=0, so can't both hold queens
        regions = {c: 2 for c in grid.get_all_cells()}
        regions[a], regions[b] = 0, 1
        self.assertEqual(count_solutions(regions, limit=None), 0)
        result = logical_solve(grid, regions)
        self.assertFalse(result.solved)
        self.assertTrue(result.contradiction)


class TestGuarantees(unittest.TestCase):
    """The headline requirements: valid, unique, logically solvable."""

    def test_generated_puzzles_are_unique_and_logical(self):
        for radius in (2, 3, 4, 5):
            for seed in range(5):
                with self.subTest(radius=radius, seed=seed):
                    puzzle = make_puzzle(radius, seed)
                    self.assertIsNotNone(puzzle)
                    self.assertTrue(puzzle.validate())
                    self.assertTrue(RuleValidator.check_region_contiguity(puzzle.grid, puzzle.cell_regions))
                    self.assertEqual(count_solutions(puzzle.cell_regions), 1)
                    result = logical_solve(puzzle.grid, puzzle.cell_regions)
                    self.assertTrue(result.solved)
                    self.assertEqual(result.solution, puzzle.queen_positions)
                    self.assertEqual(puzzle.difficulty, result.difficulty)

    def test_logical_solver_never_contradicts_exhaustive_solver(self):
        # Raw (unrefined) layouts: whenever logic claims a solve, it must be the unique one.
        for seed in range(25):
            grid = HexGrid(3)
            puzzle = make_puzzle(3, seed, require_unique=False, require_logical=False)
            result = logical_solve(grid, puzzle.cell_regions)
            if result.solved:
                self.assertEqual(count_solutions(puzzle.cell_regions), 1)
                self.assertEqual(result.solution, puzzle.queen_positions)

    def test_difficulty_cap_is_respected(self):
        puzzle = make_puzzle(4, seed=2, max_difficulty=1)
        self.assertIsNotNone(puzzle)
        self.assertEqual(puzzle.difficulty, 1)

    def test_seed_is_reproducible(self):
        a, b = make_puzzle(4, seed=11), make_puzzle(4, seed=11)
        self.assertEqual(a.cell_regions, b.cell_regions)
        self.assertEqual(a.queen_positions, b.queen_positions)

    def test_json_round_trip(self):
        puzzle = make_puzzle(3, seed=5)
        again = HexQueenPuzzle.from_json(puzzle.to_json())
        self.assertEqual(again.cell_regions, puzzle.cell_regions)
        self.assertEqual(again.queen_positions, puzzle.queen_positions)
        self.assertEqual(again.difficulty, puzzle.difficulty)


if __name__ == "__main__":
    unittest.main()
