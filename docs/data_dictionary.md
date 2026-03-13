# Dictionnaire de Données — Supply Chain Performance Dashboard

---

## Table : orders (raw) / orders_clean (processed)

| Colonne | Type | Description | Valeurs possibles / Format |
|---|---|---|---|
| order_id | TEXT | Identifiant unique de la commande | ORD000001 – ORD050000 |
| customer_id | TEXT | Identifiant client | CUST00001 – CUST02000 |
| order_date | DATE | Date de passation de la commande | YYYY-MM-DD |
| expected_delivery_date | DATE | Date de livraison promise | YYYY-MM-DD |
| actual_delivery_date | DATE | Date de livraison effective | YYYY-MM-DD |
| carrier_id | TEXT | Identifiant du transporteur | CAR001 – CAR012 |
| warehouse_id | TEXT | Identifiant de l'entrepôt d'origine | WH-PARIS, WH-NYC… |
| region | TEXT | Région de livraison | Europe, North America, Asia Pacific, Middle East, Africa |
| country | TEXT | Pays de livraison | France, USA, China… |
| order_status | TEXT | Statut final de la commande | Delivered, In Transit, Pending, Cancelled, Returned |
| shipping_cost | REAL | Coût d'expédition en EUR | 0.00 – 5000.00 |
| order_value | REAL | Valeur totale de la commande en EUR | 10.00 – 50000.00 |
| priority_level | TEXT | Niveau de priorité de la commande | Standard (60%), High (30%), Critical (10%) |

---

## Table : order_lines (raw) / order_lines_clean (processed)

| Colonne | Type | Description | Valeurs possibles / Format |
|---|---|---|---|
| order_line_id | TEXT | Identifiant unique de la ligne | OL0000001 – OL… |
| order_id | TEXT | FK → orders.order_id | ORD000001 – ORD050000 |
| product_id | TEXT | FK → products.product_id | PRD0001 – PRD0250 |
| quantity | INTEGER | Quantité commandée | 1 – 100 |
| unit_price | REAL | Prix unitaire en EUR | 1.00 – 1000.00 |
| discount | REAL | Remise appliquée (0 = pas de remise) | 0.00, 0.05, 0.10, 0.15, 0.20 |
| line_total | REAL | Montant de la ligne (qty × price × (1 – discount)) | Calculé |

---

## Table : products

| Colonne | Type | Description | Valeurs possibles |
|---|---|---|---|
| product_id | TEXT | Identifiant unique produit | PRD0001 – PRD0250 |
| product_name | TEXT | Nom descriptif du produit | "{Subcategory} Model-XXXX" |
| category | TEXT | Catégorie principale | Electronics, Industrial, Healthcare, Fashion, Food & Beverage, Automotive, Office |
| subcategory | TEXT | Sous-catégorie | Smartphones, Laptops, Machinery… |
| weight | REAL | Poids en kg | 0.10 – 50.00 |
| volume | REAL | Volume en m³ | 0.01 – 5.00 |

---

## Table : carriers

| Colonne | Type | Description | Valeurs possibles |
|---|---|---|---|
| carrier_id | TEXT | Identifiant unique du transporteur | CAR001 – CAR012 |
| carrier_name | TEXT | Nom commercial du transporteur | FastFreight, GlobalShip… |
| carrier_type | TEXT | Mode de transport principal | Air, Ground, Sea, Rail |
| service_level | TEXT | Niveau de service proposé | Economy, Standard, Express, Premium |

---

## Table : warehouses

| Colonne | Type | Description | Valeurs possibles |
|---|---|---|---|
| warehouse_id | TEXT | Identifiant unique de l'entrepôt | WH-PARIS, WH-NYC… |
| warehouse_name | TEXT | Nom de l'entrepôt | Paris, New York… |
| city | TEXT | Ville | Paris, Berlin, Shanghai… |
| region | TEXT | Région | Europe, North America… |
| country | TEXT | Pays | France, USA, China… |

---

## Table : customers

| Colonne | Type | Description | Valeurs possibles |
|---|---|---|---|
| customer_id | TEXT | Identifiant unique client | CUST00001 – CUST02000 |
| customer_segment | TEXT | Segment commercial du client | B2B, B2C, Enterprise, SME |
| industry | TEXT | Secteur d'activité du client | Retail, Manufacturing, Healthcare… |
| country | TEXT | Pays d'origine du client | France, USA… |
| region | TEXT | Région d'origine du client | Europe, North America… |

---

## Table : fact_orders (modèle dimensionnel)

| Colonne | Type | Description | Calculé ? |
|---|---|---|---|
| order_id | TEXT | Clé primaire | Non |
| customer_id | TEXT | FK → dim_customer | Non |
| carrier_id | TEXT | FK → dim_carrier | Non |
| warehouse_id | TEXT | FK → dim_warehouse | Non |
| main_product_id | TEXT | FK → dim_product — produit avec la plus haute valeur de ligne | Oui |
| order_date_key | INTEGER | FK → dim_date (YYYYMMDD) — date de commande | Oui |
| expected_date_key | INTEGER | FK → dim_date (YYYYMMDD) — date de livraison promise | Oui |
| actual_date_key | INTEGER | FK → dim_date (YYYYMMDD) — date de livraison effective | Oui |
| order_date | TEXT | Date de commande (brute, pour calculs directs) | Non |
| expected_delivery_date | TEXT | Date de livraison promise (brute) | Non |
| actual_delivery_date | TEXT | Date de livraison effective (brute) | Non |
| region | TEXT | Région de l'entrepôt source | Non |
| country | TEXT | Pays de l'entrepôt source | Non |
| order_status | TEXT | Statut de la commande | Non |
| priority_level | TEXT | Niveau de priorité | Non |
| order_value | REAL | Valeur de la commande | Non |
| shipping_cost | REAL | Coût logistique | Non |
| shipping_cost_ratio | REAL | shipping_cost / order_value | Oui |
| total_items | INTEGER | Somme des quantités des lignes | Oui |
| total_lines | INTEGER | Nombre de lignes de commande | Oui |
| avg_unit_price | REAL | Prix unitaire moyen des lignes | Oui |
| avg_discount | REAL | Remise moyenne des lignes (0–1) | Oui |
| lines_total_value | REAL | Somme des line_total des lignes | Oui |
| delay_days | INTEGER | actual_delivery_date – expected_delivery_date | Oui |
| is_late | INTEGER | 1 si delay_days > 0, sinon 0 | Oui |
| lead_time_days | INTEGER | actual_delivery_date – order_date | Oui |
| order_year | INTEGER | Année de la commande | Oui |
| order_month | INTEGER | Mois de la commande | Oui |
| order_quarter | INTEGER | Trimestre de la commande | Oui |
| order_year_month | TEXT | "2023-04" | Oui |

---

## Table : dim_date

| Colonne | Type | Description |
|---|---|---|
| date_key | INTEGER | Clé primaire — format YYYYMMDD |
| date | TEXT | Date complète |
| year | INTEGER | Année (2022–2024) |
| quarter | INTEGER | Trimestre (1–4) |
| month | INTEGER | Mois (1–12) |
| month_name | TEXT | Nom complet du mois |
| month_abbr | TEXT | Abréviation du mois (Jan, Feb…) |
| week | INTEGER | Numéro de semaine ISO |
| day_of_month | INTEGER | Jour du mois (1–31) |
| day_of_week | INTEGER | Jour de la semaine (0=Lundi) |
| day_name | TEXT | Nom du jour |
| is_weekend | INTEGER | 1 = week-end, 0 = semaine |
| year_month | TEXT | Format "2023-04" (axe Power BI) |
| year_quarter | TEXT | Format "2023-Q2" |

---

## Colonnes calculées (supply_chain_analytics.csv)

| Colonne | Description |
|---|---|
| delay_bucket | Catégorisation du retard : "On Time", "1-3 days late", "4-7 days late", "8-14 days late", ">14 days late" |
| is_on_time | 1 si commande livrée à temps (alias de is_late == 0) |
| is_critical | 1 si priority_level = "Critical" |
| is_high_value | 1 si order_value >= 75e percentile |
| main_product_id | Identifiant du produit principal (FK → dim_product) |
| main_category | Catégorie produit principale (Electronics, Fashion…) |
| main_subcategory | Sous-catégorie associée au produit principal |
| carrier_name | Nom du transporteur (jointure dim_carrier) |
| carrier_type | Mode de transport (Air, Ground, Sea, Rail) |
| service_level | Niveau de service du transporteur |
| warehouse_name | Nom de l'entrepôt (jointure dim_warehouse) |
| warehouse_city | Ville de l'entrepôt |
| warehouse_region | Région de l'entrepôt (renommé depuis dim_warehouse.region pour éviter conflit) |
| warehouse_country | Pays de l'entrepôt (renommé depuis dim_warehouse.country) |

---

## Règles de qualité des données

| Règle | Implémentation |
|---|---|
| order_id unique | drop_duplicates(subset=["order_id"]) |
| actual_delivery_date >= order_date | Correction automatique si incohérence |
| shipping_cost >= 0 | Remplacement par 0 si négatif |
| order_value > 0 | Valeur absolue si négatif |
| quantity > 0 | Suppression des lignes avec qty ≤ 0 |
| discount ∈ [0, 1] | Clip entre 0 et 1 |
| order_status ∈ liste valide | Remplacement par "Delivered" si inconnu |
| priority_level ∈ liste valide | Remplacement par "Standard" si inconnu |
| shipping_cost (outliers) | Cap au 99e percentile par z-score > 3.5 |
| carrier_id null | Imputation par la modalité la plus fréquente |
| actual_delivery_date null | Imputation neutre = expected_delivery_date (hypothèse : livraison à temps) |
