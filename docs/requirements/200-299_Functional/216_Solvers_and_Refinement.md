# 216: Solvers and Refinement

## 216.1: Exhaustive Solver
* `solver.count_solutions` / `find_solutions` enumerate puzzle solutions (region -> queen cell) with early exit at a limit.
* A puzzle is unique iff the count is exactly 1 (satisfies 213).

## 216.2: Logical Solver
* `solver.LogicalSolver` solves by deduction only, using two patterns parameterised by set size *k*:
  * **Region set**: *k* regions confined to *k* lines of one axis exclude those lines for all other regions.
  * **Line set**: *k* lines of one axis fed by only *k* regions pin those regions to those lines.
* Every axis has exactly 2r+1 lines and there are 2r+1 queens, so each line holds exactly one queen.
* The smallest *k* that makes progress is always used; the largest *k* needed is the puzzle's **difficulty** (1-4).
* A puzzle the logical solver completes satisfies 214.

## 216.3: Region Refinement
* `region_refiner.RegionRefiner` moves single boundary cells between adjacent regions (never a queen cell, never breaking contiguity, minimum region size 2).
* Phase 1 minimises extra solutions; phase 2 keeps uniqueness while minimising undeduced candidates.
* Sideways moves are accepted to cross plateaus. Generation retries with fresh queens if a run fails.

## 216.4: Parameters
* `PuzzleSpecification.require_unique`, `require_logical`, `max_difficulty` (1-4), `max_attempts`.
