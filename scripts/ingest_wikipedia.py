#!/usr/bin/env python3
"""
Ingestion Wikipedia → nœuds data/texts/ NIPADA (test de pipeline à l'échelle)

Stratégie :
 - Liste de catégories sémantiques (philosophie, linguistique, mathématiques, etc.)
 - Pour chaque catégorie, liste d'articles Wikipedia avec les langues disponibles
 - Téléchargement des extraits via l'API Wikipedia REST (multilingue)
 - Calcul de freq_signature V17 par lexique sémantique
 - Création de nœuds data/texts/ en mode distributed

Usage :
  python3 scripts/ingest_wikipedia.py [--langs en fr de] [--limit 50] [--dry-run]

Dépendances : requests (pip install requests)
Sortie : data/texts/text_wikipedia_<lang>_<slug>.json
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

# ---------------------------------------------------------------------------
# Lexique sémantique V17 — même que fetch_gutenberg_multilingual.py
# ---------------------------------------------------------------------------
ATOM_LEXICON: dict[str, list[str]] = {
    "ÊTRE": [
        "exist", "existence", "being", "entity", "essence", "real", "reality",
        "presence", "ontology", "substance", "exists",
        "exister", "existence", "présence", "être", "réalité", "entité",
    ],
    "DIFFÉRENCE": [
        "different", "difference", "other", "various", "distinct",
        "distinction", "contrary", "contrast", "otherwise", "nor",
        "différent", "différence", "autre", "contraire", "distinct",
    ],
    "RAPPORT": [
        "between", "relation", "ratio", "proportion", "with", "among", "link",
        "connect", "related", "relationship", "toward",
        "rapport", "entre", "relation", "lien",
    ],
    "ORIENTATION": [
        "toward", "from", "into", "out", "direction", "forward", "away",
        "through", "path", "aim", "goal",
        "vers", "depuis", "direction",
    ],
    "SUJET": [
        "who", "person", "agent", "actor", "subject", "self", "man", "woman",
        "people", "soul", "human", "individual",
        "personne", "sujet", "âme", "humain",
    ],
    "TEMPS": [
        "time", "when", "before", "after", "past", "future", "now", "moment",
        "duration", "age", "era", "year", "century", "period", "history",
        "temps", "quand", "avant", "après", "passé", "futur", "siècle",
    ],
    "MODALITÉ": [
        "can", "must", "should", "would", "may", "might", "could", "shall",
        "possible", "necessary", "impossible",
        "peut", "doit", "faut", "possible", "nécessaire",
    ],
    "NOMBRE": [
        "one", "two", "three", "many", "few", "all", "count", "number",
        "quantity", "much", "more", "less", "first", "second",
        "nombre", "quantité", "plusieurs",
    ],
    "ESPACE": [
        "where", "place", "space", "here", "there",
        "location", "region", "land", "world", "earth",
        "lieu", "espace", "monde", "pays",
    ],
    "OPÉRATION": [
        "do", "make", "act", "perform", "process", "create", "produce",
        "build", "develop", "write", "form",
        "faire", "agir", "créer", "produire",
    ],
    "FONCTION": [
        "function", "role", "purpose", "use", "serve", "mean", "represent",
        "define", "term", "concept", "meaning",
        "fonction", "rôle", "sens", "signifier",
    ],
    "STRUCTURE": [
        "structure", "form", "system", "part", "whole", "order", "organize",
        "consist", "contains", "law", "rule", "principle",
        "structure", "forme", "système", "partie",
    ],
    "SYMÉTRIE": [
        "same", "equal", "like", "similar", "parallel", "correspond", "match",
        "common", "share", "equivalent", "both",
        "même", "égal", "semblable", "commun",
    ],
    "ÉQUATION": [
        "equals", "equation", "formula", "calculate", "compute", "prove",
        "theorem", "logic", "truth", "correct", "defined", "denoted",
        "égale", "équation", "calculer", "prouver",
    ],
    "CAUSALITÉ": [
        "cause", "because", "therefore", "result", "effect", "lead",
        "produce", "reason", "thus", "hence", "since", "due",
        "car", "parce", "donc", "cause", "résultat",
    ],
    "ÉVÉNEMENT": [
        "event", "happen", "occur", "incident", "battle", "war",
        "death", "birth", "found", "established", "published",
        "événement", "guerre", "mort", "fondé",
    ],
    "MENTAL_STATE": [
        "think", "believe", "know", "feel", "want", "mind", "consciousness",
        "understand", "fear", "love", "idea", "thought", "perception", "argue",
        "penser", "croire", "savoir", "sentir", "esprit", "idée",
    ],
}

ATOMS_V17 = list(ATOM_LEXICON.keys())

# ---------------------------------------------------------------------------
# Articles Wikipedia par catégorie sémantique
# Format : {"title_en": ..., "fr": ..., "de": ..., "es": ..., "it": ...}
# On utilise le titre anglais comme pivot + titres dans les autres langues
# ---------------------------------------------------------------------------
WIKIPEDIA_ARTICLES: list[dict] = [
    # Philosophie antique
    {"title_en": "Plato",             "fr": "Platon",          "de": "Platon",      "es": "Platón"},
    {"title_en": "Aristotle",         "fr": "Aristote",        "de": "Aristoteles", "es": "Aristóteles"},
    {"title_en": "Socrates",          "fr": "Socrate",         "de": "Sokrates",    "es": "Sócrates"},
    {"title_en": "Epicurus",          "fr": "Épicure",         "de": "Epikur"},
    {"title_en": "Stoicism",          "fr": "Stoïcisme",       "de": "Stoa"},
    {"title_en": "Pre-Socratic philosophy", "fr": "Philosophie présocratique"},
    # Philosophie moderne
    {"title_en": "Immanuel Kant",     "fr": "Emmanuel Kant",   "de": "Immanuel Kant"},
    {"title_en": "René Descartes",    "fr": "René Descartes",  "de": "René Descartes"},
    {"title_en": "Baruch Spinoza",    "fr": "Baruch Spinoza",  "de": "Baruch de Spinoza"},
    {"title_en": "Gottfried Wilhelm Leibniz", "fr": "Gottfried Wilhelm Leibniz"},
    {"title_en": "David Hume",        "fr": "David Hume",      "de": "David Hume"},
    {"title_en": "John Locke",        "fr": "John Locke",      "de": "John Locke"},
    {"title_en": "Jean-Jacques Rousseau", "fr": "Jean-Jacques Rousseau"},
    {"title_en": "Georg Wilhelm Friedrich Hegel", "fr": "Georg Wilhelm Friedrich Hegel", "de": "Georg Wilhelm Friedrich Hegel"},
    # Logique & mathématiques
    {"title_en": "Logic",             "fr": "Logique",         "de": "Logik",       "es": "Lógica"},
    {"title_en": "Set theory",        "fr": "Théorie des ensembles", "de": "Mengenlehre"},
    {"title_en": "Category theory",   "fr": "Théorie des catégories"},
    {"title_en": "Mathematical proof","fr": "Preuve mathématique"},
    {"title_en": "Axiom",             "fr": "Axiome",          "de": "Axiom"},
    {"title_en": "Number theory",     "fr": "Théorie des nombres"},
    # Linguistique
    {"title_en": "Linguistics",       "fr": "Linguistique",    "de": "Linguistik",  "es": "Lingüística"},
    {"title_en": "Morphology (linguistics)", "fr": "Morphologie (linguistique)"},
    {"title_en": "Syntax",            "fr": "Syntaxe",         "de": "Syntax"},
    {"title_en": "Semantics",         "fr": "Sémantique",      "de": "Semantik"},
    {"title_en": "Phonology",         "fr": "Phonologie",      "de": "Phonologie"},
    {"title_en": "Ferdinand de Saussure", "fr": "Ferdinand de Saussure"},
    {"title_en": "Noam Chomsky",      "fr": "Noam Chomsky",    "de": "Noam Chomsky"},
    {"title_en": "Pāṇini",            "fr": "Pāṇini"},
    # Physique & sciences
    {"title_en": "Causality",         "fr": "Causalité",       "de": "Kausalität"},
    {"title_en": "Entropy",           "fr": "Entropie",        "de": "Entropie"},
    {"title_en": "Symmetry",          "fr": "Symétrie",        "de": "Symmetrie"},
    {"title_en": "Spacetime",         "fr": "Espace-temps",    "de": "Raumzeit"},
    {"title_en": "Quantum mechanics", "fr": "Mécanique quantique", "de": "Quantenmechanik"},
    # Philosophie du langage & de l'esprit
    {"title_en": "Philosophy of language", "fr": "Philosophie du langage"},
    {"title_en": "Philosophy of mind",     "fr": "Philosophie de l'esprit"},
    {"title_en": "Consciousness",          "fr": "Conscience",       "de": "Bewusstsein"},
    {"title_en": "Meaning (linguistics)",  "fr": "Signification"},
    {"title_en": "Reference",             "fr": "Référence (linguistique)"},
    # Traditions spirituelles
    {"title_en": "Dharma",            "fr": "Dharma",          "de": "Dharma"},
    {"title_en": "Karma",             "fr": "Karma",           "de": "Karma"},
    {"title_en": "Upanishads",        "fr": "Upanishads",      "de": "Upanischaden"},
    {"title_en": "Tao Te Ching",      "fr": "Tao Te King"},
    {"title_en": "Confucianism",      "fr": "Confucianisme",   "de": "Konfuzianismus"},
    # Mathématiques fondamentales
    {"title_en": "Prime number",      "fr": "Nombre premier",  "de": "Primzahl"},
    {"title_en": "Infinity",          "fr": "Infini",          "de": "Unendlichkeit"},
    {"title_en": "Topology",          "fr": "Topologie",       "de": "Topologie"},
    {"title_en": "Graph theory",      "fr": "Théorie des graphes"},
    {"title_en": "Information theory","fr": "Théorie de l'information"},
]

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "nipada-public/1.0 (github.com/stephanedenis/nipada-public; research)"


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text.lower())
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_).strip("_")


def wikipedia_summary(title: str, lang: str = "en") -> dict | None:
    """Fetche le résumé d'un article Wikipedia via l'API REST."""
    encoded = requests.utils.quote(title.replace(" ", "_"))
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=10)
            if r.status_code == 404:
                return None
            if r.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"  ⏳ rate-limit [{lang}] {title!r}, attente {wait}s…", file=sys.stderr)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError:
            raise
        except Exception as e:
            print(f"  ⚠ Wikipedia [{lang}] {title!r}: {e}", file=sys.stderr)
            return None
    return None


def wikipedia_full_text(title: str, lang: str = "en", max_chars: int = 50_000) -> str:
    """Récupère le texte complet via l'API action (sections concaténées)."""
    encoded = requests.utils.quote(title)
    url = (
        f"https://{lang}.wikipedia.org/w/api.php"
        f"?action=query&prop=extracts&explaintext=1&titles={encoded}"
        f"&format=json&redirects=1"
    )
    try:
        r = SESSION.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            text = page.get("extract", "")
            if text:
                return text[:max_chars]
    except Exception as e:
        print(f"  ⚠ Wikipedia full-text [{lang}] {title!r}: {e}", file=sys.stderr)
    return ""


def compute_freq_signature(text: str) -> dict[str, float]:
    """Freq_signature V17 par lexique — identique à fetch_gutenberg_multilingual."""
    if not text:
        return {}
    words = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", text.lower())
    total = max(len(words), 1)
    raw: dict[str, float] = {}
    for atom, indicators in ATOM_LEXICON.items():
        indicator_set = set(indicators)
        count = sum(1 for w in words if w in indicator_set)
        raw[atom] = count / total
    s = sum(raw.values()) or 1.0
    return {atom: round(v / s, 4) for atom, v in raw.items()}


# ---------------------------------------------------------------------------
# Création de nœuds
# ---------------------------------------------------------------------------

def make_wikipedia_node(
    article: dict,
    lang: str,
    summary_data: dict,
    freq_sig: dict[str, float],
    version: str,
) -> dict:
    title_lang = article.get(lang, article["title_en"]) if lang != "en" else article["title_en"]
    title_en   = article["title_en"]
    slug       = f"wikipedia_{lang}_{slugify(title_lang)[:50]}"
    nipada_id  = f"text/{slug}"

    meta_names: dict[str, str] = {lang: title_lang}
    if lang != "en":
        meta_names["en"] = title_en

    # Ajouter les titres disponibles dans les autres langues
    for other_lang in ["fr", "de", "es", "it"]:
        if other_lang != lang and other_lang in article:
            meta_names[other_lang] = article[other_lang]

    meta: dict = {
        "names": meta_names,
        "scope": "public",
        "provenance": {
            "source_url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "wikipedia_id": summary_data.get("pageid"),
            "lang": lang,
            "availability": "open_access",
            "license": "CC-BY-SA",
        },
    }
    if summary_data.get("description"):
        meta["notes"] = summary_data["description"][:300]

    semantic: dict = {
        "mode": "distributed",
        "atom_version": "V17",
        "atom_set": ATOMS_V17,
        "freq_signature": freq_sig,
    }
    if not freq_sig:
        semantic["stub"] = True

    return {
        "$schema": "https://nipada.org/schema/node_v1.json",
        "nipada_id": nipada_id,
        "type": "text",
        "version": version,
        "status": "draft",
        "meta": meta,
        "semantic": semantic,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Ingestion Wikipedia → data/texts/")
    parser.add_argument("--langs", nargs="+", default=["en", "fr"],
                        help="Langues à ingérer (ex: en fr de es)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Nombre max d'articles à ingérer (par langue)")
    parser.add_argument("--version", default="§272",
                        help="Version NIPADA")
    parser.add_argument("--dry-run", action="store_true",
                        help="Ne pas écrire de fichiers")
    parser.add_argument("--no-text", action="store_true",
                        help="Utiliser le résumé seulement (pas le texte complet)")
    parser.add_argument("--output", default="data/texts",
                        help="Répertoire de sortie")
    parser.add_argument("--stats", default="data/wikipedia_ingestion_stats.json",
                        help="Fichier stats JSON")
    args = parser.parse_args()

    out_dir = Path(args.output)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    articles_to_process = WIKIPEDIA_ARTICLES[: args.limit]

    print(f"🌍 Ingestion Wikipedia — {len(articles_to_process)} articles × {args.langs} langues")
    print(f"   Mode: {'dry-run' if args.dry_run else 'live'}")
    print(f"   Texte: {'résumé uniquement' if args.no_text else 'texte complet'}")
    print()

    created, skipped, errors = 0, 0, 0
    stats_records: list[dict] = []

    for article in articles_to_process:
        title_en = article["title_en"]
        print(f"  📄 {title_en}")

        for lang in args.langs:
            title_lang = article.get(lang, title_en) if lang != "en" else title_en

            # Résumé
            summary_data = wikipedia_summary(title_lang, lang)
            if not summary_data:
                print(f"    [{lang}] ✗ article introuvable")
                skipped += 1
                continue

            # Texte pour freq_signature
            if args.no_text:
                text_for_sig = summary_data.get("extract", "")
            else:
                text_for_sig = wikipedia_full_text(title_lang, lang)
                if not text_for_sig:
                    text_for_sig = summary_data.get("extract", "")

            freq_sig = compute_freq_signature(text_for_sig)

            node = make_wikipedia_node(
                article, lang, summary_data, freq_sig, args.version
            )

            path = out_dir / f"text_wikipedia_{lang}_{slugify(title_lang)[:50]}.json"

            if args.dry_run:
                dom = max(freq_sig, key=freq_sig.get) if freq_sig else "?"
                print(f"    [{lang}] [dry-run] {path.name}  dominant={dom}")
                created += 1
            else:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(node, f, ensure_ascii=False, indent=2)
                dom = max(freq_sig, key=freq_sig.get) if freq_sig else "?"
                print(f"    [{lang}] ✓  {path.name}  dominant={dom}")
                created += 1

            stats_records.append({
                "title_en": title_en,
                "lang": lang,
                "nipada_id": node["nipada_id"],
                "freq_signature": freq_sig,
                "dominant_atom": dom,
                "text_len": len(text_for_sig),
            })

            time.sleep(2.0)  # Respecter les serveurs Wikipedia

    # Stats finales
    print(f"\n✅ {created} nœuds créés, {skipped} ignorés, {errors} erreurs → {out_dir}/")

    if stats_records:
        # Analyse des atomes dominants
        from collections import Counter
        dominant_counts = Counter(r["dominant_atom"] for r in stats_records)
        print("\n📊 Distribution des atomes dominants :")
        for atom, count in dominant_counts.most_common():
            print(f"   {atom:<20} {count:3d}")

    if not args.dry_run and stats_records:
        Path(args.stats).parent.mkdir(parents=True, exist_ok=True)
        stats_out = {
            "date": __import__("datetime").datetime.now().isoformat(),
            "langs": args.langs,
            "articles_requested": len(articles_to_process),
            "nodes_created": created,
            "nodes_skipped": skipped,
            "records": stats_records,
        }
        Path(args.stats).write_text(json.dumps(stats_out, ensure_ascii=False, indent=2))
        print(f"\n💾 Stats sauvegardées → {args.stats}")


if __name__ == "__main__":
    main()
