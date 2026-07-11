# Third-Party Notices and Attribution

This project uses open-source software and references published research. The following information records the main upstream reference and runtime dependencies.

## SCoPP upstream reference

- Project: *Scalable Coverage Path Planning of Multi-Robot Teams for Monitoring Non-Convex Areas*
- Official repository: https://github.com/adamslab-ub/SCoPP
- Repository license: MIT License
- Paper: L. Collins, P. Ghassemi, S. Chowdhury, K. Dantu, E. Esfahani, and D. Doermann, ICRA 2021, arXiv:2103.14709
- Code reference used for parity review: `monitoring_algorithms.py` and `SCoPP_settings.py` from the upstream `main` branch

MICPP_INAIR keeps SCoPP behavior as a comparison and reproduction baseline while adding project-specific indoor planning features.

Project-specific adaptations include indoor Cartesian map handling, no-fly-zone geometry, executable transit constraints, KPI reporting, and experiment user interfaces.

The upstream SCoPP license and copyright information are available in its official repository.

## Runtime dependencies

The project installs and imports the following third-party Python packages rather than vendoring their source code:

- PyYAML
- Matplotlib
- NumPy
- scikit-learn
- Shapely

The test environment additionally uses pytest. Each dependency is distributed under the terms provided by its maintainers.
