# Contributing to NIPADA

Thank you for contributing to the NIPADA knowledge graph.

## What lives here

| Contribution type | Target directory | Schema |
|---|---|---|
| New atom or molecule definition | `src/atoms/` or `src/molecules/levelN/` | `src/index.json` entry required |
| New encyclopedic node (concept, tradition, period…) | `data/<type>/` | `schema/schema_node_v1.json` |
| New public-domain text node | `data/texts/` | `schema/schema_node_v1.json` |
| Schema improvement | `schema/` | Requires semver bump in `$id` |

## Node naming convention

Node files use the pattern: `{type}_{id}.json`

- `concept_logos.json`
- `text_bhagavad_gita.json`
- `person_nagarjuna.json`
- `tradition_madhyamaka.json`

The `nipada_id` inside the file must match: `{type}/{id}` → `concept/logos`, `text/bhagavad_gita`.

## Semantic mode selection

| Node type | Mode |
|---|---|
| atom, molecule, crossing | `exact` |
| text, person, place, event | `distributed` |
| concept, tradition, language, period | `hybrid` |

## Validation

Validate your node before submitting:

```bash
pip install jsonschema
python3 -c "
import json, jsonschema
schema = json.load(open('schema/schema_node_v1.json'))
node   = json.load(open('data/concepts/concept_dharma.json'))
jsonschema.validate(node, schema)
print('OK')
"
```

## Relation types

The controlled vocabulary for `relations[].type` is defined in the schema.
26 types are available: `authored_by`, `derived_from`, `cites`, `analogous_to`, `causes`, `part_of`, `belongs_to`, etc.

Relations that carry causal weight (`causes`, `caused_by`, `influenced_by`, `influenced`) **must** include a `causal_category` field: `logique | physique | teleologique | stochastique`.

## Version references

Every node must reference the research section that canonized it:

```json
"version": "§103"
```

See the [Panini-Research](https://github.com/stephanedenis/Panini-Research) session journals for section numbers.

## Pull requests

1. Fork the repo.
2. Add or modify nodes in `data/`.
3. Validate against the schema (see above).
4. Open a PR with a brief description of the semantic rationale for the node.
