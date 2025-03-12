# HexQueen Architecture v2

```mermaid
classDiagram
    direction BT
    
    class IRegionGenerator {
        <<interface>>
        +generate_regions(HexGrid, Dict[int, HexCoord]) Dict[HexCoord, int]
        +validate_regions(HexGrid, Dict[HexCoord, int]) bool
    }

    class HexGrid {
        +radius: int
        +get_all_cells() List[HexCoord]
        +get_neighbors(HexCoord) List[HexCoord]
    }

    class PuzzleSpecification {
        +queen_positions: Dict[int, HexCoord]
        +region_constraints: Dict
    }

    class HexQueenPuzzle {
        +grid: HexGrid
        +queen_positions: Dict[int, HexCoord]
        +cell_regions: Dict[HexCoord, int]
        +validate() bool
        +to_json() str
    }

    class PuzzleGenerator {
        -region_generator: IRegionGenerator
        +generate_puzzle(PuzzleSpecification) HexQueenPuzzle
    }

    class GrowthRegionGenerator {
        +generate_regions(HexGrid, Dict[int, HexCoord]) Dict[HexCoord, int]
        +validate_regions(HexGrid, Dict[HexCoord, int]) bool
    }

    class RuleValidator {
        +check_queen_visibility(HexGrid, Dict[int, HexCoord]) bool
        +check_region_contiguity(HexGrid, Dict[HexCoord, int]) bool
    }

    HexQueenPuzzle --> HexGrid
    PuzzleGenerator --> IRegionGenerator
    PuzzleGenerator --> PuzzleSpecification
    PuzzleGenerator --> HexQueenPuzzle
    GrowthRegionGenerator ..|> IRegionGenerator
    GrowthRegionGenerator --> RuleValidator
    GrowthRegionGenerator --> HexGrid