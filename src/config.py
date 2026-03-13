"""
config.py
---------
Centralisation de tous les paramètres du projet Supply Chain Dashboard.
Modifier ce fichier pour adapter les chemins, volumes et paramètres métier.
"""

from pathlib import Path

# ─── Racine du projet ──────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent

# ─── Répertoires de données ────────────────────────────────────────────────────
DATA_RAW_DIR       = ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
DATA_EXTERNAL_DIR  = ROOT_DIR / "data" / "external"

# ─── Répertoires SQL / Power BI ───────────────────────────────────────────────
SQL_DIR    = ROOT_DIR / "sql"
POWERBI_DIR = ROOT_DIR / "powerbi"
DOCS_DIR   = ROOT_DIR / "docs"

# ─── Base de données SQLite ────────────────────────────────────────────────────
DB_PATH = ROOT_DIR / "data" / "supply_chain.db"

# ─── Paramètres de génération du dataset ──────────────────────────────────────
GENERATION = {
    "seed":             42,
    "n_orders":         50_000,    # Nombre de commandes principales
    "n_customers":      2_000,
    "n_products":       250,
    "n_carriers":       12,
    "n_warehouses":     18,
    "start_date":       "2022-01-01",
    "end_date":         "2024-12-31",
    "late_rate":        0.18,      # 18 % de commandes en retard (réaliste)
    "null_rate":        0.03,      # 3 % de valeurs manquantes injectées
    "duplicate_rate":   0.005,     # 0.5 % de doublons injectés
}

# ─── Seuils métier ─────────────────────────────────────────────────────────────
BUSINESS = {
    "max_shipping_days":        30,    # Délai max acceptable (jours)
    "late_threshold_days":      0,     # Retard = actual > expected
    "min_order_value":          10.0,
    "max_order_value":          50_000.0,
    "min_shipping_cost":        0.0,
    "max_shipping_cost":        5_000.0,
    "outlier_zscore_threshold": 3.5,
}

# ─── Colonnes attendues (contrat de données) ───────────────────────────────────
ORDERS_COLUMNS = [
    "order_id", "customer_id", "order_date", "expected_delivery_date",
    "actual_delivery_date", "carrier_id", "warehouse_id", "region",
    "country", "order_status", "shipping_cost", "order_value",
    "priority_level",
]

ORDER_LINES_COLUMNS = [
    "order_line_id", "order_id", "product_id",
    "quantity", "unit_price", "discount", "line_total",
]

PRODUCTS_COLUMNS = [
    "product_id", "product_name", "category", "subcategory", "weight", "volume",
]

CARRIERS_COLUMNS = [
    "carrier_id", "carrier_name", "carrier_type", "service_level",
]

WAREHOUSES_COLUMNS = [
    "warehouse_id", "warehouse_name", "city", "region", "country",
]

CUSTOMERS_COLUMNS = [
    "customer_id", "customer_segment", "industry", "country", "region",
]

# ─── Statuts et niveaux de priorité ────────────────────────────────────────────
ORDER_STATUSES   = ["Delivered", "In Transit", "Pending", "Cancelled", "Returned"]
PRIORITY_LEVELS  = ["Standard", "High", "Critical"]
CARRIER_TYPES    = ["Air", "Ground", "Sea", "Rail"]
SERVICE_LEVELS   = ["Economy", "Standard", "Express", "Premium"]
CUSTOMER_SEGMENTS = ["B2B", "B2C", "Enterprise", "SME"]

# ─── Régions / Pays ────────────────────────────────────────────────────────────
REGIONS_COUNTRIES = {
    "Europe":        ["France", "Germany", "Spain", "Italy", "Netherlands", "Poland", "Belgium"],
    "North America": ["USA", "Canada", "Mexico"],
    "Asia Pacific":  ["China", "Japan", "India", "Australia", "South Korea", "Singapore"],
    "Middle East":   ["UAE", "Saudi Arabia", "Turkey"],
    "Africa":        ["South Africa", "Morocco", "Nigeria"],
}

# ─── Catégories de produits ────────────────────────────────────────────────────
PRODUCT_CATEGORIES = {
    "Electronics":     ["Smartphones", "Laptops", "Tablets", "Accessories", "Audio"],
    "Industrial":      ["Machinery", "Tools", "Safety Equipment", "Spare Parts"],
    "Healthcare":      ["Medical Devices", "Pharmaceuticals", "Consumables"],
    "Fashion":         ["Clothing", "Footwear", "Accessories"],
    "Food & Beverage": ["Packaged Goods", "Beverages", "Fresh Produce"],
    "Automotive":      ["Parts", "Accessories", "Lubricants"],
    "Office":          ["Furniture", "Stationery", "IT Equipment"],
}

# ─── Noms de fichiers de sortie ────────────────────────────────────────────────
OUTPUT_FILES = {
    "orders_raw":        DATA_RAW_DIR / "orders.csv",
    "order_lines_raw":   DATA_RAW_DIR / "order_lines.csv",
    "products_raw":      DATA_RAW_DIR / "products.csv",
    "carriers_raw":      DATA_RAW_DIR / "carriers.csv",
    "warehouses_raw":    DATA_RAW_DIR / "warehouses.csv",
    "customers_raw":     DATA_RAW_DIR / "customers.csv",
    "orders_clean":      DATA_PROCESSED_DIR / "orders_clean.csv",
    "order_lines_clean": DATA_PROCESSED_DIR / "order_lines_clean.csv",
    "analytics":         DATA_PROCESSED_DIR / "supply_chain_analytics.csv",
    "dim_date":          DATA_PROCESSED_DIR / "dim_date.csv",
    "dim_customer":      DATA_PROCESSED_DIR / "dim_customer.csv",
    "dim_product":       DATA_PROCESSED_DIR / "dim_product.csv",
    "dim_carrier":       DATA_PROCESSED_DIR / "dim_carrier.csv",
    "dim_warehouse":     DATA_PROCESSED_DIR / "dim_warehouse.csv",
    "fact_orders":       DATA_PROCESSED_DIR / "fact_orders.csv",
    "quality_report":    DATA_PROCESSED_DIR / "quality_report.csv",
}
