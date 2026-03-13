-- =============================================================================
-- analysis_queries.sql
-- Supply Chain Performance Dashboard — Requêtes d'analyse métier
-- =============================================================================
-- Collection de requêtes analytiques prêtes à l'emploi.
-- Compatible SQLite et PostgreSQL (avec ajustements mineurs).
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 1 : VUE GLOBALE
-- ─────────────────────────────────────────────────────────────────────────────

-- Q1.1 — Tableau de bord exécutif
SELECT * FROM v_kpi_global;

-- Q1.2 — Évolution mensuelle clé
SELECT
    order_year_month,
    total_orders,
    total_revenue,
    late_rate_pct,
    avg_lead_time_days
FROM v_kpi_monthly
ORDER BY order_year_month;

-- Q1.3 — Répartition des statuts de commande
SELECT
    order_status,
    COUNT(*)                                            AS nb_orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2)  AS share_pct,
    ROUND(SUM(order_value), 2)                         AS total_revenue
FROM fact_orders
GROUP BY order_status
ORDER BY nb_orders DESC;

-- Q1.4 — Répartition par niveau de priorité
SELECT * FROM v_kpi_by_priority;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 2 : ANALYSE DES RETARDS
-- ─────────────────────────────────────────────────────────────────────────────

-- Q2.1 — Distribution des retards
SELECT * FROM v_delay_distribution;

-- Q2.2 — Top 20 commandes avec le plus grand retard
SELECT
    order_id,
    order_date,
    expected_delivery_date,
    actual_delivery_date,
    delay_days,
    region,
    country,
    priority_level,
    order_value
FROM fact_orders
WHERE is_late = 1
ORDER BY delay_days DESC
LIMIT 20;

-- Q2.3 — Taux de retard mensuel avec tendance glissante
SELECT
    order_year_month,
    total_orders,
    late_orders,
    late_rate_pct,
    ROUND(AVG(late_rate_pct) OVER (
        ORDER BY order_year_month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_late_rate
FROM v_kpi_monthly
ORDER BY order_year_month;

-- Q2.4 — Retards par trimestre
SELECT
    order_year,
    order_quarter,
    COUNT(*)                                           AS total_orders,
    SUM(is_late)                                       AS late_orders,
    ROUND(100.0 * SUM(is_late) / COUNT(*), 2)          AS late_rate_pct,
    ROUND(AVG(CASE WHEN is_late = 1 THEN delay_days END), 2) AS avg_delay_when_late
FROM fact_orders
GROUP BY order_year, order_quarter
ORDER BY order_year, order_quarter;

-- Q2.5 — Retards par niveau de priorité (commandes critiques en retard)
SELECT
    priority_level,
    COUNT(*)                                           AS late_orders,
    ROUND(AVG(delay_days), 2)                          AS avg_delay_days,
    MAX(delay_days)                                    AS max_delay_days,
    ROUND(SUM(order_value), 2)                         AS revenue_at_risk
FROM fact_orders
WHERE is_late = 1
GROUP BY priority_level
ORDER BY avg_delay_days DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 3 : PERFORMANCE TRANSPORTEURS
-- ─────────────────────────────────────────────────────────────────────────────

-- Q3.1 — Classement complet des transporteurs
SELECT * FROM v_kpi_by_carrier;

-- Q3.2 — Top 3 transporteurs (meilleure ponctualité)
SELECT carrier_name, late_rate_pct, avg_lead_time_days, total_orders
FROM v_kpi_by_carrier
ORDER BY late_rate_pct ASC
LIMIT 3;

-- Q3.3 — Pire transporteur (taux de retard le plus élevé)
SELECT carrier_name, late_rate_pct, avg_delay_when_late, total_orders
FROM v_kpi_by_carrier
ORDER BY late_rate_pct DESC
LIMIT 3;

-- Q3.4 — Ratio coût / performance par transporteur
SELECT
    c.carrier_name,
    c.carrier_type,
    ROUND(AVG(f.shipping_cost), 2)             AS avg_shipping_cost,
    ROUND(AVG(f.lead_time_days), 2)            AS avg_lead_time_days,
    ROUND(100.0 * SUM(f.is_late) / COUNT(*), 2) AS late_rate_pct,
    ROUND(AVG(f.shipping_cost) /
        NULLIF(ROUND(100.0 * SUM(CASE WHEN f.is_late = 0 THEN 1 ELSE 0 END) / COUNT(*), 2), 0)
    , 4) AS cost_per_pct_on_time
FROM fact_orders f
JOIN dim_carrier c ON f.carrier_id = c.carrier_id
GROUP BY c.carrier_name, c.carrier_type
ORDER BY late_rate_pct ASC;

-- Q3.5 — Performance transporteur par type de service
SELECT
    c.carrier_type,
    c.service_level,
    COUNT(*)                                           AS total_orders,
    ROUND(AVG(f.shipping_cost), 2)                     AS avg_shipping_cost,
    ROUND(AVG(f.lead_time_days), 2)                    AS avg_lead_time,
    ROUND(100.0 * SUM(f.is_late) / COUNT(*), 2)        AS late_rate_pct
FROM fact_orders f
JOIN dim_carrier c ON f.carrier_id = c.carrier_id
GROUP BY c.carrier_type, c.service_level
ORDER BY c.carrier_type, c.service_level;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 4 : PERFORMANCE ENTREPÔTS
-- ─────────────────────────────────────────────────────────────────────────────

-- Q4.1 — Classement des entrepôts
SELECT * FROM v_kpi_by_warehouse;

-- Q4.2 — Entrepôts avec le plus fort taux de retard
SELECT
    w.warehouse_name,
    w.city,
    w.country,
    COUNT(*)                                           AS total_orders,
    ROUND(100.0 * SUM(f.is_late) / COUNT(*), 2)        AS late_rate_pct,
    ROUND(AVG(f.delay_days), 2)                        AS avg_delay_days
FROM fact_orders f
JOIN dim_warehouse w ON f.warehouse_id = w.warehouse_id
GROUP BY w.warehouse_name, w.city, w.country
HAVING COUNT(*) > 100
ORDER BY late_rate_pct DESC;

-- Q4.3 — Charge par entrepôt et par mois (volumétrie)
SELECT
    w.warehouse_name,
    f.order_year_month,
    COUNT(*)           AS total_orders,
    SUM(f.total_items) AS total_items_shipped
FROM fact_orders f
JOIN dim_warehouse w ON f.warehouse_id = w.warehouse_id
GROUP BY w.warehouse_name, f.order_year_month
ORDER BY f.order_year_month, w.warehouse_name;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 5 : ANALYSE GÉOGRAPHIQUE
-- ─────────────────────────────────────────────────────────────────────────────

-- Q5.1 — Performance par région
SELECT * FROM v_kpi_by_region;

-- Q5.2 — Comparaison inter-régionale (délai et coût)
SELECT
    region,
    COUNT(*)                                           AS total_orders,
    ROUND(AVG(lead_time_days), 2)                      AS avg_lead_time_days,
    ROUND(AVG(shipping_cost), 2)                       AS avg_shipping_cost,
    ROUND(100.0 * SUM(is_late) / COUNT(*), 2)          AS late_rate_pct,
    ROUND(SUM(order_value), 2)                         AS total_revenue
FROM fact_orders
GROUP BY region
ORDER BY late_rate_pct DESC;

-- Q5.3 — Pays avec le délai moyen le plus élevé
SELECT
    country,
    region,
    COUNT(*)                        AS total_orders,
    ROUND(AVG(lead_time_days), 1)   AS avg_lead_time_days,
    ROUND(AVG(delay_days), 1)       AS avg_delay_days,
    ROUND(AVG(shipping_cost), 2)    AS avg_shipping_cost
FROM fact_orders
GROUP BY country, region
HAVING COUNT(*) > 50
ORDER BY avg_lead_time_days DESC
LIMIT 15;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 6 : ANALYSE FINANCIÈRE
-- ─────────────────────────────────────────────────────────────────────────────

-- Q6.1 — Ratio coût logistique / valeur commande par région
SELECT
    region,
    ROUND(AVG(shipping_cost_ratio) * 100, 2) AS avg_shipping_ratio_pct,
    ROUND(SUM(shipping_cost), 2)             AS total_shipping_cost,
    ROUND(SUM(order_value), 2)               AS total_order_value,
    ROUND(SUM(shipping_cost) / NULLIF(SUM(order_value), 0) * 100, 2) AS actual_ratio_pct
FROM fact_orders
GROUP BY region
ORDER BY actual_ratio_pct DESC;

-- Q6.2 — Évolution mensuelle du CA et des coûts logistiques
SELECT
    order_year_month,
    ROUND(SUM(order_value), 2)   AS total_revenue,
    ROUND(SUM(shipping_cost), 2) AS total_shipping_cost,
    ROUND(SUM(shipping_cost) / NULLIF(SUM(order_value), 0) * 100, 2) AS shipping_ratio_pct
FROM fact_orders
GROUP BY order_year_month
ORDER BY order_year_month;

-- Q6.3 — Valeur des commandes en retard (revenus à risque)
SELECT
    priority_level,
    ROUND(SUM(CASE WHEN is_late = 1 THEN order_value ELSE 0 END), 2) AS late_revenue,
    ROUND(SUM(order_value), 2)                                        AS total_revenue,
    ROUND(100.0 * SUM(CASE WHEN is_late = 1 THEN order_value ELSE 0 END) /
        NULLIF(SUM(order_value), 0), 2)                               AS late_revenue_pct
FROM fact_orders
GROUP BY priority_level
ORDER BY late_revenue DESC;
