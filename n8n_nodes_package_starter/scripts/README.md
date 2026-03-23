# Scripts and maintenance workflow

Ce dossier contient le mode opératoire pour récupérer les éléments du package et le tenir à jour.

## Comment récupérer tous les éléments du package

### 1. Construire l'inventaire des pages source

Point de départ recommandé :
- page d'index des integrations
- pages d'index built-in nodes
- pages des familles core / app / trigger / cluster
- pages AI/LangChain de taxonomie

Objectif : produire une liste canonique des URLs de node.

### 2. Télécharger les pages de node

Pour chaque URL :
- récupérer le HTML source
- stocker un snapshot local
- calculer un hash du contenu
- enregistrer la date de collecte

### 3. Extraire les sections normalisées

Chercher, quand présentes :
- titre
- description
- credentials
- operations
- node parameters
- templates and examples
- related resources
- common issues
- notes de version visibles

### 4. Générer les artefacts du package

Pour chaque node :
- créer un dossier stable
- générer `node.json`
- générer `node.md`

Ensuite :
- régénérer `map.json`
- régénérer `indexes/*`
- régénérer `stats.json`
- mettre à jour `sources.json`

## Comment tenir le package à jour en continu

### Stratégie recommandée

#### A. Snapshot complet hebdomadaire
- reconstruire l'inventaire
- redétecter nouveaux nodes
- redétecter pages supprimées ou déplacées
- régénérer tout le package

#### B. Vérification légère quotidienne
- comparer les hashes des pages déjà connues
- si changement, régénérer seulement les nodes impactés

#### C. Validation mensuelle
- contrôler manuellement un échantillon
- vérifier les familles AI / cluster nodes, souvent plus sujettes à évolution
- vérifier les remplacements / notes de version

## Source of truth

La source de vérité doit rester la doc officielle n8n. Le package ne doit pas être enrichi depuis des sources non officielles sans marquage explicite.

## Versioning recommandé

Utiliser Git avec :
- commits datés par snapshot
- tags de release du package
- changelog des nodes ajoutés / modifiés / retirés

## Champs à surveiller pour le diff

- titre du node
- URL de doc
- famille
- liste d'opérations
- paramètres
- notes de version
- présence ou absence d'une page common issues

## Publication recommandée

- dépôt Git principal
- ZIP de snapshot
- optionnel : export vers Drive pour consultation
