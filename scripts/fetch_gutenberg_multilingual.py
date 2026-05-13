#!/usr/bin/env python3
"""
Inventaire des textes les plus traduits dans Gutenberg → nœuds data/texts/

Stratégie :
 - Télécharge le catalogue CSV officiel Project Gutenberg (pg_catalog.csv)
 - Identifie les œuvres canoniques par auteur + mots-clés de titre
 - Classe par nombre de langues distinctes par groupe
 - Pour chaque édition : download du texte brut, calcul de freq_signature

Usage :
  python3 scripts/fetch_gutenberg_multilingual.py [--top N] [--dry-run] [--no-text]
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

ATOM_LEXICON = {
    "ÊTRE": ["exist","existence","being","entity","essence","real","reality","presence","ontology","substance","soul","exister","présence","être","réalité","entité","existenz","sein","existe","ser","essere"],
    "DIFFÉRENCE": ["different","difference","other","another","various","distinct","distinction","contrary","contrast","otherwise","différent","différence","autre","sinon","contraire","verschieden","unterschied","otro","diferente","altro"],
    "RAPPORT": ["between","relation","ratio","proportion","among","link","connect","related","relationship","bond","against","rapport","entre","relation","lien","contre","verhältnis","relación","tra","rapporto"],
    "ORIENTATION": ["toward","into","move","direction","forward","away","through","path","aim","goal","vers","depuis","aller","direction","but","nach","richtung","hacia","verso"],
    "SUJET": ["person","agent","actor","subject","self","hero","soul","mind","individual","identity","personne","sujet","âme","individu","soi","mensch","individuum","persona","individuo","uomo"],
    "TEMPS": ["time","when","before","after","past","future","now","moment","duration","age","era","year","day","hour","temps","quand","avant","après","passé","futur","maintenant","zeit","wann","tiempo","cuando","tempo"],
    "MODALITÉ": ["possible","necessary","impossible","ought","allow","permit","permission","obligation","freedom","forbidden","duty","possible","nécessaire","obligation","liberté","devoir","möglich","notwendig","posible","necesario","possibile"],
    "NOMBRE": ["one","two","three","many","few","all","none","count","number","quantity","thousand","million","hundred","un","deux","trois","plusieurs","nombre","quantité","tous","viele","uno","dos","muchos","due"],
    "ESPACE": ["where","place","space","location","region","land","city","world","earth","sea","country","territory","où","lieu","espace","pays","monde","terre","wo","ort","raum","donde","lugar","dove","luogo"],
    "OPÉRATION": ["do","make","act","perform","create","produce","build","break","fight","attack","command","faire","agir","créer","produire","combattre","machen","tun","hacer","actuar","fare"],
    "FONCTION": ["function","role","purpose","use","serve","signify","name","call","word","term","define","represent","fonction","rôle","sens","signifier","nommer","définir","funktion","rolle","función","papel","funzione"],
    "STRUCTURE": ["structure","form","system","part","whole","order","body","law","rule","principle","pattern","organization","structure","forme","système","partie","tout","loi","struktur","sistema","struttura"],
    "SYMÉTRIE": ["same","equal","similar","symmetric","parallel","correspond","match","alike","together","common","même","égal","semblable","pareil","ensemble","commun","gleich","mismo","igual","stesso"],
    "ÉQUATION": ["equals","equation","formula","calculate","compute","solve","prove","theorem","logic","truth","correct","égale","équation","calculer","prouver","vrai","rechnen","igual","calcular","uguale"],
    "CAUSALITÉ": ["cause","because","therefore","result","effect","lead","produce","reason","why","thus","hence","since","car","parce","donc","cause","résultat","effet","raison","weil","wegen","porque","entonces","perché"],
    "ÉVÉNEMENT": ["event","happen","occur","incident","situation","battle","war","death","birth","arrival","fall","scene","événement","arriver","bataille","guerre","mort","ereignis","geschehen","evento","suceder"],
    "MENTAL_STATE": ["think","believe","know","feel","want","consciousness","perception","understand","fear","love","hate","hope","desire","penser","croire","savoir","sentir","vouloir","amour","denken","glauben","wissen","pensar","creer","pensare"],
}
ATOMS_V17 = list(ATOM_LEXICON.keys())

CANONICAL_GROUPS = [
    {"group": "shakespeare",     "author_kw": "shakespeare", "title_kws": ["hamlet","macbeth","othello","lear","midsummer","tempest","romeo","merchant","juliet"]},
    {"group": "goethe",          "author_kw": "goethe",      "title_kws": ["faust"]},
    {"group": "tolstoy",         "author_kw": "tolstoy",     "title_kws": ["war and peace","anna karenina","resurrection","guerre"]},
    {"group": "dante",           "author_kw": "dante",       "title_kws": ["inferno","divine comedy","divina commedia","purgatorio","paradiso"]},
    {"group": "hugo",            "author_kw": "hugo",        "title_kws": ["misérables","miserables","notre-dame","hunchback","travailleurs"]},
    {"group": "plato",           "author_kw": "plato",       "title_kws": ["republic","phaedo","symposium","apology","meno","timaeus","dialogues"]},
    {"group": "homer",           "author_kw": "homer",       "title_kws": ["iliad","odyssey","iliade","odyssée"]},
    {"group": "aristotle",       "author_kw": "aristotle",   "title_kws": ["nicomachean","poetics","politics","metaphysics"]},
    {"group": "cervantes",       "author_kw": "cervantes",   "title_kws": ["don quixote","quijote","don quichotte"]},
    {"group": "dostoevsky",      "author_kw": "dostoevsky",  "title_kws": ["crime","punishment","brothers karamazov","idiot"]},
    {"group": "kant",            "author_kw": "kant",        "title_kws": ["critique","kritik","practical reason","judgment"]},
    {"group": "descartes",       "author_kw": "descartes",   "title_kws": ["meditations","discourse","méthode"]},
    {"group": "spinoza",         "author_kw": "spinoza",     "title_kws": ["ethics","ethica","éthique"]},
    {"group": "voltaire",        "author_kw": "voltaire",    "title_kws": ["candide"]},
    {"group": "marcus_aurelius", "author_kw": "marcus aurelius", "title_kws": ["meditations"]},
    {"group": "aesop",           "author_kw": "aesop",       "title_kws": ["fables"]},
    {"group": "machiavelli",     "author_kw": "machiavelli", "title_kws": ["prince","principe"]},
    {"group": "rousseau",        "author_kw": "rousseau",    "title_kws": ["social contract","contrat social","confessions","emile"]},
    {"group": "virgil",          "author_kw": "virgil",      "title_kws": ["aeneid","énéide","aeneis"]},
    {"group": "ovid",            "author_kw": "ovid",        "title_kws": ["metamorphoses","métamorphoses"]},
]

CATALOG_URL   = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"
CATALOG_CACHE = Path("/tmp/pg_catalog.csv")

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "nipada-public/1.0 (github.com/stephanedenis/nipada-public; research)"


def slugify(text):
    nfkd = unicodedata.normalize("NFD", text.lower())
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_).strip("_")


def compute_freq_signature(text):
    text_lower = text.lower()
    counts = {}
    for atom, indicators in ATOM_LEXICON.items():
        score = sum(text_lower.count(f" {ind} ") for ind in indicators)
        counts[atom] = score
    total = sum(counts.values()) or 1
    return {atom: round(v / total, 4) for atom, v in counts.items()}


def load_catalog():
    if CATALOG_CACHE.exists():
        age_h = (time.time() - CATALOG_CACHE.stat().st_mtime) / 3600
        if age_h < 24:
            print(f"  📋 Catalogue local ({CATALOG_CACHE}, âge={age_h:.1f}h)")
            with open(CATALOG_CACHE, newline='', encoding='utf-8', errors='replace') as f:
                return list(csv.DictReader(f))
    print("  📥 Téléchargement pg_catalog.csv…")
    r = SESSION.get(CATALOG_URL, timeout=60)
    r.raise_for_status()
    CATALOG_CACHE.write_bytes(r.content)
    reader = csv.DictReader(io.StringIO(r.text))
    return list(reader)


def match_groups(catalog):
    groups = defaultdict(list)
    for row in catalog:
        if row.get("Type") != "Text":
            continue
        title   = row.get("Title",   "").lower()
        authors = row.get("Authors", "").lower()
        lang    = row.get("Language","").strip()
        bid_str = row.get("Text#",   "").strip()
        if not bid_str.isdigit():
            continue
        for grp in CANONICAL_GROUPS:
            if grp["author_kw"] not in authors:
                continue
            if any(kw in title for kw in grp["title_kws"]):
                groups[grp["group"]].append({
                    "id":      int(bid_str),
                    "title":   row.get("Title","").strip(),
                    "lang":    lang,
                    "authors": row.get("Authors","").strip(),
                })
    return dict(groups)


def rank_groups(groups):
    ranked = sorted(groups.items(), key=lambda x: -len({e["lang"] for e in x[1]}))
    return ranked


def fetch_text_content(book_id, max_chars=40000):
    for url in [
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
    ]:
        try:
            r = SESSION.get(url, timeout=25)
            if r.status_code == 200 and len(r.content) > 500:
                return r.content[:max_chars*2].decode("utf-8", errors="replace")[:max_chars]
        except Exception:
            continue
    return ""


def make_text_node(book, group, group_langs, freq_sig, version, stub):
    book_id = book["id"]
    slug = slugify(f"{group}_{book['lang']}_{book_id}")
    node = {
        "nipada_id": f"texts/{slug}",
        "type": "text",
        "mode": "distributed",
        "semantic": {
            "freq_signature": freq_sig,
            "atom_version": version,
            "atom_set": ATOMS_V17,
        },
        "meta": {
            "names": {book["lang"]: book["title"]},
            "scope": "public",
            "provenance": {
                "source": "gutenberg",
                "gutenberg_id": book_id,
                "language": book["lang"],
                "authors": book["authors"],
                "group": group,
                "group_languages": sorted(group_langs),
                "url": f"https://www.gutenberg.org/ebooks/{book_id}",
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "stub": stub,
            },
        },
    }
    return node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top",     type=int, default=15)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-text", action="store_true")
    ap.add_argument("--version", default="V17")
    ap.add_argument("--langs",   nargs="*")
    args = ap.parse_args()

    repo_root = Path(__file__).parent.parent
    out_dir   = repo_root / "data" / "texts"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"📚 Gutenberg multilingual — top {args.top} groupes")
    catalog = load_catalog()
    print(f"   {len(catalog):,} entrées")

    groups = match_groups(catalog)
    ranked = rank_groups(groups)

    print(f"\n  {'Rang':>4}  {'Groupe':<25} {'Langs':>5}  Langues")
    print("  " + "-" * 65)
    for rank, (group, editions) in enumerate(ranked, 1):
        langs = sorted({e["lang"] for e in editions})
        marker = " ← " if rank <= args.top else ""
        print(f"  {rank:>4}  {group:<25} {len(langs):>5}  {', '.join(langs[:8])}{'…' if len(langs)>8 else ''}{marker}")

    print()
    n_created = 0
    for group, editions in ranked[:args.top]:
        group_langs = sorted({e["lang"] for e in editions})
        print(f"  📖 {group}  ({len(group_langs)} langues)")
        for book in editions:
            if args.langs and book["lang"] not in args.langs:
                continue
            stub = True
            freq_sig = {}
            if not args.no_text and not args.dry_run:
                text = fetch_text_content(book["id"])
                time.sleep(0.5)
                if text:
                    freq_sig = compute_freq_signature(text)
                    stub = False
            if not freq_sig:
                freq_sig = {a: round(1.0/len(ATOMS_V17), 4) for a in ATOMS_V17}
            node = make_text_node(book, group, group_langs, freq_sig, args.version, stub)
            out_file = out_dir / f"text_gutenberg_{book['id']:06d}.json"
            dominant = max(freq_sig, key=freq_sig.get)
            if args.dry_run:
                print(f"    [{book['lang']:3}] [dry-run] {out_file.name}  dominant={'stub' if stub else dominant}")
            else:
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(node, f, ensure_ascii=False, indent=2)
                print(f"    [{book['lang']:3}] ✓  {out_file.name}")
                n_created += 1
        print()

    # Rapport
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "atom_version": args.version,
        "ranking": [
            {"group": g, "n_languages": len({e["lang"] for e in eds}),
             "languages": sorted({e["lang"] for e in eds}), "n_editions": len(eds)}
            for g, eds in ranked[:args.top]
        ],
    }
    report_path = repo_root / "data" / "gutenberg_multilingual_report.json"
    if not args.dry_run:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    mode = "[dry-run]" if args.dry_run else "live"
    print(f"✅  {mode}  {n_created} nœuds créés")
    if not args.dry_run:
        print(f"   Rapport → {report_path}")


if __name__ == "__main__":
    main()
