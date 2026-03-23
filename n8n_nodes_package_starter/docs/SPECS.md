# Spécification complète du package

## Objectif
Construire une base de connaissances versionnable sur les nodes n8n officiels, exploitable par humain et par IA.

## Principes
- un dossier par node
- un `node.json` canonique
- un `node.md` lisible
- une carte globale `map.json`
- des index secondaires
- une taxonomie stable
- une provenance traçable

## Familles
- core
- action
- trigger
- cluster_root
- cluster_sub

## Fichiers racine
- README.md
- SKILLS.md
- package-manifest.json
- map.json
- map.md
- taxonomy.json
- sources.json
- stats.json

## Règles de production
1. inventorier les pages officielles
2. collecter les pages
3. extraire les sections normalisées
4. générer les artefacts node
5. régénérer les index
6. publier un snapshot versionné

## Maintenance
- vérification légère quotidienne
- snapshot complet hebdomadaire
- audit mensuel

## Règles IA
L'IA doit commencer par `map.json`, résoudre le node, puis consulter `node.json`.
