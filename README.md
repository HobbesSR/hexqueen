# HexQueen Puzzle Generator and Queen Placer

## Overview
HexQueen is a comprehensive puzzle generation project that creates engaging hexagonal grid puzzles. It includes modules for generating puzzles with unique solutions, placing queens on the grid so that no two threaten each other, and rendering puzzle pages for both digital viewing and printable output. Features include:
- Generating hexagonal grids using cube coordinates.
- Creating puzzles with region growth.
- Ensuring contiguity of regions and a logical solution.
- Strategic queen placement using random or backtracking methods.
- Generating puzzle pages as images and PDFs with multiple puzzles per sheet.

## Hexagonal Grid (hex_grid.py)
The HexGrid module provides the infrastructure for managing a hexagonal grid using cube coordinates (where x + y + z = 0). It includes capabilities to generate grid cells, determine neighbors, and calculate distances.

## Puzzle Generation (puzzle_generator.py)
This module creates puzzles on a hexagonal grid ensuring a unique and logically solvable layout. Key functionalities include:
- Puzzle generation with region growth.
- Ensuring contiguity of regions.
- Validating the uniqueness and solvability of puzzles.

## Queen Placement (queen_placer.py)
The Queen Placer module strategically positions queens on the grid so that no two queens can attack each other. It features:
- Random queen placements that adhere to non-attacking constraints.
- A backtracking approach if initial placements fail.
- Functions to determine available cells and update attack zones.

## Puzzle Page Generation (puzzle_page_generator.py)
This module generates visual representations of puzzles and their solutions. It supports:
- Rendering puzzles on an 8x11 inch page using matplotlib.
- Generating solution pages that display the completed puzzle with pieces or queens.
- Batch generation of puzzle pages.
- Optional PDF generation featuring multiple puzzles per sheet.

## Usage Examples

### Puzzle Generation and Queen Placement
```python
from hex_grid import HexGrid
from puzzle_generator import PuzzleGenerator
from queen_placer import QueenPlacer

# Generate a puzzle
grid = HexGrid(radius=5)
generator = PuzzleGenerator(grid, num_pieces=4, seed=42)
if generator.generate_puzzle():
    puzzle = generator.get_puzzle_state()
    print("Generated Puzzle:", puzzle)
else:
    print("Failed to generate a valid puzzle.")

# Place queens on the grid
placer = QueenPlacer(grid, num_queens=4, seed=42)
if placer.place_queens():
    queens = placer.get_queen_positions()
    print("Queen Positions:", queens)
else:
    print("Failed to place queens without conflicts.")
```

### Puzzle Page Generation and PDF Output
Run the puzzle page generator from the command line:
```bash
python puzzle_page_generator.py --num_puzzles 3 --grid_radius 3 --output output_folder --seed 1234
```
For PDF output with multiple puzzles per page, add the `--pdf` flag along with `--rows` and `--columns`:
```bash
python puzzle_page_generator.py --num_puzzles 6 --grid_radius 3 --output output_folder --seed 1234 --pdf --rows 2 --columns 3
```

### Main Script Usage
The main script (`main.py`) serves as the entry point for running HexQueen. To display the available options, run:
```bash
python main.py --help
```
You can customize command line arguments to run different components of the project.

For internal tracking of agent goals and in-progress tasks, refer to the [AGENT_README.md](AGENT_README.md) file, which serves as a scratch pad for AI agent task management.

## Testing and Validation
Run the tests using:
```bash
python -m unittest test.py
```

## Dependencies
Refer to `requirements.txt` for the list of required packages, including matplotlib and numpy.

## Contributing
Contributions are welcome. Fork the repository and submit pull requests to enhance puzzle generation, queen placement strategies, and page rendering functionalities.

## License
This project is licensed under the MIT License.