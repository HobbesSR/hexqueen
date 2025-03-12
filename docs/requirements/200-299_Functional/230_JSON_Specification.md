# 230: JSON Output Specification

## 231: JSON Structure Overview

The JSON output format represents a hexagonal queen puzzle with its regions and queen positions. The puzzle is uniquely defined by the following elements:

- The grid radius (size of the hexagonal grid)
- The number of regions (equal to the number of queens)
- The queen positions (represented as region seeds)
- The mapping of all cells to their respective regions

```json
{
  "grid_radius": <int>,                   // Radius of the hexagonal grid
  "num_regions": <int>,                   // Number of regions/queens
  "region_seeds": {
    "<region_id>": [<x>, <y>, <z>],       // Queen position for each region in cube coordinates
    "...": [...]
  },
  "cell_regions": {
    "[<x>, <y>, <z>]": <region_id>,       // Mapping of cells to regions
    "...": ...
  }
}
```

## 232: Field Descriptions

- **grid_radius**: The radius of the hexagonal grid, determining its size.
- **num_regions**: The total number of regions in the puzzle, equal to the number of queens.
- **region_seeds**: Maps region IDs to the positions of their respective queens. Each queen serves as the "seed" from which a region grows in the puzzle generation process. Positions are represented as cube coordinate arrays [x, y, z].
- **cell_regions**: Maps cell positions to their region IDs. Cell positions are represented as string-formatted cube coordinates "[x, y, z]".

**Note:** The order of elements within JSON objects (e.g., `region_seeds`, `cell_regions`) is not guaranteed to be consistent. Consumers of the JSON output should not rely on a specific order.

## 233: Coordinate System
* Cube Coordinates representation where x + y + z = 0
* Each cell is uniquely identified by its three coordinate values