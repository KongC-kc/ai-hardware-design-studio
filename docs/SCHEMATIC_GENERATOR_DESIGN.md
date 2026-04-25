# Schematic Generator Design

The schematic generator compiles hardware design IR into KiCad schematic artifacts.

## V1 Mock Generator

The V1 generator writes a minimal deterministic schematic file with:

- Project metadata
- Block summaries
- Power tree comments
- Logical connection comments

This is not a complete production KiCad schematic writer. It exists to prove the project pipeline, file ownership, and deterministic generation boundary.

## Future Generator Responsibilities

- Resolve block types to concrete KiCad symbols.
- Map logical pins to symbol pins.
- Place symbols deterministically by block groups.
- Create labels and net names.
- Add power symbols and power flags.
- Insert decoupling placeholders or generated capacitors.
- Split large designs into hierarchical sheets.
- Preserve reproducibility across repeated runs.

## Source of Truth

The source of truth is the IR. If a generated schematic is wrong, fix the IR, schema, templates, part mappings, or generator code.
