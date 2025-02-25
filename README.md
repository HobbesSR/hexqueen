# Hexagonal Puzzle Solver

A Python implementation for generating and solving hexagonal grid-based puzzles with region expansion.

## Overview

This project implements a puzzle system where:
- Pieces are placed on a hexagonal grid
- Each piece has its own region that grows to cover parts of the board
- All regions together cover the entire board
- Each region is contiguous and contains exactly one piece
- The puzzle has a unique solution that can be found using logical techniques

## Features

- **Hexagonal Grid**: Uses cube coordinates for clean hexagonal grid operations
- **Puzzle Generation**: Creates regions for each piece and grows them until the entire board is covered
- **Solving Techniques**: Implements logical solving strategies like "hidden pairs" and "naked singles"
- **Recursive Solver**: Includes a backtracking solver with memoization for efficient solving
- **Visualization**: Provides visualization of puzzles and solutions using matplotlib

## Installation

### Requirements

- Python 3.7+
- Required packages:
  - matplotlib
  - numpy

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/hexagonal-puzzle-solver.git
cd hexagonal-puzzle-solver

# Install dependencies
pip install matplotlib numpy
```

## Usage

### Basic Usage

```python
from hex_grid import HexGrid
from puzzle_generator import PuzzleGenerator
from solver import PuzzleSolver

# Create a hexagonal grid with radius 3
grid = HexGrid(3)

# Generate a puzzle with 5 pieces
generator = PuzzleGenerator(grid, 5, seed=42)
generator.generate_puzzle()

# Solve the puzzle
solver = PuzzleSolver(grid, 5)
solver.initialize_from_clues(generator.piece_positions)
solver.solve()

# Get the solution
solution = solver.get_solution()
```

### Command Line Interface

The project includes a command-line interface for generating and solving puzzles:

```bash
python main.py --radius 3 --pieces 5 --seed 42
```

This will:
1. Generate a puzzle with the specified parameters
2. Visualize the generated puzzle and save it as "generated_puzzle.png"
3. Solve the puzzle using logical techniques and recursive solving
4. Visualize the solution and save it as "puzzle_solution.png"
5. Check if the solution is unique

## Components

### HexGrid

The `HexGrid` class manages the hexagonal grid using cube coordinates, which simplifies neighbor calculations and distance measurements.

Key features:
- Efficient neighbor calculation
- Distance measurement between cells
- Grid generation with specified radius

### PuzzleGenerator

The `PuzzleGenerator` class creates puzzles by:
1. Placing pieces randomly on the grid
2. Growing regions from each piece until the entire board is covered
3. Ensuring all regions are contiguous

Features:
- Configurable number of pieces
- Random seed for reproducibility
- Retry mechanism to handle failed generation attempts

### PuzzleSolver

The `PuzzleSolver` class implements various techniques to solve puzzles:

1. **Logical Techniques**:
   - Naked Singles: If a cell has only one possible region, assign it
   - Hidden Singles: If a region can only go in one cell in a local area, assign it
   - Hidden Pairs: If two cells can only have the same two regions, those regions must be in those cells

2. **Recursive Solver**:
   - Uses backtracking with memoization
   - Applies logical techniques at each step
   - Finds all solutions (or up to a specified limit)

3. **Contiguity Constraints**:
   - Ensures all regions remain contiguous during solving
   - Eliminates candidates that would break contiguity

## Challenges Addressed

### Infinite Recursion Prevention

The puzzle generator includes a retry count and maximum retries limit to prevent infinite recursion during puzzle creation. If a puzzle cannot be generated after a certain number of attempts, the generator gives up and reports failure.

### Logical Flow in Solving Functions

The solver implements a clean separation between different logical techniques, with each technique returning whether it made progress. The main solving loop applies techniques until no more progress is made, ensuring efficient solving.

### State Management

The recursive solver carefully manages state by:
- Saving and restoring the complete state before and after each recursive call
- Using memoization to avoid redundant work
- Maintaining consistent state for neighbors and candidates

### Efficiency Improvements

Several optimizations improve efficiency:
- Memoization in the recursive solver
- Minimum remaining values heuristic for cell selection
- Caching of neighbors in the HexGrid class
- Early termination when contradictions are found

## Visualization

The project includes visualization capabilities using matplotlib:
- Displays the hexagonal grid with regions colored differently
- Marks piece positions with special markers
- Saves visualizations as PNG files

## Future Improvements

Potential areas for enhancement:
- More advanced logical solving techniques
- Interactive GUI for puzzle solving
- Difficulty rating system for generated puzzles
- Optimization for larger grid sizes
- Additional puzzle constraints and variations

## License

[MIT License](LICENSE)