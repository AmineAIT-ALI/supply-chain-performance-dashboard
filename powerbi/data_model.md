# Power BI — Modèle de données

## Schéma en étoile

```
                        dim_date
                       (date_key)
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
     order_date_key expected_date_key actual_date_key
          │                │                 │
          └────────────────┼─────────────────┘
                           │
dim_customer ──── customer_id ──── fact_orders ──── carrier_id ──── dim_carrier
                                        │
                                   warehouse_id
                                        │
                                   dim_warehouse
```

---

## Tables et colonnes clés

### fact_orders (Table de faits)
| Colonne | Type | Description |
|---|---|---|
| order_id | Text | Clé primaire |
| customer_id | Text | FK → dim_customer |
| carrier_id | Text | FK → dim_carrier |
| warehouse_id | Text | FK → dim_warehouse |
| order_date_key | Integer | FK → dim_date |
| order_value | Decimal | Valeur de la commande (€) |
| shipping_cost | Decimal | Coût d'expédition (€) |
| shipping_cost_ratio | Decimal | Ratio coût / valeur |
| total_items | Integer | Nombre d'articles |
| delay_days | Integer | Jours de retard (0 = à l'heure) |
| is_late | Integer | 0 = à l'heure, 1 = en retard |
| lead_time_days | Integer | Délai total order → livraison |
| order_status | Text | Delivered / In Transit / etc. |
| priority_level | Text | Standard / High / Critical |
| region | Text | Région géographique |
| country | Text | Pays |
| order_year_month | Text | "2023-04" (axe temporel) |

### dim_date
| Colonne | Type | Description |
|---|---|---|
| date_key | Integer | Clé primaire (YYYYMMDD) |
| date | Date | Date complète |
| year | Integer | Année |
| quarter | Integer | Trimestre (1–4) |
| month | Integer | Mois (1–12) |
| month_name | Text | "January", "February"… |
| year_month | Text | "2023-04" |
| year_quarter | Text | "2023-Q2" |
| is_weekend | Boolean | Vrai si week-end |
| day_name | Text | "Monday"… |

### dim_carrier
| Colonne | Type | Description |
|---|---|---|
| carrier_id | Text | Clé primaire |
| carrier_name | Text | Nom du transporteur |
| carrier_type | Text | Air / Ground / Sea / Rail |
| service_level | Text | Economy / Standard / Express / Premium |

### dim_warehouse
| Colonne | Type | Description |
|---|---|---|
| warehouse_id | Text | Clé primaire |
| warehouse_name | Text | Nom de l'entrepôt |
| city | Text | Ville |
| region | Text | Région |
| country | Text | Pays |

### dim_customer
| Colonne | Type | Description |
|---|---|---|
| customer_id | Text | Clé primaire |
| customer_segment | Text | B2B / B2C / Enterprise / SME |
| industry | Text | Secteur d'activité |
| country | Text | Pays du client |
| region | Text | Région du client |

---

## Relations dans Power BI

| De | Vers | Cardinalité | Active |
|---|---|---|---|
| fact_orders[order_date_key] | dim_date[date_key] | Plusieurs → Un | Oui |
| fact_orders[expected_date_key] | dim_date[date_key] | Plusieurs → Un | Non (role-playing) |
| fact_orders[actual_date_key] | dim_date[date_key] | Plusieurs → Un | Non (role-playing) |
| fact_orders[carrier_id] | dim_carrier[carrier_id] | Plusieurs → Un | Oui |
| fact_orders[warehouse_id] | dim_warehouse[warehouse_id] | Plusieurs → Un | Oui |
| fact_orders[customer_id] | dim_customer[customer_id] | Plusieurs → Un | Oui |

---

## Import des données

**Option 1 — CSV (recommandé pour démarrage)**
- Importer chaque fichier CSV depuis `data/processed/`
- Utiliser Power Query pour définir les types

**Option 2 — SQLite via ODBC**
- Connecter Power BI à `data/supply_chain.db`
- Utiliser les vues SQL comme source (ex. `v_powerbi_main`)

**Fichiers à importer :**
```
data/processed/fact_orders.csv
data/processed/dim_date.csv
data/processed/dim_carrier.csv
data/processed/dim_warehouse.csv
data/processed/dim_customer.csv
data/processed/dim_product.csv
data/processed/supply_chain_analytics.csv
```

---

## Paramètres Power Query recommandés

```m
// Exemple pour fact_orders
let
    Source = Csv.Document(File.Contents("data/processed/fact_orders.csv"),
        [Delimiter=",", Columns=25, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Headers = Table.PromoteHeaders(Source),
    TypesSet = Table.TransformColumnTypes(Headers, {
        {"order_value", type number},
        {"shipping_cost", type number},
        {"delay_days", Int64.Type},
        {"is_late", Int64.Type},
        {"order_date", type date}
    })
in
    TypesSet
```

---

## Grain et hypothèses métier

- **Grain** : 1 ligne = 1 commande (order_id)
- **Devise** : EUR (symbolique, données synthétiques)
- **Fuseau horaire** : UTC (dates sans heure)
- **Retard** : défini comme `actual_delivery_date > expected_delivery_date`
- **Lead time** : `actual_delivery_date - order_date` (en jours)
- **Période couverte** : 2022-01-01 à 2024-12-31 (3 ans)
