# Scientific review required before publication

The refactor preserves numerical models. Reference curves are regression tests,
not independent validation against experiments or published derivations. These
observations require a scientific decision before changing results.

## Layer segmentation can change total areal density

`stopping.assign_stopping` repeatedly halves a layer's density. It starts its
counter at 1, increments after each halving, then uses two daughters for one
halving and `(counter - 1) ** 2` daughters otherwise. Three halvings produce nine
daughters of one-eighth the original thickness: 112.5% of the initial total.
More halvings give other discrepancies.

`test_existing_layer_segmentation_arithmetic` reproduces this with synthetic
stopping `S(E) = E`, original density 0.04 TFU and energy 100 keV. The returned
density is 0.045 TFU. This law isolates arithmetic; it is not a physical model.

The algorithm mutates its input while constructing the result. The application
now protects callers with copies, leaving numerical behavior unchanged. A
correction needs approval and validation of thickness conservation, stopping
tolerances, beam exhaustion, and affected historical results.

## Comparison statistic

`yield_calc.chi_squared_test` returns mean squared yield difference, interpolating
onto measured energies and ignoring points outside that range. Experimental
uncertainties do not enter the formula. The GUI's “chi-squared” label and numerical
behavior remain. A weighted/reduced statistic is a separate scientific decision.

## Broadening diagnostics

`broadening.broadening` resets `layers_contribution` and `outOfTarget` inside the
loop over samples. Returned diagnostics reflect the last sample, despite the
docstring describing normalized contributions. Main yield calculation does not
use these outputs. They are retained pending review.

## Release evidence still needed

- Validate representative targets and both reaction configurations against
  independent experiments/reference calculations, including segmentation.
- Exercise real Windows SRIM. Adapter tests cover input/output and process
  directory isolation with a fake process, not executable physics or installation.
- Run the CI platform/Python matrix and interactive desktop acceptance on
  supported systems, including native dialogs and imports.
- Verify provenance and redistribution permission for `SCS-2025-solid.json`.
  Its metadata cites a 2024 article and a December 2025 submission but supplies
  no explicit data license. The repository GPL alone does not resolve this.
- Update the legacy PDF manual and establish a citation/versioned release
  record with maintainers. No DOI or publication readiness is claimed here.
