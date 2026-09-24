# Tactile and Vision-Language-Action Robotics

A structured bibliography for tactile sensing, visuo-tactile learning, robot foundation models, and vision-language-action (VLA) policies.

## Contents

- [Paper index](papers/index.csv)
- [Tactile-VLA and multimodal policies](papers/tactile-vla.md)
- [Tactile representation and sensing](papers/tactile-representation.md)
- [Tactile manipulation and control](papers/tactile-manipulation.md)
- [Robot foundation models and VLA](papers/vla-foundations.md)
- [Datasets, benchmarks, and surveys](papers/datasets-benchmarks.md)
- [Paper interpretations](paper-interpretations/README.md)
- [BibTeX](sources/references.bib)

Each entry contains bibliographic metadata and a primary publication link. Publication type is recorded as `conference`, `journal`, or `preprint`. Conference and journal labels follow the linked publication record.

## Scope

The bibliography covers:

- tactile-conditioned VLA and visuo-tactile-language-action policies;
- tactile representation learning and optical tactile sensing;
- contact-rich and dexterous manipulation;
- robot foundation models and generalist policies used as VLA backbones;
- robot datasets, benchmarks, and surveys relevant to tactile manipulation.

## Paper interpretations

Detailed Chinese interpretations are maintained separately from the bibliography in
[`paper-interpretations/`](paper-interpretations/README.md). Each document explains
the paper's problem, method, innovations, improvements over prior work, experimental
evidence, accumulated insights, limitations, and reproducibility considerations.
Every new interpretation is synchronized to that directory, its README, the relevant
topic page, `papers/index.csv`, and `sources/references.bib` before being pushed.
The current Force-aware VLA sequence includes ForceVLA (force-aware fusion), FAVLA
(adaptive fast-slow execution), ForceDelta-VLA (force/delay correction distillation),
and ImplicitRDP (end-to-end causal slow-fast diffusion).

## Citation policy

Links point to arXiv, publisher, proceedings, or official project pages. The repository stores metadata and links rather than paper PDFs.
