# HyProC2 glossary

HyProC simulates resonant nuclear reaction analysis (NRA) excitation curves for layered targets, so that a profiled element's depth profile can be fitted to a measured curve.

<!-- Format adapted from mattpocock-skills' domain-modeling (GLOSSARY-FORMAT.md): https://github.com/mattpocock/skills.git -->

<!--
How to add a term (the moment it is resolved, not in a batch at the end):

**Term**:
One or two sentences: what it IS, not what it does.
_Avoid_: the other words people use for it

- Be opinionated: one word per concept; list the others under _Avoid_.
- Only terms specific to this project. General programming concepts and
  implementation details don't belong here: this is a glossary, not a spec.
- Group terms under "### <area>" subheadings once natural clusters emerge.
-->

## Language

**Reaction config**:
The beam ion (Z1/A1), the profiled element (Z2/A2) and the resonance (E_R, Γ, σ) used to simulate one measurement. The standard and the experiment each have their own.
_Avoid_: settings, reaction (alone, when the resonance is meant too)

**Standard**:
A thick, single-layer reference sample of known composition whose measured yield calibrates the K factor.
_Avoid_: std, reference

**Experiment**:
The layered target being profiled, and the measured excitation curve that is fitted to it.
_Avoid_: sample, actual experiment

**K factor**:
The measured standard yield divided by the simulated standard yield. It is the setup's detection efficiency and applies to the experiment as is, even when the two reaction configs differ.
_Avoid_: calibration factor, efficiency
