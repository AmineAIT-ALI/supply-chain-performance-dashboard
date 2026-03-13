# Définition des KPI — Supply Chain Performance Dashboard

---

## KPI Principaux

### 1. Total Orders
- **Définition** : Nombre total de commandes dans la période sélectionnée
- **Python** : `len(df)`
- **SQL** : `COUNT(*) FROM fact_orders`
- **DAX** : `Total Orders = COUNTROWS(fact_orders)`
- **Interprétation** : Volume d'activité de référence

---

### 2. Total Revenue
- **Définition** : Somme des valeurs de commandes (€)
- **Python** : `df["order_value"].sum()`
- **SQL** : `SUM(order_value)`
- **DAX** : `Total Revenue = SUM(fact_orders[order_value])`
- **Interprétation** : Chiffre d'affaires généré sur la période

---

### 3. Total Shipping Cost
- **Définition** : Somme des coûts d'expédition (€)
- **Python** : `df["shipping_cost"].sum()`
- **SQL** : `SUM(shipping_cost)`
- **DAX** : `Total Shipping Cost = SUM(fact_orders[shipping_cost])`
- **Interprétation** : Charge logistique totale

---

### 4. On-Time Delivery Rate (OTDR)
- **Définition** : % de commandes livrées avant ou à la date promise
- **Formule** : `(commandes avec delay_days ≤ 0) / total_orders × 100`
- **Python** : `(df["is_late"] == 0).sum() / len(df) * 100`
- **SQL** : `100.0 * SUM(CASE WHEN is_late = 0 THEN 1 ELSE 0 END) / COUNT(*)`
- **DAX** : `On-Time Delivery Rate % = DIVIDE(CALCULATE(COUNTROWS(fact_orders), fact_orders[is_late]=0), [Total Orders], 0) * 100`
- **Benchmark** : > 85% = bon, > 92% = excellent
- **Interprétation** : Indicateur de fiabilité logistique principal

---

### 5. Late Rate (%)
- **Définition** : % de commandes livrées après la date promise
- **Formule** : `(commandes avec delay_days > 0) / total_orders × 100`
- **Python** : `df["is_late"].mean() * 100`
- **SQL** : `100.0 * SUM(is_late) / COUNT(*)`
- **DAX** : `Late Rate % = DIVIDE([Late Orders Count], [Total Orders], 0) * 100`
- **Benchmark** : < 10% = bon, < 5% = excellent
- **Interprétation** : Proportion de commandes non conformes aux engagements de livraison

---

### 6. Avg Lead Time (jours)
- **Définition** : Délai moyen entre la date de commande et la livraison effective
- **Formule** : `mean(actual_delivery_date - order_date)`
- **Python** : `df["lead_time_days"].mean()`
- **SQL** : `AVG(lead_time_days)`
- **DAX** : `Avg Lead Time Days = AVERAGE(fact_orders[lead_time_days])`
- **Interprétation** : Mesure de la rapidité du cycle logistique complet

---

### 7. Avg Delay When Late (jours)
- **Définition** : Délai moyen des commandes livrées en retard uniquement
- **Python** : `df.loc[df["is_late"]==1, "delay_days"].mean()`
- **SQL** : `AVG(CASE WHEN is_late = 1 THEN delay_days END)`
- **DAX** : `Avg Delay When Late = CALCULATE(AVERAGE(fact_orders[delay_days]), fact_orders[is_late]=1)`
- **Interprétation** : Sévérité des retards (un retard de 1j vs. 15j n'a pas le même impact)

---

### 8. Shipping Cost Ratio (%)
- **Définition** : Rapport entre le coût logistique et la valeur de la commande
- **Formule** : `shipping_cost / order_value × 100`
- **Python** : `(df["shipping_cost"] / df["order_value"]).mean() * 100`
- **SQL** : `AVG(shipping_cost_ratio) * 100`
- **DAX** : `Shipping Cost Ratio % = DIVIDE([Total Shipping Cost], [Total Revenue], 0) * 100`
- **Benchmark** : < 5% = efficace, 5–10% = acceptable, > 10% = à optimiser
- **Interprétation** : Efficience logistique — un ratio élevé peut indiquer des choix de transport sous-optimaux

---

## KPI Avancés

### 9. Orders MoM Growth (%)
- **Définition** : Croissance du nombre de commandes d'un mois à l'autre
- **DAX** : Voir `dax_measures.md` — `Orders MoM Growth %`
- **Interprétation** : Détecte les tendances saisonnières et les pics d'activité

---

### 10. Revenue YoY Growth (%)
- **Définition** : Croissance du CA d'une année à l'autre
- **DAX** : `Revenue YoY Growth %` (Time Intelligence)
- **Interprétation** : Indicateur de croissance business à moyen terme

---

### 11. Late Revenue at Risk (€)
- **Définition** : Valeur totale des commandes en retard
- **Python** : `df.loc[df["is_late"]==1, "order_value"].sum()`
- **DAX** : `Late Revenue = CALCULATE(SUM(fact_orders[order_value]), fact_orders[is_late]=1)`
- **Interprétation** : Impact financier potentiel des retards (risque de litiges, remises, pénalités)

---

### 12. Carrier Late Rate Rank
- **Définition** : Classement des transporteurs du plus ponctuel au moins ponctuel
- **Python** : `carrier_kpis.sort_values("late_rate_pct")`
- **SQL** : `RANK() OVER (ORDER BY late_rate_pct ASC)`
- **DAX** : `Carrier Rank by Late Rate = RANKX(ALL(dim_carrier), [Late Rate %], , ASC, DENSE)`
- **Interprétation** : Permet d'identifier les partenaires logistiques sous-performants

---

### 13. Late Rate 3-Month Rolling Average
- **Définition** : Moyenne glissante du taux de retard sur 3 mois consécutifs
- **SQL** : `AVG(late_rate_pct) OVER (ORDER BY order_year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`
- **DAX** : `Late Rate 3M Rolling %` (voir `dax_measures.md`)
- **Interprétation** : Lisse les variations ponctuelles pour identifier les tendances structurelles

---

### 14. Delay Distribution (Buckets)
- **Définition** : Répartition des commandes en retard par tranche de jours
- **Buckets** : On Time | 1-3 j | 4-7 j | 8-14 j | >14 j
- **Python** : `pd.cut(df["delay_days"], bins=[-inf, 0, 3, 7, 14, inf])`
- **SQL** : `CASE WHEN delay_days BETWEEN 1 AND 3 THEN '1-3 days late' …`
- **Interprétation** : Distingue les retards mineurs (tolérance client) des retards critiques (impact fort)

---

## Tableau de Référence des Benchmarks

| KPI | Mauvais | Acceptable | Bon | Excellent |
|---|---|---|---|---|
| On-Time Delivery Rate | < 75% | 75–84% | 85–92% | > 92% |
| Late Rate | > 25% | 15–25% | 5–15% | < 5% |
| Avg Lead Time | > 15j | 10–15j | 5–10j | < 5j |
| Shipping Cost Ratio | > 12% | 8–12% | 5–8% | < 5% |
| Avg Delay (when late) | > 10j | 5–10j | 2–5j | < 2j |

*Benchmarks indicatifs — à adapter selon le secteur et les SLA contractuels.*
