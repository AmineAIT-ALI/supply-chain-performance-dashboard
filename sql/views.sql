-- =============================================================================
-- views.sql
-- Supply Chain Performance Dashboard — Vues SQL analytiques
-- =============================================================================
-- Ces vues exposent les KPI directement exploitables par Power BI ou tout
-- outil de BI connecté à la base SQLite.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- VUE 1 : Résumé global des KPI
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_kpi_global AS
SELECT
    COUNT(*)                                         AS total_orders,
    SUM(CASE WHEN order_status = 'Delivered' THEN 1 ELSE 0 END) AS total_delivered,
    ROUND(SUM(order_value), 2)                       AS total_revenue,
    ROUND(SUM(shipping_cost), 2)                     AS total_shipping_cost,
    ROUND(AVG(order_value), 2)                       AS avg_order_value,
    ROUND(AVG(shipping_cost), 2)                     AS avg_shipping_cost,
    ROUND(AVG(lead_time_days), 2)                    AS avg_lead_time_days,
    ROUND(AVG(delay_days), 2)                        AS avg_delay_days,
    ROUND(100.0 * SUM(CASE WHEN is_late = 0 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                     AS on_time_rate_pct,
    SUM(is_late)                                     AS late_orders_count,
    ROUND(100.0 * SUM(is_late) / COUNT(*), 2)        AS late_rate_pct,
    ROUND(AVG(CASE WHEN is_late = 1 THEN delay_days END), 2)
                                                     AS avg_delay_when_late_days,
    SUM(total_items)                                 AS total_items_shipped
FROM fact_orders;

-- -----------------------------------------------------------------------------
-- VUE 2 : Performance par transporteur
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_kpi_by_carrier AS
SELECT
    f.carrier_id,
    c.carrier_name,
    c.carrier_type,
    c.service_level,
    COUNT(*)                                               AS total_orders,
    ROUND(SUM(f.order_value), 2)                           AS total_revenue,
    ROUND(SUM(f.shipping_cost), 2)                         AS total_shipping_cost,
    ROUND(AVG(f.shipping_cost), 2)                         AS avg_shipping_cost,
    ROUND(AVG(f.lead_time_days), 2)                        AS avg_lead_time_days,
    ROUND(AVG(f.delay_days), 2)                            AS avg_delay_days,
    SUM(f.is_late)                                         AS late_orders,
    ROUND(100.0 * SUM(f.is_late) / COUNT(*), 2)            AS late_rate_pct,
    ROUND(AVG(CASE WHEN f.is_late = 1 THEN f.delay_days END), 2)
                                                           AS avg_delay_when_late,
    SUM(f.total_items)                                     AS total_items,
    ROUND(100.0 * SUM(f.order_value) /
        (SELECT SUM(order_value) FROM fact_orders), 2)     AS revenue_share_pct
FROM fact_orders f
LEFT JOIN dim_carrier c ON f.carrier_id = c.carrier_id
GROUP BY f.carrier_id, c.carrier_name, c.carrier_type, c.service_level
ORDER BY late_rate_pct ASC;

-- -----------------------------------------------------------------------------
-- VUE 3 : Performance par entrepôt
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_kpi_by_warehouse AS
SELECT
    f.warehouse_id,
    w.warehouse_name,
    w.city,
    w.region,
    w.country,
    COUNT(*)                                           AS total_orders,
    ROUND(SUM(f.order_value), 2)                       AS total_revenue,
    ROUND(AVG(f.shipping_cost), 2)                     AS avg_shipping_cost,
    ROUND(AVG(f.lead_time_days), 2)                    AS avg_lead_time_days,
    ROUND(AVG(f.delay_days), 2)                        AS avg_delay_days,
    SUM(f.is_late)                                     AS late_orders,
    ROUND(100.0 * SUM(f.is_late) / COUNT(*), 2)        AS late_rate_pct,
    SUM(f.total_items)                                 AS total_items_shipped
FROM fact_orders f
LEFT JOIN dim_warehouse w ON f.warehouse_id = w.warehouse_id
GROUP BY f.warehouse_id, w.warehouse_name, w.city, w.region, w.country
ORDER BY total_orders DESC;

-- -----------------------------------------------------------------------------
-- VUE 4 : Performance géographique (région / pays)
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_kpi_by_region AS
SELECT
    region,
    country,
    COUNT(*)                                           AS total_orders,
    ROUND(SUM(order_value), 2)                         AS total_revenue,
    ROUND(AVG(shipping_cost), 2)                       AS avg_shipping_cost,
    ROUND(AVG(lead_time_days), 2)                      AS avg_lead_time_days,
    ROUND(AVG(delay_days), 2)                          AS avg_delay_days,
    SUM(is_late)                                       AS late_orders,
    ROUND(100.0 * SUM(is_late) / COUNT(*), 2)          AS late_rate_pct,
    ROUND(100.0 * SUM(order_value) /
        (SELECT SUM(order_value) FROM fact_orders), 2) AS revenue_share_pct
FROM fact_orders
GROUP BY region, country
ORDER BY total_orders DESC;

-- -----------------------------------------------------------------------------
-- VUE 5 : Tendances mensuelles
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_kpi_monthly AS
SELECT
    order_year,
    order_month,
    order_year_month,
    COUNT(*)                                           AS total_orders,
    ROUND(SUM(order_value), 2)                         AS total_revenue,
    ROUND(SUM(shipping_cost), 2)                       AS total_shipping_cost,
    ROUND(AVG(lead_time_days), 2)                      AS avg_lead_time_days,
    ROUND(AVG(delay_days), 2)                          AS avg_delay_days,
    SUM(is_late)                                       AS late_orders,
    ROUND(100.0 * SUM(is_late) / COUNT(*), 2)          AS late_rate_pct,
    SUM(total_items)                                   AS total_items
FROM fact_orders
GROUP BY order_year, order_month, order_year_month
ORDER BY order_year, order_month;

-- -----------------------------------------------------------------------------
-- VUE 6 : Performance par niveau de priorité
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_kpi_by_priority AS
SELECT
    priority_level,
    COUNT(*)                                           AS total_orders,
    ROUND(SUM(order_value), 2)                         AS total_revenue,
    ROUND(AVG(lead_time_days), 2)                      AS avg_lead_time_days,
    ROUND(AVG(delay_days), 2)                          AS avg_delay_days,
    SUM(is_late)                                       AS late_orders,
    ROUND(100.0 * SUM(is_late) / COUNT(*), 2)          AS late_rate_pct,
    ROUND(100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM fact_orders), 2)         AS share_pct
FROM fact_orders
GROUP BY priority_level;

-- -----------------------------------------------------------------------------
-- VUE 7 : Distribution des retards
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_delay_distribution AS
SELECT
    CASE
        WHEN delay_days <= 0             THEN 'On Time'
        WHEN delay_days BETWEEN 1 AND 3  THEN '1-3 days late'
        WHEN delay_days BETWEEN 4 AND 7  THEN '4-7 days late'
        WHEN delay_days BETWEEN 8 AND 14 THEN '8-14 days late'
        ELSE '>14 days late'
    END AS delay_bucket,
    COUNT(*) AS order_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_late_orders
FROM fact_orders
WHERE is_late = 1
GROUP BY delay_bucket
ORDER BY MIN(delay_days);

-- -----------------------------------------------------------------------------
-- VUE 8 : Vue consolidée Power BI (dénormalisée, prête à l'emploi)
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_powerbi_main AS
SELECT
    f.order_id,
    f.order_date,
    f.expected_delivery_date,
    f.actual_delivery_date,
    f.order_year,
    f.order_month,
    f.order_quarter,
    f.order_year_month,
    f.region,
    f.country,
    f.order_status,
    f.priority_level,
    f.order_value,
    f.shipping_cost,
    f.shipping_cost_ratio,
    f.total_items,
    f.total_lines,
    f.delay_days,
    f.is_late,
    f.lead_time_days,
    -- Dimensions dénormalisées
    c.carrier_name,
    c.carrier_type,
    c.service_level,
    w.warehouse_name,
    w.city               AS warehouse_city,
    w.region             AS warehouse_region,
    w.country            AS warehouse_country,
    cu.customer_segment,
    cu.industry,
    -- Dimension produit principal
    f.main_product_id,
    p.product_name      AS main_product_name,
    p.category          AS main_category,
    p.subcategory       AS main_subcategory,
    -- Attributs des dates expected / actual (role-playing dim_date)
    de.year_month       AS expected_year_month,
    de.year_quarter     AS expected_year_quarter,
    da.year_month       AS actual_year_month,
    da.year_quarter     AS actual_year_quarter,
    -- Colonnes de catégorisation utiles
    CASE WHEN f.is_late = 1 THEN 'Late' ELSE 'On Time' END AS delivery_status,
    CASE
        WHEN f.delay_days <= 0             THEN 'On Time'
        WHEN f.delay_days BETWEEN 1 AND 3  THEN '1-3 days late'
        WHEN f.delay_days BETWEEN 4 AND 7  THEN '4-7 days late'
        WHEN f.delay_days BETWEEN 8 AND 14 THEN '8-14 days late'
        ELSE '>14 days late'
    END AS delay_bucket
FROM fact_orders f
LEFT JOIN dim_carrier   c   ON f.carrier_id        = c.carrier_id
LEFT JOIN dim_warehouse w   ON f.warehouse_id      = w.warehouse_id
LEFT JOIN dim_customer  cu  ON f.customer_id       = cu.customer_id
LEFT JOIN dim_product   p   ON f.main_product_id   = p.product_id
LEFT JOIN dim_date      de  ON f.expected_date_key = de.date_key
LEFT JOIN dim_date      da  ON f.actual_date_key   = da.date_key;
