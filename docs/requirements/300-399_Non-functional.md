# 300-399: Non-functional Requirements

This section outlines the non-functional requirements for the HexQueen project, focusing on puzzle quality and performance.

## Puzzle Quality
<!-- Subsections could be added here later -->
Generated puzzles must be solvable, have a unique solution, and be solvable through logical deduction without brute-force methods.
Examples of logical deduction techniques include:
- Eliminating cells in the same row/column/diagonal as a placed queen.
- If a region's candidate cells are collinear in a row, eliminating other cells outside the region in that row.

## Performance
<!-- Subsections could be added here later -->
Puzzle generation should be reasonably fast for practical use. (Specific performance metrics to be defined if necessary)
*   **322: Generation Time Complexity:**
    *   Puzzle generation time should be polynomial with the puzzle radius.