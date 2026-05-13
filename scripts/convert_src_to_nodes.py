#!/usr/bin/env python3
"""
Convert nipada src/ catalog (atoms, molecules, crossings) to data/ node_v1 format.

Usage:
    python3 scripts/convert_src_to_nodes.py [--version §272]

Reads  : src/atoms/*.json, src/molecules/**/*.json, src/crossings/*.json
Writes : data/atoms/*.json, data/molecules/*.json, data/crossings/*.json
Schema : schema/schema_node_v1.json
"""

import json
import unicodedata
import re
import argparse
from pathlib import Path

BASE    = Path(__file__).parent.parent
SRC     = BASE / "src"
DATA    = BASE / "data"
SCHEMA  = BASE / "schema" / "schema_node_v1.json"


# ── helpers ────────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    """Convert a French/Sanskrit/Greek name to an ASCII nipada_id slug."""
    nfd    = unicodedata.normalize("NFD", name)
    ascii_ = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", ascii_.lower()).strip("_")


def load_atoms_index() -> dict[int, str]:
    """Return {prime → French name} for factor-name lookup."""
    idx: dict[int, str] = {}
    for f in (SRC / "atoms").glob("*.json"):
        try:
            a = json.loads(f.read_text())
            if isinstance(a.get("id"), int) and a["id"] > 0:
                idx[a["id"]] = a["name"]
        except Exception:
            pass
    return idx


# ── converters ─────────────────────────────────────────────────────────────────

def atom_to_node(src: dict, version: str) -> dict:
    name  = src["name"]
    slug  = slugify(name)
    status = "canonical" if src.get("status") == "confirmed" else "hypothetical"

    meta: dict = {
        "names": {"fr": name},
        "scope": "public",
    }

    provenance: dict = {}
    if src.get("peirce"):   provenance["peirce"]   = src["peirce"]
    if src.get("jakobson"): provenance["jakobson"] = src["jakobson"]
    if src.get("dehaene"):  provenance["dehaene"]  = src["dehaene"]
    if src.get("uexkull"):  provenance["uexkull"]  = src["uexkull"]
    if src.get("convergences"): provenance["convergences"] = src["convergences"]
    if provenance: meta["provenance"] = provenance

    return {
        "$schema": "https://nipada.org/schema/node_v1.json",
        "nipada_id": f"atom/{slug}",
        "type": "atom",
        "version": version,
        "status": status,
        "meta": meta,
        "semantic": {
            "mode": "exact",
            "nipada_value": src["id"],
            "factors": [],
            "names": [name],
            "formula": name,
            "level": 0,
            "domain": "Z+",
        },
    }


def molecule_to_node(src: dict, atoms_idx: dict[int, str], version: str) -> dict:
    name   = src["name"]
    slug   = slugify(name)
    status = "canonical" if src.get("status", "confirmed") == "confirmed" else "draft"
    domain = src.get("domain", "Z")

    meta: dict = {
        "names": {"fr": name},
        "scope": "public",
    }
    if src.get("name_en"): meta["names"]["en"] = src["name_en"]
    if src.get("name_sa"): meta["names"]["sa"] = src["name_sa"]

    if src.get("examples"):
        meta["provenance"] = {"examples": src["examples"]}
    if src.get("convergences"):
        prov = meta.setdefault("provenance", {})
        prov["convergences"] = src["convergences"]

    factors      = src.get("factors", [])
    factor_names = [atoms_idx.get(f, str(f)) for f in factors]
    formula      = src.get("formula") or " ∧ ".join(factor_names)

    return {
        "$schema": "https://nipada.org/schema/node_v1.json",
        "nipada_id": f"molecule/{slug}",
        "type": "molecule",
        "version": version,
        "status": status,
        "meta": meta,
        "semantic": {
            "mode": "exact",
            "nipada_value": src["id"],
            "factors": factors,
            "names": factor_names,
            "formula": formula,
            "level": src.get("level", 1),
            "domain": "Z+",
        },
    }


def crossing_to_node(src: dict, atoms_idx: dict[int, str], version: str) -> dict:
    name  = src["name"]
    slug  = slugify(name)

    meta: dict = {
        "names": {"fr": name},
        "scope": "public",
    }
    if src.get("name_en"): meta["names"]["en"] = src["name_en"]
    if src.get("name_sa"): meta["names"]["sa"] = src["name_sa"]

    notes_parts = []
    if src.get("notes"):         notes_parts.append(src["notes"])
    if src.get("crossing_note"): notes_parts.append(f"[Spencer-Brown] {src['crossing_note']}")
    if notes_parts:              meta["notes"] = " | ".join(notes_parts)

    provenance: dict = {}
    if src.get("examples"):      provenance["examples"]     = src["examples"]
    if src.get("convergences"):  provenance["convergences"] = src["convergences"]
    if provenance: meta["provenance"] = provenance

    factors      = src.get("factors", [abs(src["id"])])
    factor_names = [atoms_idx.get(f, str(f)) for f in factors]
    formula      = src.get("formula") or f"crossing({' ∧ '.join(factor_names)})"

    return {
        "$schema": "https://nipada.org/schema/node_v1.json",
        "nipada_id": f"crossing/{slug}",
        "type": "crossing",
        "version": version,
        "status": "canonical",
        "meta": meta,
        "semantic": {
            "mode": "exact",
            "nipada_value": src["id"],
            "factors": factors,
            "names": factor_names,
            "formula": formula,
            "level": src.get("level", 0),
            "domain": "Z-",
        },
    }


# ── validation ─────────────────────────────────────────────────────────────────

def validate_node(node: dict, schema: dict) -> tuple[bool, str]:
    try:
        import jsonschema
        jsonschema.validate(node, schema)
        return True, "OK"
    except ImportError:
        return True, "jsonschema not installed — skipped"
    except jsonschema.ValidationError as e:
        return False, e.message


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Convert src/ to data/ node_v1")
    parser.add_argument("--version", default="§272", help="Research section reference")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    schema = json.loads(SCHEMA.read_text())
    atoms_idx = load_atoms_index()

    stats = {"atoms": 0, "molecules": 0, "crossings": 0, "errors": 0}

    # ── atoms ─────────────────────────────────────────────────────────────────
    out_dir = DATA / "atoms"
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted((SRC / "atoms").glob("*.json")):
        src = json.loads(f.read_text())
        if src.get("id", 0) <= 0:  # skip crossings accidentally in atoms/
            continue
        node = atom_to_node(src, args.version)
        ok, msg = validate_node(node, schema)
        slug = slugify(src["name"])
        out  = out_dir / f"atom_{slug}.json"
        print(f"  {'DRY' if args.dry_run else 'OK ':3s} atom/{slug}  ({msg})")
        if not ok:
            stats["errors"] += 1
        if not args.dry_run:
            out.write_text(json.dumps(node, ensure_ascii=False, indent=2))
        stats["atoms"] += 1

    # ── molecules ──────────────────────────────────────────────────────────────
    out_dir = DATA / "molecules"
    out_dir.mkdir(parents=True, exist_ok=True)
    for level_dir in sorted((SRC / "molecules").iterdir()):
        for f in sorted(level_dir.glob("*.json")):
            src = json.loads(f.read_text())
            if src.get("id", 0) <= 0:
                continue
            node = molecule_to_node(src, atoms_idx, args.version)
            ok, msg = validate_node(node, schema)
            slug = slugify(src["name"])
            out  = out_dir / f"molecule_{slug}.json"
            print(f"  {'DRY' if args.dry_run else 'OK ':3s} molecule/{slug}  ({msg})")
            if not ok:
                stats["errors"] += 1
            if not args.dry_run:
                out.write_text(json.dumps(node, ensure_ascii=False, indent=2))
            stats["molecules"] += 1

    # ── crossings ─────────────────────────────────────────────────────────────
    out_dir = DATA / "crossings"
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted((SRC / "crossings").glob("*.json")):
        src = json.loads(f.read_text())
        node = crossing_to_node(src, atoms_idx, args.version)
        ok, msg = validate_node(node, schema)
        slug = slugify(src["name"])
        out  = out_dir / f"crossing_{slug}.json"
        print(f"  {'DRY' if args.dry_run else 'OK ':3s} crossing/{slug}  ({msg})")
        if not ok:
            stats["errors"] += 1
        if not args.dry_run:
            out.write_text(json.dumps(node, ensure_ascii=False, indent=2))
        stats["crossings"] += 1

    print(f"\nDone: {stats['atoms']} atoms · {stats['molecules']} molecules · "
          f"{stats['crossings']} crossings · {stats['errors']} validation errors")


if __name__ == "__main__":
    main()
