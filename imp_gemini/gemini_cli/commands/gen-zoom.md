# gen zoom
**Implements**: REQ-GRAPH-002, REQ-UX-003

## Usage
`gen zoom --edge <SOURCE\u2192TARGET>`

## Description
Zooms into a sub-graph of a specific edge or feature. In the Asset Graph Model, edges are not always atomic; they can represent a more complex sub-process.

## Example
- `gen zoom --edge "design\u2192code"` shows the path through `module_decomp` and `basis_proj`.

## Effects
- Visualizes the sub-graph for a given transition.
- Helps identify specific bottlenecks in a complex edge.
