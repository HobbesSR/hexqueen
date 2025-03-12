# 230: JSON Output Specification

## 231: JSON Structure
```json
{
  "grid_radius": <int>,
  "num_regions": <int>,
  "region_seeds": {
    "<region_id>": [<x>, <y>, <z>],  // Cube coordinates [x, y, z]
    "...": [...]
  },
  "cell_regions": {
    "[<x>, <y>, <z>]": <region_id>,  // Cube coordinates [x, y, z]
    "...": ...
  }
}
```

**Note:** The order of elements within JSON sets (e.g., `region_seeds`, `cell_regions`) is not guaranteed to be consistent. Consumers of the JSON output should not rely on a specific order.

## 232: Coordinate System
* Cube Coordinates representation where x + y + z = 0