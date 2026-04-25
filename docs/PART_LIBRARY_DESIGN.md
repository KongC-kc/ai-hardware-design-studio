# Part Library Design

The part library is intentionally small in V1. Blocks can use placeholder parts such as `PLACEHOLDER_FPGA` while the pipeline is being proven.

## Future Sources

- Local curated part database in `packages/parts/db`
- KiCad symbol and footprint references in `packages/parts/kicad`
- LCEDA import adapters in `packages/parts/lceda`

## Part Record Goals

A future part record should include:

- Stable part ID
- Manufacturer part number
- Symbol alias
- Footprint alias
- Pin map
- Electrical pin types
- Power pins
- Required passives
- Lifecycle and availability metadata

## Design Rule Integration

Parts should expose rule hooks for required decoupling, oscillator load components, termination, pull-ups, USB protection, and power sequencing.
