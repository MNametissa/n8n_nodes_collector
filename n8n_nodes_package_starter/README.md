# n8n Nodes Knowledge — Starter Package

Ce package starter sert de base pour construire une base de connaissances complète des nodes n8n, exploitable par humain et par agent IA.

## Contenu

- `SKILLS.md` : mode d'emploi du package pour une IA
- `package-manifest.json` : manifeste technique
- `map.json` : carte machine globale des nodes présents dans le package
- `map.md` : vue humaine du contenu
- `taxonomy.json` : taxonomie officielle et interne
- `sources.json` : provenance des sources documentaires
- `stats.json` : statistiques du snapshot
- `indexes/` : index secondaires
- `nodes/` : un dossier par node, contenant `node.json` et `node.md`
- `scripts/` : scripts et procédures de collecte / mise à jour
- `auxiliary/` : tables secondaires

## Ce que contient ce starter

Ce starter n'est **pas** le corpus complet. Il contient :

- la structure cible
- les schémas de données
- les règles d'exploitation par IA
- trois nodes réels d'exemple :
  - Google Sheets
  - OpenAI
  - AI Agent
- un guide de collecte et de mise à jour
- un script d'inventaire initial à adapter

## Objectif de production

À terme, le corpus complet doit couvrir tous les nodes officiels documentés dans la doc n8n.

## Workflow recommandé

1. Construire l'inventaire officiel depuis les pages d'index n8n.
2. Résoudre chaque page de node.
3. Extraire les sections normalisées.
4. Générer `node.json` et `node.md`.
5. Régénérer `map.json`, `indexes/*`, `stats.json`.
6. Marquer les pages obsolètes ou modifiées.
7. Publier un nouveau snapshot.

## Format de livraison recommandé

- dossier versionné dans Git
- archive ZIP pour diffusion
- import éventuel dans Google Drive / Google Docs pour consultation humaine
