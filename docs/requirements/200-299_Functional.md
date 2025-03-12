# 200-299: Functional Requirements

## 210: Puzzle Generation

*   **211: Puzzle Parameter:**
    *   Puzzles are generated based on a `radius` parameter, which determines the puzzle size and the number of queens.
*   **212: Puzzle Validity:**
    *   Generated puzzles must be valid HexQueen puzzles.
*   **213: Unique Solution:**
    *   Generated puzzles must have a unique solution.
*   **214: Logical Solvability:**
    *   Generated puzzles must be solvable using logical inferences.

## 220: Output Formats

*   **221: PNG Output:**
    *   Generate puzzle images in PNG format, with options for including or excluding the solution.
*   **222: PDF Output:**
    *   Generate puzzle documents in PDF format, allowing configuration of puzzles per page (rows and columns).
*   **223: JSON Output:**
    *   Generate puzzle data in JSON format for application integration.

## 230: JSON Output Specification

*   **231: JSON Structure:**
    ```json
    {
      "grid_radius": <int>,
      "num_regions": <int>,
      "region_seeds": {
        "<region_id>": [<x>, <y>, <z>],  // Cube coordinates [x, y, z]
        "...": [...]
      },
      "cell_regions": {
        " [<x>, <y>, <z>]": <region_id>, // Cube coordinates [x, y, z]
        "...": ...
      }
    }
    ```
*   **232: Coordinate System:**
    *   Cube Coordinates are used to represent hexagonal grid cells. Each cell is identified by three coordinates [x, y, z] where x + y + z = 0.