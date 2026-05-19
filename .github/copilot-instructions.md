# Instructions Copilot - NIPADA

📍 **CONTEXTE LOCAL :** Tu te trouves actuellement dans le sous-module `modules/core/knowledge`.
**Mission stricte :** Graphe de connaissances encyclopédique universel — chaque concept reçoit une identité sémantique mathématiquement fondée.

⚠️ **RÈGLES D'ANTI-DÉBORDEMENT :**
- Gère les nœuds encyclopédiques, les schémas de validation et le corpus signé.
- Ne recrée jamais une logique de stockage FUSE3 (Panini-FS) ni d'extraction dhātu (SemanticCore).
- Ce module fournit la couche de connaissance structurée à l'écosystème.

🗺️ **CARTOGRAPHIE DE L'ÉCOSYSTÈME PANINI :**
1. **Hub/Orchestrateur** (Racine) : Lien entre les modules. Ne contient que l'orchestration (`src/panini_colabmcp`).
2. **Panini-FS** (`modules/core/filesystem`) : Stockage FUSE3.
3. **Panini-SemanticCore** (`modules/core/semantic`) : Extraction dhātu.
4. **NIPADA** (`modules/core/knowledge`) : Graphe de connaissances.
5. **OntoWave** (`modules/ontowave`) : UX et UI.
6. **Panini-AttributionRegistry** (`modules/data/attribution`) : Traçabilité et provenance.
7. **Panini-AutonomousMissions** (`modules/missions/autonomous`) : Workflows IA.
8. **Panini-PublicationEngine** (`modules/publication/engine`) : Formatage/Export.
9. **Panini-UltraReactive** (`modules/reactive/ultra-reactive`) : Streaming temps réel.
10. **Panini-CloudOrchestrator** (`modules/orchestration/cloud`) : Infra et Déploiement.
11. **Panini-Research** (`research`) : Brouillons et laboratoire.

🔗 **RÈGLES GLOBALES :**
Le submodule `copilotage/` est présent dans ce dépôt et contient les directives partagées de l'écosystème Panini.
- **Journal de bord :** ce dépôt tient son propre journal dans `docs/journal-de-bord/YYYY-MM-DD.md`. Consulter `copilotage/regles/REGLES_JOURNAL_v1.md` pour les règles complètes.
- **Règles d'autonomie et de copilotage :** `copilotage/regles/REGLES_COPILOTAGE_v0.0.2.md`
- **Avant tout commit :** créer/mettre à jour `docs/journal-de-bord/$(date +%Y-%m-%d).md` puis stager le fichier.
