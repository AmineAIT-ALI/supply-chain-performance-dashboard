"""
kpi_analysis.py
---------------
Calcule et exporte l'ensemble des KPI supply chain depuis fact_orders.

KPI couverts :
  - Vue globale : volumes, CA, coûts, délais, taux de retard
  - Performance transporteurs (late rate, coût moyen, ranking)
  - Performance entrepôts
  - Performance géographique (région / pays)
  - Tendances mensuelles avec croissance MoM
  - Analyse par niveau de priorité
  - Analyse par catégorie produit principale
  - Top/Worst carriers par taux de retard

Usage :
    python src/kpi_analysis.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_PROCESSED_DIR, OUTPUT_FILES
from src.utils import ensure_dirs, get_logger, load_csv, save_csv

logger = get_logger("kpi_analysis")


# ─── Chargement ───────────────────────────────────────────────────────────────

def load_data():
    """Charge fact_orders, analytics et les référentiels transporteurs/entrepôts.

    Returns:
        Tuple (fact, analytics, carriers, warehouses).
    """
    date_cols = [
        "order_date",
        "expected_delivery_date",
        "actual_delivery_date",
    ]
    fact = load_csv(OUTPUT_FILES["fact_orders"], parse_dates=date_cols)
    analytics = load_csv(OUTPUT_FILES["analytics"], parse_dates=date_cols)
    carriers = load_csv(OUTPUT_FILES["carriers_raw"])
    warehouses = load_csv(OUTPUT_FILES["warehouses_raw"])
    return fact, analytics, carriers, warehouses


# ─── KPI Globaux ──────────────────────────────────────────────────────────────

def kpi_global(fact: pd.DataFrame) -> dict:
    """Calcule les KPI agrégés sur l'ensemble du dataset.

    Args:
        fact: Table de faits fact_orders.

    Returns:
        Dictionnaire des KPI globaux (volumes, CA, délais, taux de retard).
    """
    delivered = fact[fact["order_status"] == "Delivered"]
    late_orders = fact[fact["is_late"] == 1]

    return {
        "total_orders": len(fact),
        "total_delivered": len(delivered),
        "total_revenue": round(fact["order_value"].sum(), 2),
        "total_shipping_cost": round(fact["shipping_cost"].sum(), 2),
        "avg_order_value": round(fact["order_value"].mean(), 2),
        "avg_shipping_cost": round(fact["shipping_cost"].mean(), 2),
        "avg_lead_time_days": round(fact["lead_time_days"].mean(), 2),
        "avg_delay_days": round(fact["delay_days"].mean(), 2),
        "on_time_delivery_rate_pct": round(
            (fact["is_late"] == 0).sum() / len(fact) * 100, 2
        ),
        "late_orders_count": len(late_orders),
        "late_orders_pct": round(len(late_orders) / len(fact) * 100, 2),
        # Délai moyen calculé uniquement sur les commandes effectivement en retard
        "avg_delay_when_late_days": (
            round(late_orders["delay_days"].mean(), 2)
            if len(late_orders) > 0
            else 0
        ),
        "avg_shipping_cost_ratio": round(
            fact["shipping_cost_ratio"].mean(), 4
        ),
        "total_items_shipped": int(fact["total_items"].sum()),
    }


# ─── Performance transporteurs ────────────────────────────────────────────────

def kpi_by_carrier(
    fact: pd.DataFrame,
    carriers: pd.DataFrame,
) -> pd.DataFrame:
    """Calcule les KPI de performance par transporteur.

    Inclut un double ranking : par volume de commandes et par taux de retard.
    Les informations descriptives du transporteur sont jointes depuis carriers.

    Args:
        fact: Table de faits fact_orders.
        carriers: Référentiel transporteurs.

    Returns:
        DataFrame trié par volume décroissant avec ranks.
    """
    agg = fact.groupby("carrier_id").agg(
        total_orders=("order_id", "count"),
        total_revenue=("order_value", "sum"),
        total_shipping_cost=("shipping_cost", "sum"),
        avg_shipping_cost=("shipping_cost", "mean"),
        avg_lead_time=("lead_time_days", "mean"),
        avg_delay=("delay_days", "mean"),
        late_orders=("is_late", "sum"),
        total_items=("total_items", "sum"),
    ).reset_index()

    agg["late_rate_pct"] = (
        agg["late_orders"] / agg["total_orders"] * 100
    ).round(2)
    agg["avg_lead_time"] = agg["avg_lead_time"].round(2)
    agg["avg_delay"] = agg["avg_delay"].round(2)
    agg["avg_shipping_cost"] = agg["avg_shipping_cost"].round(2)
    agg["total_revenue"] = agg["total_revenue"].round(2)
    agg["total_shipping_cost"] = agg["total_shipping_cost"].round(2)
    agg["revenue_share_pct"] = (
        agg["total_revenue"] / agg["total_revenue"].sum() * 100
    ).round(2)

    # Ranking dual : meilleur carrier = plus de volume ET moins de retards
    agg["rank_by_volume"] = (
        agg["total_orders"].rank(ascending=False).astype(int)
    )
    agg["rank_by_laterate"] = (
        agg["late_rate_pct"].rank(ascending=True).astype(int)
    )

    return agg.merge(
        carriers[["carrier_id", "carrier_name", "carrier_type", "service_level"]],
        on="carrier_id",
        how="left",
    ).sort_values("total_orders", ascending=False)


# ─── Performance entrepôts ────────────────────────────────────────────────────

def kpi_by_warehouse(
    fact: pd.DataFrame,
    warehouses: pd.DataFrame,
) -> pd.DataFrame:
    """Calcule les KPI de performance par entrepôt.

    Args:
        fact: Table de faits fact_orders.
        warehouses: Référentiel entrepôts.

    Returns:
        DataFrame trié par volume de commandes décroissant.
    """
    agg = fact.groupby("warehouse_id").agg(
        total_orders=("order_id", "count"),
        total_revenue=("order_value", "sum"),
        total_shipping_cost=("shipping_cost", "sum"),
        avg_shipping_cost=("shipping_cost", "mean"),
        avg_lead_time=("lead_time_days", "mean"),
        avg_delay=("delay_days", "mean"),
        late_orders=("is_late", "sum"),
        total_items=("total_items", "sum"),
    ).reset_index()

    agg["late_rate_pct"] = (
        agg["late_orders"] / agg["total_orders"] * 100
    ).round(2)
    agg["avg_lead_time"] = agg["avg_lead_time"].round(2)
    agg["avg_delay"] = agg["avg_delay"].round(2)
    agg["avg_shipping_cost"] = agg["avg_shipping_cost"].round(2)
    agg["total_revenue"] = agg["total_revenue"].round(2)

    return agg.merge(
        warehouses[["warehouse_id", "warehouse_name", "city", "region", "country"]],
        on="warehouse_id",
        how="left",
    ).sort_values("total_orders", ascending=False)


# ─── Performance géographique ─────────────────────────────────────────────────

def kpi_by_region(fact: pd.DataFrame) -> pd.DataFrame:
    """Calcule les KPI agrégés par région et pays.

    Args:
        fact: Table de faits fact_orders.

    Returns:
        DataFrame trié par volume de commandes décroissant.
    """
    agg = fact.groupby(["region", "country"]).agg(
        total_orders=("order_id", "count"),
        total_revenue=("order_value", "sum"),
        avg_lead_time=("lead_time_days", "mean"),
        avg_delay=("delay_days", "mean"),
        late_orders=("is_late", "sum"),
        avg_shipping=("shipping_cost", "mean"),
    ).reset_index()

    agg["late_rate_pct"] = (
        agg["late_orders"] / agg["total_orders"] * 100
    ).round(2)
    agg["avg_lead_time"] = agg["avg_lead_time"].round(2)
    agg["avg_delay"] = agg["avg_delay"].round(2)
    agg["avg_shipping"] = agg["avg_shipping"].round(2)
    agg["total_revenue"] = agg["total_revenue"].round(2)
    agg["revenue_share_pct"] = (
        agg["total_revenue"] / agg["total_revenue"].sum() * 100
    ).round(2)

    return agg.sort_values("total_orders", ascending=False)


# ─── Tendances mensuelles ─────────────────────────────────────────────────────

def kpi_monthly_trends(fact: pd.DataFrame) -> pd.DataFrame:
    """Calcule les KPI mensuels avec croissance mois-sur-mois (MoM).

    La croissance MoM (mom_orders_growth, mom_revenue_growth) est calculée
    sur la série triée chronologiquement via pct_change().

    Args:
        fact: Table de faits fact_orders.

    Returns:
        DataFrame mensuel trié chronologiquement.
    """
    agg = fact.groupby(
        ["order_year", "order_month", "order_year_month"]
    ).agg(
        total_orders=("order_id", "count"),
        total_revenue=("order_value", "sum"),
        total_shipping=("shipping_cost", "sum"),
        avg_lead_time=("lead_time_days", "mean"),
        avg_delay=("delay_days", "mean"),
        late_orders=("is_late", "sum"),
        total_items=("total_items", "sum"),
    ).reset_index()

    agg["late_rate_pct"] = (
        agg["late_orders"] / agg["total_orders"] * 100
    ).round(2)
    agg["avg_lead_time"] = agg["avg_lead_time"].round(2)
    agg["avg_delay"] = agg["avg_delay"].round(2)
    agg["total_revenue"] = agg["total_revenue"].round(2)
    agg["total_shipping"] = agg["total_shipping"].round(2)
    # Croissance mensuelle (NaN pour le premier mois = comportement normal)
    agg["mom_orders_growth"] = (
        agg["total_orders"].pct_change().mul(100).round(2)
    )
    agg["mom_revenue_growth"] = (
        agg["total_revenue"].pct_change().mul(100).round(2)
    )

    return agg.sort_values(["order_year", "order_month"])


# ─── Performance par priorité ─────────────────────────────────────────────────

def kpi_by_priority(fact: pd.DataFrame) -> pd.DataFrame:
    """Calcule les KPI par niveau de priorité (Standard / High / Critical).

    Les résultats sont triés selon l'ordre croissant de criticité :
    Standard → High → Critical.

    Args:
        fact: Table de faits fact_orders.

    Returns:
        DataFrame trié par niveau de priorité croissant.
    """
    agg = fact.groupby("priority_level").agg(
        total_orders=("order_id", "count"),
        total_revenue=("order_value", "sum"),
        avg_lead_time=("lead_time_days", "mean"),
        avg_delay=("delay_days", "mean"),
        late_orders=("is_late", "sum"),
        avg_shipping=("shipping_cost", "mean"),
    ).reset_index()

    agg["late_rate_pct"] = (
        agg["late_orders"] / agg["total_orders"] * 100
    ).round(2)
    agg["share_pct"] = (
        agg["total_orders"] / agg["total_orders"].sum() * 100
    ).round(2)
    agg["avg_lead_time"] = agg["avg_lead_time"].round(2)
    agg["avg_delay"] = agg["avg_delay"].round(2)
    agg["total_revenue"] = agg["total_revenue"].round(2)

    # Ordre métier : Standard=0, High=1, Critical=2
    order_map = {"Standard": 0, "High": 1, "Critical": 2}
    agg["priority_order"] = agg["priority_level"].map(order_map)
    return agg.sort_values("priority_order").drop("priority_order", axis=1)


# ─── Performance par catégorie produit ────────────────────────────────────────

def kpi_by_category(analytics: pd.DataFrame) -> pd.DataFrame:
    """Calcule les KPI par catégorie produit principale.

    Utilise le dataset analytics (qui contient main_category) plutôt que
    fact_orders, car la catégorie produit n'est pas dans la table de faits.

    Args:
        analytics: Dataset analytique enrichi (supply_chain_analytics.csv).

    Returns:
        DataFrame trié par taux de retard décroissant.
    """
    agg = (
        analytics
        .dropna(subset=["main_category"])
        .groupby("main_category")
        .agg(
            total_orders=("order_id", "count"),
            total_revenue=("order_value", "sum"),
            avg_lead_time=("lead_time_days", "mean"),
            avg_delay=("delay_days", "mean"),
            late_orders=("is_late", "sum"),
            avg_shipping=("shipping_cost", "mean"),
        )
        .reset_index()
    )

    agg["late_rate_pct"] = (
        agg["late_orders"] / agg["total_orders"] * 100
    ).round(2)
    agg["avg_lead_time"] = agg["avg_lead_time"].round(2)
    agg["avg_delay"] = agg["avg_delay"].round(2)
    agg["total_revenue"] = agg["total_revenue"].round(2)

    return agg.sort_values("late_rate_pct", ascending=False)


# ─── Top / Worst performers ───────────────────────────────────────────────────

def top_worst_carriers(
    carrier_kpis: pd.DataFrame,
    n: int = 3,
) -> dict:
    """Retourne les n meilleurs et n pires transporteurs par taux de retard.

    Args:
        carrier_kpis: Résultat de kpi_by_carrier().
        n: Nombre de transporteurs à retourner dans chaque groupe.

    Returns:
        Dict avec clés "top_performers" et "worst_performers".
    """
    cols = ["carrier_name", "late_rate_pct", "total_orders"]
    top = carrier_kpis.nsmallest(n, "late_rate_pct")[cols]
    worst = carrier_kpis.nlargest(n, "late_rate_pct")[cols]
    return {"top_performers": top, "worst_performers": worst}


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def main():
    """Point d'entrée du pipeline d'analyse KPI.

    Calcule tous les KPI, sauvegarde les fichiers CSV dans data/processed/kpis/
    et affiche un résumé console.
    """
    ensure_dirs(DATA_PROCESSED_DIR)
    logger.info("=== KPI Analysis Pipeline ===")

    fact, analytics, carriers, warehouses = load_data()

    # Calcul de tous les KPI
    global_kpis = kpi_global(fact)
    carrier_kpis = kpi_by_carrier(fact, carriers)
    warehouse_kpis = kpi_by_warehouse(fact, warehouses)
    region_kpis = kpi_by_region(fact)
    monthly_kpis = kpi_monthly_trends(fact)
    priority_kpis = kpi_by_priority(fact)
    category_kpis = kpi_by_category(analytics)

    # Sauvegarde des tableaux KPI dans un sous-répertoire dédié
    kpi_dir = DATA_PROCESSED_DIR / "kpis"
    kpi_dir.mkdir(exist_ok=True)

    save_csv(carrier_kpis, kpi_dir / "kpi_by_carrier.csv", "kpi_by_carrier")
    save_csv(
        warehouse_kpis,
        kpi_dir / "kpi_by_warehouse.csv",
        "kpi_by_warehouse",
    )
    save_csv(region_kpis, kpi_dir / "kpi_by_region.csv", "kpi_by_region")
    save_csv(monthly_kpis, kpi_dir / "kpi_monthly.csv", "kpi_monthly")
    save_csv(
        priority_kpis,
        kpi_dir / "kpi_by_priority.csv",
        "kpi_by_priority",
    )
    save_csv(
        category_kpis,
        kpi_dir / "kpi_by_category.csv",
        "kpi_by_category",
    )

    # KPI globaux sauvegardés comme une seule ligne (format compatible BI)
    global_df = pd.DataFrame([global_kpis])
    save_csv(global_df, kpi_dir / "kpi_global.csv", "kpi_global")

    # Affichage console du résumé exécutif
    top_worst = top_worst_carriers(carrier_kpis)

    print("\n" + "=" * 60)
    print("  SUPPLY CHAIN KPI SUMMARY")
    print("=" * 60)
    print(
        f"  Total orders          : "
        f"{global_kpis['total_orders']:>12,}"
    )
    print(
        f"  Total revenue         : "
        f"${global_kpis['total_revenue']:>14,.2f}"
    )
    print(
        f"  Total shipping cost   : "
        f"${global_kpis['total_shipping_cost']:>14,.2f}"
    )
    print(
        f"  Avg order value       : "
        f"${global_kpis['avg_order_value']:>14,.2f}"
    )
    print(
        f"  Avg lead time         : "
        f"{global_kpis['avg_lead_time_days']:>11.1f} days"
    )
    print(
        f"  On-time delivery rate : "
        f"{global_kpis['on_time_delivery_rate_pct']:>11.1f} %"
    )
    print(
        f"  Late orders           : "
        f"{global_kpis['late_orders_count']:>12,}"
    )
    print(
        f"  Late order rate       : "
        f"{global_kpis['late_orders_pct']:>11.1f} %"
    )
    print(
        f"  Avg delay (late only) : "
        f"{global_kpis['avg_delay_when_late_days']:>11.1f} days"
    )
    print("=" * 60)
    print("\nTop 3 carriers (lowest late rate):")
    print(top_worst["top_performers"].to_string(index=False))
    print("\nWorst 3 carriers (highest late rate):")
    print(top_worst["worst_performers"].to_string(index=False))
    print("=" * 60)

    logger.info("=== KPI Analysis complete ===")


if __name__ == "__main__":
    main()
