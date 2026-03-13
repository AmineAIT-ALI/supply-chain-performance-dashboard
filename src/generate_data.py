"""
generate_data.py
----------------
Génère un dataset synthétique réaliste de supply chain (50 000 commandes).

Le dataset inclut des anomalies volontaires (nulls, doublons, outliers,
incohérences de dates) pour simuler des données brutes réelles et tester
la robustesse du pipeline de nettoyage.

Usage :
    python src/generate_data.py
"""

import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    BUSINESS,
    CARRIER_TYPES,
    CUSTOMER_SEGMENTS,
    GENERATION,
    ORDER_STATUSES,
    OUTPUT_FILES,
    PRIORITY_LEVELS,
    PRODUCT_CATEGORIES,
    REGIONS_COUNTRIES,
    SERVICE_LEVELS,
)
from src.utils import ensure_dirs, get_logger, save_csv

logger = get_logger("generate_data")

# Seed fixe pour la reproductibilité des données générées
rng = np.random.default_rng(GENERATION["seed"])
random.seed(GENERATION["seed"])


# ─── Référentiels ─────────────────────────────────────────────────────────────

def generate_carriers(n: int = None) -> pd.DataFrame:
    """Génère le référentiel des transporteurs.

    Args:
        n: Nombre de transporteurs (défaut : config GENERATION["n_carriers"]).

    Returns:
        DataFrame avec colonnes carrier_id, carrier_name, carrier_type,
        service_level.
    """
    n = n or GENERATION["n_carriers"]
    carrier_names = [
        "FastFreight", "GlobalShip", "NordExpress", "PacificLogistics",
        "EuroTrans", "SwiftCargo", "AtlasFreight", "BlueLine",
        "SkyBridge", "TerraRoute", "ArcticFreight", "MedShip",
    ][:n]
    records = []
    for i, name in enumerate(carrier_names, start=1):
        records.append({
            "carrier_id": f"CAR{i:03d}",
            "carrier_name": name,
            "carrier_type": random.choice(CARRIER_TYPES),
            "service_level": random.choice(SERVICE_LEVELS),
        })
    return pd.DataFrame(records)


def generate_warehouses(n: int = None) -> pd.DataFrame:
    """Génère le référentiel des entrepôts avec localisation géographique.

    Args:
        n: Nombre d'entrepôts (défaut : config GENERATION["n_warehouses"]).

    Returns:
        DataFrame avec colonnes warehouse_id, warehouse_name, region,
        country, city.
    """
    n = n or GENERATION["n_warehouses"]
    locations = [
        ("WH-PARIS",     "Paris",         "Europe",        "France"),
        ("WH-BERLIN",    "Berlin",         "Europe",        "Germany"),
        ("WH-MADRID",    "Madrid",         "Europe",        "Spain"),
        ("WH-MILAN",     "Milan",          "Europe",        "Italy"),
        ("WH-WARSAW",    "Warsaw",         "Europe",        "Poland"),
        ("WH-AMSTERDAM", "Amsterdam",      "Europe",        "Netherlands"),
        ("WH-NYC",       "New York",       "North America", "USA"),
        ("WH-LA",        "Los Angeles",    "North America", "USA"),
        ("WH-CHICAGO",   "Chicago",        "North America", "USA"),
        ("WH-TORONTO",   "Toronto",        "North America", "Canada"),
        ("WH-SHANGHAI",  "Shanghai",       "Asia Pacific",  "China"),
        ("WH-TOKYO",     "Tokyo",          "Asia Pacific",  "Japan"),
        ("WH-MUMBAI",    "Mumbai",         "Asia Pacific",  "India"),
        ("WH-SYDNEY",    "Sydney",         "Asia Pacific",  "Australia"),
        ("WH-SINGAPORE", "Singapore",      "Asia Pacific",  "Singapore"),
        ("WH-DUBAI",     "Dubai",          "Middle East",   "UAE"),
        ("WH-RIYADH",    "Riyadh",         "Middle East",   "Saudi Arabia"),
        ("WH-JOBURG",    "Johannesburg",   "Africa",        "South Africa"),
    ][:n]
    return pd.DataFrame(
        locations,
        columns=["warehouse_id", "warehouse_name", "region", "country"],
    ).assign(city=lambda d: d["warehouse_name"])


def generate_products(n: int = None) -> pd.DataFrame:
    """Génère le catalogue produits avec catégories et attributs physiques.

    Args:
        n: Nombre de produits cibles (défaut : config GENERATION["n_products"]).

    Returns:
        DataFrame avec colonnes product_id, product_name, category,
        subcategory, weight, volume.
    """
    n = n or GENERATION["n_products"]
    records = []
    pid = 1
    for category, subcats in PRODUCT_CATEGORIES.items():
        # Répartition uniforme des produits entre catégories et sous-catégories
        per_sub = max(1, n // (len(PRODUCT_CATEGORIES) * len(subcats)))
        for sub in subcats:
            for _ in range(per_sub):
                if pid > n:
                    break
                records.append({
                    "product_id": f"PRD{pid:04d}",
                    "product_name": f"{sub} Model-{pid:04d}",
                    "category": category,
                    "subcategory": sub,
                    "weight": round(rng.uniform(0.1, 50.0), 2),
                    "volume": round(rng.uniform(0.01, 5.0), 3),
                })
                pid += 1
    return pd.DataFrame(records[:n])


def generate_customers(n: int = None) -> pd.DataFrame:
    """Génère le référentiel clients avec segment et pays d'origine.

    Args:
        n: Nombre de clients (défaut : config GENERATION["n_customers"]).

    Returns:
        DataFrame avec colonnes customer_id, customer_segment, industry,
        country, region.
    """
    n = n or GENERATION["n_customers"]
    all_countries = [
        c for countries in REGIONS_COUNTRIES.values() for c in countries
    ]
    # Mapping inverse pays → région pour dénormalisation rapide
    region_map = {
        c: r for r, countries in REGIONS_COUNTRIES.items() for c in countries
    }
    industries = [
        "Retail", "Manufacturing", "Healthcare", "Technology",
        "Finance", "Logistics", "Automotive", "Energy",
    ]
    records = []
    for i in range(1, n + 1):
        country = random.choice(all_countries)
        records.append({
            "customer_id": f"CUST{i:05d}",
            "customer_segment": random.choice(CUSTOMER_SEGMENTS),
            "industry": random.choice(industries),
            "country": country,
            "region": region_map[country],
        })
    return pd.DataFrame(records)


# ─── Commandes ────────────────────────────────────────────────────────────────

def generate_orders(
    carriers: pd.DataFrame,
    warehouses: pd.DataFrame,
    customers: pd.DataFrame,
    n: int = None,
) -> pd.DataFrame:
    """Génère le dataset principal des commandes avec anomalies volontaires.

    Les anomalies injectées (nulls, doublons, outliers) simulent la réalité
    d'un système ERP non maîtrisé et servent à valider le pipeline de nettoyage.

    Args:
        carriers: Référentiel transporteurs.
        warehouses: Référentiel entrepôts.
        customers: Référentiel clients.
        n: Nombre de commandes cibles (défaut : GENERATION["n_orders"]).

    Returns:
        DataFrame des commandes avec anomalies, prêt pour clean_data.py.
    """
    n = n or GENERATION["n_orders"]
    logger.info(f"Generating {n:,} orders...")

    all_countries = [
        c for countries in REGIONS_COUNTRIES.values() for c in countries
    ]
    region_map = {
        c: r for r, countries in REGIONS_COUNTRIES.items() for c in countries
    }

    start = pd.Timestamp(GENERATION["start_date"])
    end = pd.Timestamp(GENERATION["end_date"])
    day_range = (end - start).days

    # Génération vectorisée des dates et délais pour performances
    order_dates = start + pd.to_timedelta(
        rng.integers(0, day_range, size=n), unit="D"
    )
    expected_days = rng.integers(3, 21, size=n)   # délai promis : 3–20 jours
    actual_offsets = rng.integers(-2, 30, size=n)  # écart réel vs. promis

    # Application du taux de retard configuré : late_rate % de commandes
    # arrivent après la date promise (retard entre +1 et +19 jours)
    late_mask = rng.random(n) < GENERATION["late_rate"]
    actual_days = np.where(
        late_mask,
        expected_days + rng.integers(1, 20, size=n),  # commandes en retard
        expected_days + actual_offsets.clip(-2, 0),   # à l'heure ou en avance
    )

    expected_delivery = order_dates + pd.to_timedelta(expected_days, unit="D")
    actual_delivery = order_dates + pd.to_timedelta(actual_days, unit="D")

    # Statuts cohérents avec l'état de livraison simulé
    statuses = []
    for i in range(n):
        if rng.random() < 0.02:
            statuses.append("Cancelled")
        elif rng.random() < 0.015:
            statuses.append("Returned")
        elif actual_days[i] > 0:
            statuses.append("Delivered")
        else:
            # Commandes sans date de livraison connue → statut intermédiaire
            statuses.append(random.choice(["In Transit", "Pending"]))

    carrier_ids = rng.choice(carriers["carrier_id"].values, size=n)
    warehouse_ids = rng.choice(warehouses["warehouse_id"].values, size=n)
    customer_ids = rng.choice(customers["customer_id"].values, size=n)

    # Pays et région déduits de l'entrepôt d'expédition (pas du client)
    wh_lookup = (
        warehouses.set_index("warehouse_id")[["country", "region"]]
        .to_dict("index")
    )
    countries = [wh_lookup[w]["country"] for w in warehouse_ids]
    regions = [wh_lookup[w]["region"] for w in warehouse_ids]

    # Distribution log-normale des valeurs et coûts (réaliste pour l'e-commerce)
    order_values = rng.lognormal(mean=7.5, sigma=1.2, size=n).clip(
        BUSINESS["min_order_value"], BUSINESS["max_order_value"]
    ).round(2)
    shipping_costs = (
        order_values * rng.uniform(0.02, 0.15, size=n)
    ).clip(
        BUSINESS["min_shipping_cost"], BUSINESS["max_shipping_cost"]
    ).round(2)

    df = pd.DataFrame({
        "order_id": [f"ORD{i:06d}" for i in range(1, n + 1)],
        "customer_id": customer_ids,
        "order_date": order_dates,
        "expected_delivery_date": expected_delivery,
        "actual_delivery_date": actual_delivery,
        "carrier_id": carrier_ids,
        "warehouse_id": warehouse_ids,
        "region": regions,
        "country": countries,
        "order_status": statuses,
        "shipping_cost": shipping_costs,
        "order_value": order_values,
        "priority_level": rng.choice(
            PRIORITY_LEVELS,
            size=n,
            p=[0.60, 0.30, 0.10],  # Standard > High > Critical
        ),
    })

    # ── Injection d'anomalies réalistes ───────────────────────────────────────
    # Nulls aléatoires sur 3 colonnes pour simuler des saisies manquantes
    null_rate = GENERATION["null_rate"]
    for col in ["actual_delivery_date", "shipping_cost", "carrier_id"]:
        mask = rng.random(n) < null_rate
        df.loc[mask, col] = np.nan

    # Quelques coûts aberrants (erreurs de saisie ERP)
    outlier_idx = rng.choice(n, size=max(1, int(n * 0.001)), replace=False)
    df.loc[outlier_idx, "shipping_cost"] = rng.uniform(
        8_000, 15_000, size=len(outlier_idx)
    )

    # Doublons intentionnels pour tester la déduplication
    dup_n = max(1, int(n * GENERATION["duplicate_rate"]))
    dup_rows = df.sample(n=dup_n, random_state=0)
    df = pd.concat([df, dup_rows], ignore_index=True)

    logger.info(
        f"Orders generated: {len(df):,} rows "
        f"(includes {dup_n} intentional duplicates)"
    )
    return df


# ─── Lignes de commande ───────────────────────────────────────────────────────

def generate_order_lines(
    orders: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Génère les lignes de commande (1 à 5 lignes par commande).

    Chaque ligne représente un produit commandé avec sa quantité, son prix
    unitaire et la remise appliquée. Le line_total est calculé directement.

    Args:
        orders: DataFrame des commandes (order_id utilisé comme clé).
        products: Catalogue produits (product_id utilisé pour le tirage).

    Returns:
        DataFrame des lignes de commande.
    """
    logger.info("Generating order lines...")
    order_ids = orders["order_id"].values
    product_ids = products["product_id"].values
    records = []
    line_id = 1

    for oid in order_ids:
        # Nombre de lignes variable pour simuler des commandes multi-produits
        n_lines = rng.integers(1, 6)
        for _ in range(n_lines):
            qty = int(rng.integers(1, 101))
            unit_price = round(float(rng.lognormal(4.0, 1.0)), 2)
            discount = round(
                float(
                    rng.choice(
                        [0.0, 0.05, 0.10, 0.15, 0.20],
                        p=[0.5, 0.2, 0.15, 0.1, 0.05],
                    )
                ),
                2,
            )
            line_total = round(qty * unit_price * (1 - discount), 2)
            records.append({
                "order_line_id": f"OL{line_id:07d}",
                "order_id": oid,
                "product_id": rng.choice(product_ids),
                "quantity": qty,
                "unit_price": unit_price,
                "discount": discount,
                "line_total": line_total,
            })
            line_id += 1

    df = pd.DataFrame(records)
    logger.info(f"Order lines generated: {len(df):,} rows")
    return df


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def main():
    """Point d'entrée du pipeline de génération de données synthétiques."""
    from src.config import DATA_PROCESSED_DIR, DATA_RAW_DIR, OUTPUT_FILES

    ensure_dirs(DATA_RAW_DIR, DATA_PROCESSED_DIR)
    logger.info("=== Data Generation Pipeline ===")

    carriers = generate_carriers()
    warehouses = generate_warehouses()
    products = generate_products()
    customers = generate_customers()
    orders = generate_orders(carriers, warehouses, customers)
    order_lines = generate_order_lines(orders, products)

    save_csv(carriers, OUTPUT_FILES["carriers_raw"], "carriers")
    save_csv(warehouses, OUTPUT_FILES["warehouses_raw"], "warehouses")
    save_csv(products, OUTPUT_FILES["products_raw"], "products")
    save_csv(customers, OUTPUT_FILES["customers_raw"], "customers")
    save_csv(orders, OUTPUT_FILES["orders_raw"], "orders")
    save_csv(order_lines, OUTPUT_FILES["order_lines_raw"], "order_lines")

    logger.info("=== Generation complete ===")
    print("\nSummary:")
    print(f"  Carriers    : {len(carriers):>8,}")
    print(f"  Warehouses  : {len(warehouses):>8,}")
    print(f"  Products    : {len(products):>8,}")
    print(f"  Customers   : {len(customers):>8,}")
    print(f"  Orders      : {len(orders):>8,}")
    print(f"  Order lines : {len(order_lines):>8,}")


if __name__ == "__main__":
    main()
