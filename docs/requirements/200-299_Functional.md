# 200-299: Functional Requirements

This section details the functional requirements for the HexQueen project, covering puzzle generation, output formats, and JSON specification.

## Puzzle Generation
[See detailed requirements in 210_Puzzle_Generation.md](200-299_Functional/210_Puzzle_Generation.md)
Puzzles are generated based on a `radius` parameter. They must be valid HexQueen configurations, have a unique solution, and be solvable using logical inferences.

## Output Formats
[See detailed requirements in 220_Output_Formats.md](200-299_Functional/220_Output_Formats.md)
The system should generate puzzles in PNG image format (with solution toggle), PDF document format (configurable puzzles per page), and JSON format for application integration.

## JSON Specification
[See detailed requirements in 230_JSON_Specification.md](200-299_Functional/230_JSON_Specification.md)
Puzzle data is exported in JSON format, including grid radius, number of regions, queen positions (as region seeds), and cell-to-region mappings, using a cube coordinate system. The "region seeds" represent the positions of queens, which serve as the starting points from which regions grow during puzzle generation.

## Import and Visualization from JSON
The system should be able to import a puzzle from a JSON file and visualize it. The visualization should accurately represent the puzzle's grid, regions, and queen placements.