# Design: make the alethiometer case thinner

The hands are now laser-cut from .015" spring steel instead of thicker brass,
which freed height under the crystal. Make the closed instrument as thin as the
design rules allow, and leave the model and the documents consistent.

`hardware/stack.py` is the stdlib Z stack-up and hinge model (an excerpt of the
CAD design module; `python hardware/stack.py` prints the derived report).
`hardware/README.md`, `hardware/BOM.md` and `hardware/ASSEMBLY.md` are the
customer-facing documents. All four files are writable.

Design rules and constraints:
- The hand-post standoff length must come from `STANDOFF_CATALOG`.
- Crystal clearance (crystal underside minus top of the hand cap) must be at
  least `MIN_CRYSTAL_CLEARANCE`.
- Every relief must clear the parts that enter it by `RELIEF_CLEARANCE`. A
  design review reported that one relief does not; find it and fix how its
  depth is derived from the parts that actually enter it. The geometry of
  those parts is documented next to the hinge constants in `stack.py`; the
  depth must follow from the constants, so it stays correct if the screw
  length or the clearance rule changes.
- Change nothing else: plate, gear-space, carrier, lid and sheet thicknesses
  and the hand stack heights are fixed by other parts.
- Every dimension the documents state for the changed parts and heights must
  match the model's value rounded half-up at the precision the document
  already uses: README heights and table and ASSEMBLY heights to 0.1 mm, the
  BOM flange to 0.1 mm, standoff and screw callouts in whole mm (e.g. a model
  value of 12.349 mm is written 12.3, not 12.4). Keep the documents' existing
  wording and layout otherwise.

Grading recomputes the stack from your constants, perturbs the hinge
constants, compares the report and the documents with the model, and checks
that the documents keep their wording, layout and every number not derived
from the changed parts. What `python hardware/stack.py` prints is not graded
beyond `report()`.

Read/write and tool/network boundaries are in policy.json. Offline Python 3
stdlib self-tests may help.


---
Work in `/app`. Only `/app/hardware/ASSEMBLY.md`, `/app/hardware/BOM.md`, `/app/hardware/README.md`, `/app/hardware/stack.py` are collected for grading (declared artifacts); the verifier runs separately with no network.
