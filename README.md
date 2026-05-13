# NIPADA — Universal Encyclopedic Knowledge Graph

**An open encyclopedia where every concept has a mathematically grounded semantic identity.**

Part of the [Panini research project](https://github.com/stephanedenis/Panini-Research) — fundamental research on the universal structure of meaning.

---

## What is NIPADA?

NIPADA encodes human knowledge — texts, persons, places, events, concepts, traditions — as a **typed graph** where every node carries a **semantic signature** derived from a small set of prime-number-based universal atoms.

The foundational idea: the Fundamental Theorem of Arithmetic guarantees that every product of distinct primes is unique and irreducible. Assign a prime to each irreducible semantic atom, and every concept gets an integer identity that is:

- **Unique** — no two different meanings share the same integer
- **Decomposable** — factor the integer to recover the constituent atoms
- **Composable** — multiply atoms to build new molecules

### The 4 primordial atoms (compact system)

| Prime | Atom | Meaning |
|---|---|---|
| 2 | ÊTRE (BEING) | existence — "there is X" |
| 3 | DIFFÉRENCE (DIFFERENCE) | distinction — "X ≠ Y" |
| 5 | RAPPORT (RELATION) | link — "X relates to Y" |
| 7 | ORIENTATION | direction — "toward / from" |

**Example molecules:**
- EXISTENCE = 2 × 3 = **6** — differentiated being ("X exists as something particular")
- REFERENCE = 5 × 7 = **35** — oriented relation ("pointing to")
- INTEGRATION = 2 × 3 × 5 × 7 = **210** — being, differentiated, related, and oriented

### Extended vocabulary (V14–V17)

For full-text semantic signatures, 14–17 atoms cover the complete range of human expression including mathematical, physical, and mental concepts. See [`src/index.json`](src/index.json).

---

## Repository structure

```
nipada-public/
│
├── schema/
│   ├── schema_node_v1.json       ← Universal encyclopedic node schema (JSON Schema draft-07)
│   └── schema_signed_v1.json     ← Corpus signed-signature schema (V14/V16/V17 compatible)
│
├── src/                          ← Foundational atom catalog (canonical)
│   ├── index.json                ← Master catalog: 34 confirmed entries + 1 hypothesis
│   ├── atoms/                    ← 4 primordial atoms (ÊTRE, DIFFÉRENCE, RAPPORT, ORIENTATION)
│   ├── molecules/
│   │   ├── level1/               ← 2-atom compositions (EXISTENCE, MESURE, DEVENIR…)
│   │   ├── level2/               ← 3-atom compositions (VIE, TRANSFORMATION, INTENTION…)
│   │   └── level3/               ← 4-atom composition (INTÉGRATION)
│   └── crossings/                ← Spencer-Brown negations (NÉANT, RUPTURE, DÉRIVE…)
│
├── data/                         ← Encyclopedic nodes (growing)
│   ├── atoms/                    ← Atom nodes (wrapping src/atoms/ in node format)
│   ├── molecules/                ← Molecule nodes
│   ├── concepts/                 ← Concept nodes (dharma, logos, tao…)
│   ├── languages/                ← Language nodes
│   ├── traditions/               ← Intellectual tradition nodes
│   ├── periods/                  ← Historical period nodes
│   ├── places/                   ← Geographic nodes
│   └── texts/                    ← Public-domain text nodes
│
└── examples/
    └── nodes/                    ← 3 canonical node examples (one per semantic mode)
```

---

## Node model

Every encyclopedic entry is a JSON file conforming to [`schema/schema_node_v1.json`](schema/schema_node_v1.json).

Three semantic modes:

| Mode | For | Key field |
|---|---|---|
| `exact` | atoms, molecules, crossings | `nipada_value` (prime product) |
| `distributed` | texts, persons, places, events | `freq_signature` (V14–V17 distribution) |
| `hybrid` | concepts, traditions | both |

See [`examples/nodes/`](examples/nodes/) for one example of each mode.

---

## Overlay architecture

NIPADA uses a **public/private layering** model:

- **nipada-public** (this repo) — public domain knowledge, open schemas, atom catalog. Published at nipada.org.
- **nipada-private-[org]** — private overlay repos augmenting public nodes with copyrighted or confidential content. Not distributed.

A public node with `content.stub: true` is a placeholder — its semantic identity and relations are public, but the full content lives in a private overlay repo.

---

## License

- **Schemas** (`schema/`): [CC0-1.0](LICENSE) — no rights reserved, use freely.
- **Atom catalog** (`src/`): [CC0-1.0](LICENSE)
- **Encyclopedic nodes** (`data/`, `examples/`): [CC0-1.0](LICENSE) unless otherwise noted in individual files.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Related projects

| Project | Description |
|---|---|
| [Panini-Research](https://github.com/stephanedenis/Panini-Research) | Research repository — corpus, experiments, falsification program |
| PaniniFS | Content-Addressed Storage system for semantic file decomposition |
| PanLang | Constructed language built on NIPADA atoms (forthcoming) |
| ontowave.org | Public-facing visualization of the NIPADA knowledge graph (forthcoming) |
