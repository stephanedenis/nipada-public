# NIPADA Changelog

All notable changes to the NIPADA encyclopedic node graph.

## [Unreleased]

### Added
- `schema/schema_node_v1.json` — JSON Schema draft-07 for the universal encyclopedic node model
  - 3 semantic modes: `exact` (prime encoding), `distributed` (V14–V17 freq_signature), `hybrid`
  - 26 controlled relation types + causality taxonomy (logique/physique/téléologique/stochastique)
  - Overlay architecture: public stub + private `overlay_repo` pointer
- `examples/nodes/molecule_195_causalite.json` — canonical `exact` mode example (§103)
- `examples/nodes/text_aristotle_nicomachean_ethics.json` — canonical `distributed` mode example (§243)
- `examples/nodes/concept_dharma.json` — canonical `hybrid` mode example (§243)
- Initial atom catalog from Panini-Research v280 (5 atoms, 12 molecules, 15 crossings)
- `schema/schema_signed_v1.json` — signed corpus schema (V14/V16/V17 compatible)

---

*Versioning follows research sections (§NNN) from Panini-Research.*  
*Schema IDs: `https://nipada.org/schema/node_v1.json`*
