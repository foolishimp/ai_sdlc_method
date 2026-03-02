# gen trace
**Implements**: REQ-FEAT-001, REQ-TOOL-009

## Usage
`gen trace --key <REQ-ID>`

## Description
Shows the full traceability matrix for a specific requirement key (REQ key).

## Details
- Navigates forward from `intent` through `requirements`, `design`, `code`, `tests`, and `telemetry`.
- Navigates backward from production signals to the originating requirement.
- Displays the current status of each stage in the trajectory.
