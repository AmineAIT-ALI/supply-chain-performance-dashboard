-- =============================================================================
-- schema.sql
-- Supply Chain Performance Dashboard — Schéma relationnel (SQLite compatible)
-- =============================================================================
-- Modèle dimensionnel en schéma en étoile
-- Grain de la table de faits : 1 ligne = 1 commande
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- Dimensions
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INTEGER PRIMARY KEY,    -- YYYYMMDD (ex : 20230415)
    date            TEXT NOT NULL,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,       -- 1–4
    month           INTEGER NOT NULL,       -- 1–12
    month_name      TEXT NOT NULL,
    month_abbr      TEXT NOT NULL,
    week            INTEGER NOT NULL,       -- Semaine ISO
    day_of_month    INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,       -- 0=Lundi, 6=Dimanche
    day_name        TEXT NOT NULL,
    is_weekend      INTEGER NOT NULL DEFAULT 0,  -- 0/1 booléen
    year_month      TEXT NOT NULL,          -- ex : "2023-04"
    year_quarter    TEXT NOT NULL           -- ex : "2023-Q2"
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id      TEXT PRIMARY KEY,
    customer_segment TEXT NOT NULL,         -- B2B, B2C, Enterprise, SME
    industry         TEXT NOT NULL,
    country          TEXT NOT NULL,
    region           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    subcategory  TEXT NOT NULL,
    weight       REAL,                      -- kg
    volume       REAL                       -- m³
);

CREATE TABLE IF NOT EXISTS dim_carrier (
    carrier_id    TEXT PRIMARY KEY,
    carrier_name  TEXT NOT NULL,
    carrier_type  TEXT NOT NULL,            -- Air, Ground, Sea, Rail
    service_level TEXT NOT NULL             -- Economy, Standard, Express, Premium
);

CREATE TABLE IF NOT EXISTS dim_warehouse (
    warehouse_id   TEXT PRIMARY KEY,
    warehouse_name TEXT NOT NULL,
    city           TEXT NOT NULL,
    region         TEXT NOT NULL,
    country        TEXT NOT NULL
);

-- -----------------------------------------------------------------------------
-- Table de faits — Grain : 1 commande
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS fact_orders (
    -- Clé primaire
    order_id            TEXT PRIMARY KEY,

    -- Clés étrangères dimensions
    customer_id         TEXT REFERENCES dim_customer(customer_id),
    carrier_id          TEXT REFERENCES dim_carrier(carrier_id),
    warehouse_id        TEXT REFERENCES dim_warehouse(warehouse_id),
    main_product_id     TEXT REFERENCES dim_product(product_id),

    -- Clés de dates (vers dim_date)
    order_date_key      INTEGER REFERENCES dim_date(date_key),
    expected_date_key   INTEGER REFERENCES dim_date(date_key),
    actual_date_key     INTEGER REFERENCES dim_date(date_key),

    -- Dates brutes (pour calculs directs)
    order_date              TEXT NOT NULL,
    expected_delivery_date  TEXT,
    actual_delivery_date    TEXT,

    -- Attributs temporels dénormalisés (performance)
    order_year          INTEGER NOT NULL,
    order_month         INTEGER NOT NULL,
    order_quarter       INTEGER NOT NULL,
    order_year_month    TEXT NOT NULL,

    -- Attributs géographiques
    region              TEXT NOT NULL,
    country             TEXT NOT NULL,

    -- Attributs de commande
    order_status        TEXT NOT NULL,
    priority_level      TEXT NOT NULL,

    -- Métriques financières
    order_value         REAL NOT NULL DEFAULT 0,
    shipping_cost       REAL NOT NULL DEFAULT 0,
    shipping_cost_ratio REAL,

    -- Métriques produit (agrégées des lignes)
    total_items         INTEGER DEFAULT 0,
    total_lines         INTEGER DEFAULT 0,
    avg_unit_price      REAL,
    avg_discount        REAL,
    lines_total_value   REAL,

    -- Métriques de performance logistique
    delay_days          INTEGER NOT NULL DEFAULT 0,
    is_late             INTEGER NOT NULL DEFAULT 0,  -- 0/1
    lead_time_days      INTEGER NOT NULL DEFAULT 0
);

-- =============================================================================
-- Commentaires sur les relations
-- =============================================================================
-- fact_orders.customer_id  → dim_customer.customer_id
-- fact_orders.carrier_id   → dim_carrier.carrier_id
-- fact_orders.warehouse_id → dim_warehouse.warehouse_id
-- fact_orders.order_date_key → dim_date.date_key
-- fact_orders.expected_date_key → dim_date.date_key
-- fact_orders.actual_date_key → dim_date.date_key
-- =============================================================================
