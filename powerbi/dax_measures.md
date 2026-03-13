# Power BI — Mesures DAX

Toutes les mesures sont regroupées dans une table de mesures dédiée `_Measures`.

---

## Table de mesures : `_Measures`

Créer une table vide appelée `_Measures` pour centraliser toutes les mesures.

---

## 1. Métriques de volume

```dax
// Nombre total de commandes
Total Orders = COUNTROWS(fact_orders)

// Commandes livrées
Delivered Orders =
CALCULATE(
    COUNTROWS(fact_orders),
    fact_orders[order_status] = "Delivered"
)

// Commandes annulées
Cancelled Orders =
CALCULATE(
    COUNTROWS(fact_orders),
    fact_orders[order_status] = "Cancelled"
)

// Nombre total d'articles expédiés
Total Items Shipped = SUM(fact_orders[total_items])
```

---

## 2. Métriques financières

```dax
// Chiffre d'affaires total
Total Revenue = SUM(fact_orders[order_value])

// Coût logistique total
Total Shipping Cost = SUM(fact_orders[shipping_cost])

// Valeur moyenne par commande
Avg Order Value = AVERAGE(fact_orders[order_value])

// Coût logistique moyen par commande
Avg Shipping Cost = AVERAGE(fact_orders[shipping_cost])

// Ratio coût logistique / CA
Shipping Cost Ratio % =
DIVIDE(
    [Total Shipping Cost],
    [Total Revenue],
    0
) * 100

// CA des commandes en retard (revenus à risque)
Late Revenue =
CALCULATE(
    SUM(fact_orders[order_value]),
    fact_orders[is_late] = 1
)
```

---

## 3. Métriques de performance logistique

```dax
// Délai moyen de livraison (lead time)
Avg Lead Time Days = AVERAGE(fact_orders[lead_time_days])

// Délai moyen de retard (toutes commandes)
Avg Delay Days = AVERAGE(fact_orders[delay_days])

// Délai moyen des commandes EN RETARD uniquement
Avg Delay When Late =
CALCULATE(
    AVERAGE(fact_orders[delay_days]),
    fact_orders[is_late] = 1
)

// Nombre de commandes en retard
Late Orders Count =
CALCULATE(
    COUNTROWS(fact_orders),
    fact_orders[is_late] = 1
)

// Taux de livraison à temps (%)
On-Time Delivery Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(fact_orders), fact_orders[is_late] = 0),
    [Total Orders],
    0
) * 100

// Taux de retard (%)
Late Rate % =
DIVIDE([Late Orders Count], [Total Orders], 0) * 100

// Retard maximum observé
Max Delay Days = MAX(fact_orders[delay_days])
```

---

## 4. Métriques comparatives et rankings

```dax
// Taux de retard du transporteur sélectionné vs. moyenne globale
Carrier Late Rate vs Avg =
VAR CarrierRate = [Late Rate %]
VAR GlobalRate  = CALCULATE([Late Rate %], ALL(dim_carrier))
RETURN CarrierRate - GlobalRate

// Rang du transporteur par taux de retard (1 = meilleur)
Carrier Rank by Late Rate =
RANKX(
    ALL(dim_carrier),
    [Late Rate %],
    ,
    ASC,
    DENSE
)

// Rang de l'entrepôt par volume de commandes
Warehouse Rank by Volume =
RANKX(
    ALL(dim_warehouse),
    [Total Orders],
    ,
    DESC,
    DENSE
)
```

---

## 5. Analyses temporelles

```dax
// Croissance MoM des commandes (%)
Orders MoM Growth % =
VAR CurrentMonth = [Total Orders]
VAR PreviousMonth =
    CALCULATE(
        [Total Orders],
        DATEADD(dim_date[date], -1, MONTH)
    )
RETURN
DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth, 0) * 100

// Croissance YoY du CA (%)
Revenue YoY Growth % =
VAR CurrentYear = [Total Revenue]
VAR PreviousYear =
    CALCULATE(
        [Total Revenue],
        DATEADD(dim_date[date], -1, YEAR)
    )
RETURN
DIVIDE(CurrentYear - PreviousYear, PreviousYear, 0) * 100

// Cumul annuel des commandes (YTD)
Orders YTD =
TOTALYTD([Total Orders], dim_date[date])

// Cumul annuel du CA (YTD)
Revenue YTD =
TOTALYTD([Total Revenue], dim_date[date])

// Taux de retard glissant sur 3 mois
Late Rate 3M Rolling % =
CALCULATE(
    [Late Rate %],
    DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -3, MONTH)
)
```

---

## 6. Métriques conditionnelles pour alertes

```dax
// Alerte retard : texte dynamique selon le taux
Late Rate Status =
SWITCH(
    TRUE(),
    [Late Rate %] >= 25, "CRITICAL",
    [Late Rate %] >= 15, "WARNING",
    "NORMAL"
)

// Couleur dynamique pour le taux de retard (utilisée dans la mise en forme conditionnelle)
Late Rate Color =
SWITCH(
    TRUE(),
    [Late Rate %] >= 25, "#C0392B",  -- Rouge
    [Late Rate %] >= 15, "#E67E22",  -- Orange
    "#27AE60"                         -- Vert
)

// Commandes critiques en retard (priorité = Critical)
Critical Late Orders =
CALCULATE(
    [Late Orders Count],
    fact_orders[priority_level] = "Critical"
)
```

---

## 7. Mesures pour les tooltips et détails

```dax
// Texte de résumé pour tooltip transporteur
Carrier Summary =
VAR Name     = SELECTEDVALUE(dim_carrier[carrier_name], "All")
VAR LateRate = FORMAT([Late Rate %], "0.0") & "%"
VAR AvgLead  = FORMAT([Avg Lead Time Days], "0.0") & " days"
RETURN
"Carrier: " & Name & UNICHAR(10) &
"Late Rate: " & LateRate & UNICHAR(10) &
"Avg Lead Time: " & AvgLead

// Format monétaire court (K / M)
Revenue Formatted =
VAR R = [Total Revenue]
RETURN
SWITCH(
    TRUE(),
    R >= 1000000, FORMAT(R / 1000000, "0.0") & "M €",
    R >= 1000,    FORMAT(R / 1000,    "0.0") & "K €",
    FORMAT(R, "0") & " €"
)
```

---

## 8. Mesures pour la table de détails

```dax
// Nombre de commandes visibles après filtres
Filtered Orders Count = COUNTROWS(fact_orders)

// Sélection unique — pour les cards de contexte
Selected Carrier =
SELECTEDVALUE(dim_carrier[carrier_name], "All Carriers")

Selected Warehouse =
SELECTEDVALUE(dim_warehouse[warehouse_name], "All Warehouses")

Selected Region =
SELECTEDVALUE(fact_orders[region], "All Regions")
```

---

## Bonnes pratiques DAX appliquées

- Toutes les divisions utilisent `DIVIDE()` pour éviter les erreurs `/0`
- Les mesures de ratio sont exprimées en `%` (multipliées par 100)
- Les filtres `ALL()` et `CALCULATE()` sont utilisés pour les comparaisons contextuelles
- Les mesures temporelles utilisent les fonctions Time Intelligence de la `dim_date`
- Les mesures de ranking utilisent `RANKX` avec `DENSE` pour éviter les sauts
