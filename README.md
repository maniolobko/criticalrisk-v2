# CriticalRisk Intelligence V2

Prototype Streamlit reconstruit depuis zero pour passer d'un simple score de risque a un outil de mitigation actionnable.

## Objectif

L'application aide une entreprise a comprendre:

- son exposition aux risques d'approvisionnement critiques;
- la probabilite et l'impact d'un choc;
- le cout potentiel de non-action;
- les causes racines du risque;
- le score cible apres mitigation;
- le gain potentiel associe aux actions prioritaires;
- les actions concretes a mener a 30, 60 et 90 jours;
- les scenarios de stress a presenter a un dirigeant.

## Lancement local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploiement Streamlit Cloud

1. Creer un repository GitHub avec ces fichiers.
2. Pousser le dossier `criticalrisk_v2` dans le repository.
3. Aller sur Streamlit Cloud.
4. Cliquer sur `Create app`.
5. Selectionner le repository.
6. Indiquer `app.py` comme fichier principal.
7. Deployer.

L'application ne requiert pas de cle API ni de fichier `secrets.toml`.

## Structure

- `app.py`: interface Streamlit.
- `data.py`: secteurs, matieres, composants et scenarios.
- `risk_engine.py`: calcul du score, probabilite, impact, cout et recommandations.
- `reporting.py`: export texte et PDF.

## Ce qui a ete ajoute dans cette iteration

- Synthese dirigeant.
- Causes racines expliquees en langage business.
- Score actuel et score cible apres actions.
- Valeur estimee par action.
- Effort / impact / KPI pour chaque recommandation.
- Liste des donnees manquantes a collecter pour fiabiliser le modele.

## Iteration simulateur

- Gestion de plusieurs scenarios.
- Creation, duplication, suppression et enregistrement de scenarios.
- Profil entreprise editable.
- Questionnaire complet: fournisseurs, stock, substitution, contrats, couverture prix, logistique, veille, incidents.
- Carte de score par scenario.
- Radar comparatif multi-scenarios.
- Matrice probabilite / impact multi-scenarios.
- Rapport texte et PDF base sur le scenario actif enregistre.

## Prochaine iteration conseillee

Remplacer progressivement les donnees de demonstration par une base de connaissances sourcable:

- pays producteurs;
- concentration fournisseur;
- routes logistiques;
- historiques de chocs;
- delais de requalification;
- cas comparables;
- mesures de mitigation observees.
