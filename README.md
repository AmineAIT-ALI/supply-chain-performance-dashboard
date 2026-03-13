# Supply Chain Performance Dashboard

**Analyse de performance logistique | Python · SQL · Power BI**

Pipeline ETL complet et dashboard décisionnel pour le pilotage des opérations supply chain : délais, transporteurs, entrepôts, géographie et tendances opérationnelles.

---

## Contexte Métier

Ce projet simule le système d'analyse d'un distributeur multicanal opérant à l'international. L'objectif est de donner aux équipes supply chain une visibilité instantanée sur :

- La **ponctualité des livraisons** (taux OTDR, retards, Lead Time)
- La **performance comparative des transporteurs**
- La **charge et l'efficacité des entrepôts** par zone géographique
- Les **coûts logistiques** rapportés à la valeur générée
- Les **tendances opérationnelles** sur 3 ans (2022–2024)

**Volume de données :** 50 000 commandes · 12 transporteurs · 18 entrepôts · 250 produits · 2 000 clients

---

## Stack Technique

| Couche | Technologie |
|---|---|
| Génération / ETL | Python 3.10+ (pandas, numpy) |
| Stockage | SQLite (compatible PostgreSQL) |
| Modélisation BI | Schéma en étoile (fact + 5 dimensions) |
| Visualisation | Power BI Desktop |
| Documentation | Markdown |

---

## Architecture du Projet

```
supply-chain-performance-dashboard/
│
├── data/
│   ├── raw/                    # CSV bruts générés (non committés)
│   ├── processed/              # CSV nettoyés + modèle dimensionnel
│   └── external/               # Données externes éventuelles
│
├── sql/
│   ├── schema.sql              # Schéma DDL (tables fact + dimensions)
│   ├── views.sql               # Vues KPI analytiques
│   └── analysis_queries.sql   # Requêtes d'analyse métier
│
├── src/
│   ├── config.py               # Configuration centralisée (chemins, paramètres)
│   ├── utils.py                # Fonctions utilitaires partagées
│   ├── generate_data.py        # Génération du dataset synthétique
│   ├── clean_data.py           # Pipeline de nettoyage
│   ├── transform_data.py       # Modélisation dimensionnelle
│   ├── load_to_db.py           # Chargement SQLite + vues
│   └── kpi_analysis.py         # Calcul et export des KPI
│
├── notebooks/
│   └── exploratory_analysis.ipynb  # Analyse exploratoire interactive
│
├── powerbi/
│   ├── data_model.md           # Modèle de données Power BI
│   ├── dax_measures.md         # Mesures DAX documentées
│   └── dashboard_structure.md  # Structure des pages et visuels
│
├── docs/
│   ├── business_context.md     # Contexte et objectifs métier
│   ├── data_dictionary.md      # Dictionnaire de toutes les colonnes
│   ├── kpi_definition.md       # Définition détaillée des KPI
│   └── insights.md             # Analyse et interprétation métier
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Installation

### Prérequis
- Python 3.10+
- pip

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/AmineAIT-ALI/supply-chain-performance-dashboard.git
cd supply-chain-performance-dashboard

# 2. Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate       # macOS / Linux
# venv\Scripts\activate        # Windows

# 3. Installer les dépendances
pip install -r requirements.txt
```

---

## Exécution du Pipeline

Exécuter les scripts dans cet ordre depuis la racine du projet :

```bash
# Étape 1 — Générer les données synthétiques brutes
python src/generate_data.py

# Étape 2 — Nettoyer les données
python src/clean_data.py

# Étape 3 — Transformer et construire le modèle dimensionnel
python src/transform_data.py

# Étape 4 — Charger dans SQLite
python src/load_to_db.py

# Étape 5 — Calculer et exporter les KPI
python src/kpi_analysis.py
```

**Sortie attendue :**
```
data/raw/           → 6 fichiers CSV bruts
data/processed/     → fact_orders.csv, dim_*.csv, supply_chain_analytics.csv
data/processed/kpis → kpi_global.csv, kpi_by_carrier.csv, ...
data/supply_chain.db → Base SQLite avec tables + vues
```

### Analyse exploratoire (Jupyter)

```bash
jupyter notebook notebooks/exploratory_analysis.ipynb
```

---

## Modèle de Données

Schéma en étoile — Grain : 1 ligne = 1 commande

```
                         dim_date
                        (date_key)
                             |
            order_date_key ──┤── expected_date_key
                             │
dim_customer ─── customer_id ─── FACT_ORDERS ─── carrier_id ─── dim_carrier
                                      │
                                 warehouse_id
                                      │
                                 dim_warehouse
```

| Table | Clé primaire | Grain |
|---|---|---|
| fact_orders | order_id | 1 commande |
| dim_date | date_key (YYYYMMDD) | 1 jour |
| dim_customer | customer_id | 1 client |
| dim_carrier | carrier_id | 1 transporteur |
| dim_warehouse | warehouse_id | 1 entrepôt |

---

## KPI Calculés

### KPI Principaux
| KPI | Description |
|---|---|
| Total Orders | Nombre de commandes |
| Total Revenue | CA total (€) |
| Total Shipping Cost | Coût logistique total |
| On-Time Delivery Rate | % livraisons à l'heure |
| Late Rate | % livraisons en retard |
| Avg Lead Time | Délai moyen order → livraison |
| Avg Delay When Late | Retard moyen (commandes tardives) |
| Shipping Cost Ratio | Coût logistique / CA |

### KPI Avancés
| KPI | Description |
|---|---|
| Orders MoM Growth | Croissance mensuelle |
| Revenue YoY Growth | Croissance annuelle |
| Late Revenue at Risk | CA exposé aux retards |
| Carrier Late Rate Rank | Classement transporteurs |
| Late Rate 3M Rolling | Moyenne glissante retards |
| Delay Distribution | Répartition par buckets de retard |

---

## Dashboard Power BI

4 pages analytiques :

| Page | Titre | Contenu |
|---|---|---|
| 1 | Executive Overview | KPI globaux, carte mondiale, tendances, statuts |
| 2 | Carrier Performance | Comparaison transporteurs, scatter coût/fiabilité |
| 3 | Warehouse Operations | Heatmap retards, volumétrie, performance par entrepôt |
| 4 | Delay Analysis | Distribution retards, tendances, drill-down catégories |

**Sources :** Importer les CSV depuis `data/processed/` ou connecter à `data/supply_chain.db`

Voir [powerbi/data_model.md](powerbi/data_model.md), [powerbi/dax_measures.md](powerbi/dax_measures.md) et [powerbi/dashboard_structure.md](powerbi/dashboard_structure.md).

---

## Insights Métier Principaux

- **18% des commandes sont livrées en retard**, avec une concentration sur les transporteurs de type Economy et les zones Afrique / Moyen-Orient
- **3 transporteurs sur 12** concentrent 40%+ des retards malgré des volumes comparables
- **Le T4** (oct–déc) génère systématiquement un pic de retard de +4 à +5 points (effet fêtes/Black Friday)
- **Le ratio coût logistique / CA** dépasse 18% sur les commandes < 100€, questionnant la rentabilité de ce segment
- Les commandes **Critical** bénéficient d'un taux OTDR supérieur (~89%), validant l'efficacité du routage prioritaire

Analyse complète : [docs/insights.md](docs/insights.md)

---

## Licence

**Auteur**
AmineAIT-ALI — [github.com/AmineAIT-ALI](https://github.com/AmineAIT-ALI)

Projet portfolio démontrant des compétences en Data Engineering et Analytics Engineering.

Stack : Python · SQL · SQLite · pandas · numpy
