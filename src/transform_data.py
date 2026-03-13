"""
transform_data.py
-----------------
Transforme les données nettoyées en modèle dimensionnel (schéma en étoile)
et en dataset analytique enrichi.

Produit :
  - dim_date       : dimension calendaire complète (2022–2024)
  - dim_customer   : dimension client
  - dim_product    : dimension produit
  - dim_carrier    : dimension transporteur
  - dim_warehouse  : dimension entrepôt
  - fact_orders    : table de faits (grain : 1 commande)
  - supply_chain_analytics.csv : vue dénormalisée prête pour Power BI / SQL

Usage :
    python src/transform_data.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import GENERATION, OUTPUT_FILES
from src.utils import (
    compute_delay_days,
    delivery_lead_time,
    ensure_dirs,
    get_logger,
    is_late,
    load_csv,
    save_csv,
    shipping_cost_ratio,
)

logger = get_logger("transform_data")


# ─── Dimension Date ───────────────────────────────────────────────────────────

def build_dim_date(start: str, end: str) -> pd.DataFrame:
    """Génère une dimension date complète avec tous les attributs temporels.

    Couvre la plage start–end à la granularité journalière.
    La clé date_key est au format YYYYMMDD (entier) pour jointure rapide.

    Args:
        start: Date de début (format "YYYY-MM-DD").
        end: Date de fin (format "YYYY-MM-DD").

    Returns:
        DataFrame de la dimension date.
    """
    dates = pd.date_range(start=start, end=end, freq="D")
    df = pd.DataFrame({"date": dates})
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["month_abbr"] = df["date"].dt.strftime("%b")
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_month"] = df["date"].dt.day
    df["day_of_week"] = df["date"].dt.dayofweek   # 0 = lundi
    df["day_name"] = df["date"].dt.strftime("%A")
    df["is_weekend"] = df["day_of_week"].isin([5, 6])
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    df["year_quarter"] = (
        df["year"].astype(str) + "-Q" + df["quarter"].astype(str)
    )
    return df


# ─── Dimensions clients / produits / transporteurs / entrepôts ────────────────

def build_dim_customer(customers: pd.DataFrame) -> pd.DataFrame:
    """Construit la dimension client depuis le référentiel brut."""
    return (
        customers[["customer_id", "customer_segment", "industry", "country", "region"]]
        .drop_duplicates("customer_id")
        .reset_index(drop=True)
    )


def build_dim_product(products: pd.DataFrame) -> pd.DataFrame:
    """Construit la dimension produit depuis le catalogue brut."""
    return (
        products[["product_id", "product_name", "category", "subcategory",
                  "weight", "volume"]]
        .drop_duplicates("product_id")
        .reset_index(drop=True)
    )


def build_dim_carrier(carriers: pd.DataFrame) -> pd.DataFrame:
    """Construit la dimension transporteur depuis le référentiel brut."""
    return (
        carriers[["carrier_id", "carrier_name", "carrier_type", "service_level"]]
        .drop_duplicates("carrier_id")
        .reset_index(drop=True)
    )


def build_dim_warehouse(warehouses: pd.DataFrame) -> pd.DataFrame:
    """Construit la dimension entrepôt depuis le référentiel brut."""
    return (
        warehouses[["warehouse_id", "warehouse_name", "city", "region", "country"]]
        .drop_duplicates("warehouse_id")
        .reset_index(drop=True)
    )


# ─── Table de faits ───────────────────────────────────────────────────────────

def build_fact_orders(
    orders: pd.DataFrame,
    order_lines: pd.DataFrame,
) -> pd.DataFrame:
    """Construit la table de faits à granularité commande.

    Agrège les métriques des lignes de commande (quantités, prix, remises)
    au niveau order_id, calcule les KPI logistiques (délai, retard, lead time)
    et identifie le produit principal (plus haute valeur de ligne).

    Args:
        orders: Commandes nettoyées.
        order_lines: Lignes de commande nettoyées.

    Returns:
        fact_orders avec 30 colonnes couvrant toutes les dimensions FK et KPI.
    """
    logger.info("Building fact_orders...")

    # Agrégation des lignes de commande au niveau order_id
    lines_agg = order_lines.groupby("order_id").agg(
        total_items=("quantity", "sum"),
        total_lines=("order_line_id", "count"),
        avg_unit_price=("unit_price", "mean"),
        avg_discount=("discount", "mean"),
        lines_total_value=("line_total", "sum"),
    ).reset_index()

    lines_agg["total_items"] = lines_agg["total_items"].astype(int)
    lines_agg["avg_unit_price"] = lines_agg["avg_unit_price"].round(2)
    lines_agg["avg_discount"] = lines_agg["avg_discount"].round(4)
    lines_agg["lines_total_value"] = lines_agg["lines_total_value"].round(2)

    # Fusion commandes + agrégats lignes
    fact = orders.merge(lines_agg, on="order_id", how="left")

    # Clés temporelles au format YYYYMMDD pour jointure avec dim_date
    for date_col, key_col in [
        ("order_date", "order_date_key"),
        ("expected_delivery_date", "expected_date_key"),
        ("actual_delivery_date", "actual_date_key"),
    ]:
        fact[key_col] = (
            pd.to_datetime(fact[date_col])
            .dt.strftime("%Y%m%d")
            .astype("Int64")  # Int64 nullable pour gérer les NaT résiduels
        )

    # KPI logistiques calculés
    fact["delay_days"] = compute_delay_days(fact)
    fact["is_late"] = is_late(fact["delay_days"]).astype(int)
    fact["lead_time_days"] = delivery_lead_time(fact)
    fact["shipping_cost_ratio"] = shipping_cost_ratio(fact)

    # Attributs temporels dénormalisés (évite les jointures répétées côté BI)
    fact["order_year"] = fact["order_date"].dt.year
    fact["order_month"] = fact["order_date"].dt.month
    fact["order_quarter"] = fact["order_date"].dt.quarter
    fact["order_year_month"] = (
        fact["order_date"].dt.to_period("M").astype(str)
    )

    # Produit principal par commande : celui avec la valeur de ligne la plus haute.
    # Ce choix dénormalise une FK vers dim_product dans fact_orders.
    top_product = (
        order_lines
        .sort_values("line_total", ascending=False)
        .groupby("order_id")
        .first()[["product_id"]]
        .rename(columns={"product_id": "main_product_id"})
        .reset_index()
    )
    fact = fact.merge(top_product, on="order_id", how="left")

    # Nettoyage final : les délais NaN (dates manquantes) → 0
    fact["delay_days"] = fact["delay_days"].fillna(0).astype(int)
    fact["lead_time_days"] = fact["lead_time_days"].fillna(0).astype(int)

    # Sélection et ordonnancement des colonnes de la table de faits
    fact_cols = [
        "order_id", "customer_id", "carrier_id", "warehouse_id",
        "main_product_id",
        "order_date_key", "expected_date_key", "actual_date_key",
        "order_date", "expected_delivery_date", "actual_delivery_date",
        "order_year", "order_month", "order_quarter", "order_year_month",
        "region", "country",
        "order_status", "priority_level",
        "order_value", "shipping_cost", "shipping_cost_ratio",
        "total_items", "total_lines", "avg_unit_price",
        "avg_discount", "lines_total_value",
        "delay_days", "is_late", "lead_time_days",
    ]
    fact = fact[[c for c in fact_cols if c in fact.columns]]
    logger.info(
        f"fact_orders built: {len(fact):,} rows × {fact.shape[1]} cols"
    )
    return fact


# ─── Dataset analytique enrichi ───────────────────────────────────────────────

def build_analytics_dataset(
    fact: pd.DataFrame,
    carriers: pd.DataFrame,
    warehouses: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Construit le dataset analytique plat (dénormalisé) pour Power BI / SQL.

    Jointure de fact_orders avec toutes les dimensions pour obtenir un fichier
    unique auto-suffisant. Ajoute des indicateurs binaires et la catégorisation
    des retards.

    Note : Les colonnes warehouse_region et warehouse_country sont renommées
    pour éviter le conflit avec fact_orders.region et fact_orders.country.

    Args:
        fact: Table de faits construite par build_fact_orders.
        carriers: Référentiel transporteurs.
        warehouses: Référentiel entrepôts.
        products: Catalogue produits (pour main_category / main_subcategory).

    Returns:
        DataFrame dénormalisé de 43 colonnes.
    """
    logger.info("Building analytics dataset...")

    # Jointure avec les dimensions transporteur et entrepôt
    analytics = fact.merge(
        carriers[["carrier_id", "carrier_name", "carrier_type", "service_level"]],
        on="carrier_id",
        how="left",
    ).merge(
        warehouses[["warehouse_id", "warehouse_name", "city",
                    "region", "country"]].rename(columns={
            "region": "warehouse_region",
            "country": "warehouse_country",
        }),
        on="warehouse_id",
        how="left",
    )

    # Jointure produit principal : récupère catégorie et sous-catégorie
    # via main_product_id déjà présent dans fact (évite de recalculer top_product)
    analytics = analytics.merge(
        products[["product_id", "category", "subcategory"]].rename(columns={
            "product_id": "main_product_id",
            "category": "main_category",
            "subcategory": "main_subcategory",
        }),
        on="main_product_id",
        how="left",
    )

    # Indicateurs binaires utiles pour les filtres Power BI
    analytics["is_on_time"] = (analytics["is_late"] == 0).astype(int)
    analytics["is_critical"] = (
        analytics["priority_level"] == "Critical"
    ).astype(int)
    # is_high_value : valeur de commande dans le quartile supérieur (Q3)
    analytics["is_high_value"] = (
        analytics["order_value"] >= analytics["order_value"].quantile(0.75)
    ).astype(int)

    # Bucket de retard pour regroupement graphique
    analytics["delay_bucket"] = pd.cut(
        analytics["delay_days"],
        bins=[-float("inf"), 0, 3, 7, 14, float("inf")],
        labels=[
            "On Time", "1-3 days late", "4-7 days late",
            "8-14 days late", ">14 days late",
        ],
    )

    logger.info(
        f"Analytics dataset built: {len(analytics):,} rows "
        f"× {analytics.shape[1]} cols"
    )
    return analytics


# ─── Pipeline principal ────────────────────────────────────────────────────────

def main():
    """Point d'entrée du pipeline de transformation.

    Charge les données nettoyées, construit toutes les dimensions et la table
    de faits, puis sauvegarde l'ensemble dans data/processed/.
    """
    ensure_dirs(OUTPUT_FILES["orders_clean"].parent)
    logger.info("=== Transformation Pipeline ===")

    # Chargement des données nettoyées et référentiels
    orders = load_csv(
        OUTPUT_FILES["orders_clean"],
        parse_dates=[
            "order_date", "expected_delivery_date", "actual_delivery_date",
        ],
    )
    order_lines = load_csv(OUTPUT_FILES["order_lines_clean"])
    carriers = load_csv(OUTPUT_FILES["carriers_raw"])
    warehouses = load_csv(OUTPUT_FILES["warehouses_raw"])
    products = load_csv(OUTPUT_FILES["products_raw"])
    customers = load_csv(OUTPUT_FILES["customers_raw"])

    # Construction des dimensions
    dim_date = build_dim_date(GENERATION["start_date"], GENERATION["end_date"])
    dim_customer = build_dim_customer(customers)
    dim_product = build_dim_product(products)
    dim_carrier = build_dim_carrier(carriers)
    dim_warehouse = build_dim_warehouse(warehouses)

    # Construction de la table de faits
    fact_orders = build_fact_orders(orders, order_lines)

    # Construction du dataset analytique plat
    analytics = build_analytics_dataset(
        fact_orders, carriers, warehouses, products
    )

    # Sauvegarde de tous les fichiers du modèle dimensionnel
    save_csv(dim_date, OUTPUT_FILES["dim_date"], "dim_date")
    save_csv(dim_customer, OUTPUT_FILES["dim_customer"], "dim_customer")
    save_csv(dim_product, OUTPUT_FILES["dim_product"], "dim_product")
    save_csv(dim_carrier, OUTPUT_FILES["dim_carrier"], "dim_carrier")
    save_csv(dim_warehouse, OUTPUT_FILES["dim_warehouse"], "dim_warehouse")
    save_csv(fact_orders, OUTPUT_FILES["fact_orders"], "fact_orders")
    save_csv(analytics, OUTPUT_FILES["analytics"], "supply_chain_analytics")

    logger.info("=== Transformation complete ===")
    print("\nModel summary:")
    print(f"  dim_date      : {len(dim_date):>8,} rows")
    print(f"  dim_customer  : {len(dim_customer):>8,} rows")
    print(f"  dim_product   : {len(dim_product):>8,} rows")
    print(f"  dim_carrier   : {len(dim_carrier):>8,} rows")
    print(f"  dim_warehouse : {len(dim_warehouse):>8,} rows")
    print(f"  fact_orders   : {len(fact_orders):>8,} rows")
    print(f"  analytics     : {len(analytics):>8,} rows")


if __name__ == "__main__":
    main()
