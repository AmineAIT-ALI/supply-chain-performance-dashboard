"""
clean_data.py
-------------
Pipeline de nettoyage des données brutes de supply chain.

Étapes couvertes :
  1. Standardisation des noms de colonnes
  2. Suppression des doublons sur order_id
  3. Conversion et validation des types (dates, numériques)
  4. Imputation des valeurs manquantes (carrier_id, dates, coûts)
  5. Détection et plafonnement des outliers via z-score
  6. Vérifications de cohérence métier (dates, coûts négatifs)
  7. Standardisation des catégories (statuts, priorités)
  8. Génération du rapport qualité avant/après nettoyage

Usage :
    python src/clean_data.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    BUSINESS,
    ORDER_STATUSES,
    ORDERS_COLUMNS,
    ORDER_LINES_COLUMNS,
    OUTPUT_FILES,
    PRIORITY_LEVELS,
)
from src.utils import (
    build_quality_report,
    ensure_dirs,
    get_logger,
    load_csv,
    missing_summary,
    safe_parse_dates,
    save_csv,
    zscore_outliers,
)

logger = get_logger("clean_data")


# ─── Nettoyage des commandes ───────────────────────────────────────────────────

def clean_orders(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Nettoie le dataset des commandes brutes.

    Applique dans l'ordre : dédoublonnage, typage, imputation,
    gestion des outliers, cohérence métier et standardisation des
    valeurs catégorielles.

    Args:
        df_raw: DataFrame brut chargé depuis orders.csv.

    Returns:
        DataFrame nettoyé, trié par order_date.
    """
    logger.info(f"Cleaning orders: {len(df_raw):,} raw rows")
    df = df_raw.copy()

    # 1. Standardisation des noms de colonnes (snake_case, sans espaces ni tirets)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-]+", "_", regex=True)
    )

    # 2. Suppression des doublons exacts sur la clé primaire
    n_before = len(df)
    df = df.drop_duplicates(subset=["order_id"])
    logger.info(f"  Duplicates removed (order_id): {n_before - len(df):,}")

    # 3. Parse des colonnes de dates (erreurs converties en NaT)
    date_cols = [
        "order_date",
        "expected_delivery_date",
        "actual_delivery_date",
    ]
    df = safe_parse_dates(df, date_cols)

    # 4. Imputation des valeurs manquantes
    # carrier_id : remplacé par la modalité la plus fréquente.
    # Fallback sur "CAR001" si la colonne est entièrement nulle.
    if df["carrier_id"].isnull().any():
        mode_result = df["carrier_id"].mode()
        mode_carrier = mode_result.iloc[0] if len(mode_result) > 0 else "CAR001"
        df["carrier_id"] = df["carrier_id"].fillna(mode_carrier)
        logger.info(f"  carrier_id nulls filled with mode: {mode_carrier}")

    # actual_delivery_date manquant : imputation neutre = expected_delivery_date.
    # Hypothèse conservative : si la date est inconnue, on suppose une livraison
    # à temps plutôt qu'un retard arbitraire (+2j antérieur biaisant le late rate).
    mask_no_delivery = df["actual_delivery_date"].isnull()
    df.loc[mask_no_delivery, "actual_delivery_date"] = (
        df.loc[mask_no_delivery, "expected_delivery_date"]
    )
    logger.info(
        f"  actual_delivery_date imputed: {mask_no_delivery.sum():,} rows"
    )

    # shipping_cost manquant : médiane par transporteur (plus représentative
    # que la médiane globale car les coûts varient fortement selon le carrier).
    mask_no_cost = df["shipping_cost"].isnull()
    df["shipping_cost"] = df.groupby("carrier_id")["shipping_cost"].transform(
        lambda x: x.fillna(x.median())
    )
    # Fallback sur la médiane globale si un carrier n'a aucune valeur connue
    remaining_nulls = df["shipping_cost"].isnull()
    df.loc[remaining_nulls, "shipping_cost"] = df["shipping_cost"].median()
    logger.info(
        f"  shipping_cost nulls imputed: {mask_no_cost.sum():,} rows"
    )

    # 5. Conversion des types numériques (coerce → NaN → 0.0 par sécurité)
    df["shipping_cost"] = (
        pd.to_numeric(df["shipping_cost"], errors="coerce")
        .fillna(0.0)
        .round(2)
    )
    df["order_value"] = (
        pd.to_numeric(df["order_value"], errors="coerce")
        .fillna(0.0)
        .round(2)
    )

    # 6. Plafonnement des outliers de coût logistique au 99e percentile
    cost_outliers = zscore_outliers(
        df["shipping_cost"],
        threshold=BUSINESS["outlier_zscore_threshold"],
    )
    if cost_outliers.any():
        cap = df["shipping_cost"].quantile(0.99)
        df.loc[cost_outliers, "shipping_cost"] = cap
        logger.info(
            f"  shipping_cost outliers capped at {cap:.2f}: "
            f"{cost_outliers.sum():,} rows"
        )

    # 7. Vérifications de cohérence métier
    # a) La date de livraison effective ne peut pas précéder la date de commande
    incoherent_dates = df["actual_delivery_date"] < df["order_date"]
    df.loc[incoherent_dates, "actual_delivery_date"] = (
        df.loc[incoherent_dates, "order_date"] + pd.Timedelta(days=5)
    )
    logger.info(
        f"  Incoherent delivery dates corrected: {incoherent_dates.sum():,}"
    )

    # b) Les coûts et valeurs ne peuvent pas être négatifs
    df.loc[df["shipping_cost"] < 0, "shipping_cost"] = 0.0
    df.loc[df["order_value"] < 0, "order_value"] = df["order_value"].abs()

    # 8. Standardisation des valeurs catégorielles
    # Les statuts inconnus sont remplacés par "Delivered" (valeur la plus sûre)
    df["order_status"] = df["order_status"].str.strip().str.title()
    valid_statuses = set(ORDER_STATUSES)
    unknown_status = ~df["order_status"].isin(valid_statuses)
    df.loc[unknown_status, "order_status"] = "Delivered"
    logger.info(
        f"  Unknown order_status normalized: {unknown_status.sum():,}"
    )

    # Les priorités inconnues sont ramenées au niveau "Standard" par défaut
    df["priority_level"] = df["priority_level"].str.strip().str.title()
    valid_prio = set(PRIORITY_LEVELS)
    unknown_prio = ~df["priority_level"].isin(valid_prio)
    df.loc[unknown_prio, "priority_level"] = "Standard"

    # 9. Suppression des lignes irrecupérables (clé primaire ou date manquante)
    n_before = len(df)
    df = df.dropna(subset=["order_id", "order_date"])
    logger.info(
        f"  Rows dropped (null key/date): {n_before - len(df):,}"
    )

    # 10. Tri chronologique et réinitialisation de l'index
    df = df.sort_values("order_date").reset_index(drop=True)
    logger.info(f"Orders cleaned: {len(df):,} rows")
    return df


# ─── Nettoyage des lignes de commande ─────────────────────────────────────────

def clean_order_lines(
    df_raw: pd.DataFrame,
    valid_order_ids: set,
) -> pd.DataFrame:
    """Nettoie les lignes de commande et vérifie l'intégrité référentielle.

    Supprime les lignes orphelines (order_id absent de orders_clean),
    garantit des quantités et prix strictement positifs, et recalcule
    line_total pour assurer la cohérence financière.

    Args:
        df_raw: DataFrame brut chargé depuis order_lines.csv.
        valid_order_ids: Ensemble des order_id valides issus de clean_orders.

    Returns:
        DataFrame de lignes nettoyé.
    """
    logger.info(f"Cleaning order lines: {len(df_raw):,} raw rows")
    df = df_raw.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-]+", "_", regex=True)
    )

    # Suppression des doublons sur la clé de ligne
    n_before = len(df)
    df = df.drop_duplicates(subset=["order_line_id"])
    logger.info(f"  Duplicates removed: {n_before - len(df):,}")

    # Intégrité référentielle : une ligne sans commande parente est orpheline
    n_before = len(df)
    df = df[df["order_id"].isin(valid_order_ids)]
    logger.info(
        f"  Orphan lines removed (no matching order): {n_before - len(df):,}"
    )

    # Conversion numérique de toutes les métriques quantitatives
    for col in ["quantity", "unit_price", "discount", "line_total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Filtres métier : quantité et prix unitaire strictement positifs
    df = df[df["quantity"].fillna(0) > 0]
    df = df[df["unit_price"].fillna(0) > 0]

    # Remise bornée entre 0 et 1 (une remise > 100% n'a pas de sens métier)
    df["discount"] = df["discount"].clip(0.0, 1.0).fillna(0.0)

    # Recalcul du line_total pour garantir la cohérence après corrections
    df["line_total"] = (
        df["quantity"] * df["unit_price"] * (1 - df["discount"])
    ).round(2)

    # Suppression des lignes avec des clés manquantes
    df = df.dropna(subset=["order_line_id", "order_id", "product_id"])
    df = df.reset_index(drop=True)

    logger.info(f"Order lines cleaned: {len(df):,} rows")
    return df


# ─── Pipeline principal ────────────────────────────────────────────────────────

def main():
    """Point d'entrée du pipeline de nettoyage.

    Charge les données brutes, applique le nettoyage, génère un rapport
    qualité et sauvegarde les fichiers nettoyés dans data/processed/.
    """
    ensure_dirs(OUTPUT_FILES["orders_clean"].parent)
    logger.info("=== Data Cleaning Pipeline ===")

    # Chargement des données brutes
    orders_raw = load_csv(OUTPUT_FILES["orders_raw"])
    order_lines_raw = load_csv(OUTPUT_FILES["order_lines_raw"])

    # Snapshot avant nettoyage pour le rapport qualité
    orders_before = orders_raw.copy()

    # Nettoyage
    orders_clean = clean_orders(orders_raw)
    order_lines_clean = clean_order_lines(
        order_lines_raw,
        valid_order_ids=set(orders_clean["order_id"]),
    )

    # Génération et sauvegarde du rapport qualité
    quality_report = build_quality_report(orders_before, orders_clean, "orders")
    save_csv(quality_report, OUTPUT_FILES["quality_report"], "quality_report")

    # Sauvegarde des données nettoyées
    save_csv(orders_clean, OUTPUT_FILES["orders_clean"], "orders_clean")
    save_csv(
        order_lines_clean,
        OUTPUT_FILES["order_lines_clean"],
        "order_lines_clean",
    )

    # Vérification finale : aucun null ne doit subsister dans les colonnes clés
    remaining_nulls = missing_summary(orders_clean)
    if not remaining_nulls.empty:
        logger.info(f"\nRemaining nulls in orders_clean:\n{remaining_nulls}")
    else:
        logger.info("No remaining nulls in orders_clean.")

    logger.info("=== Cleaning complete ===")
    print("\nCleaning summary:")
    print(f"  Orders raw     : {len(orders_raw):>10,}")
    print(f"  Orders clean   : {len(orders_clean):>10,}")
    print(f"  Lines raw      : {len(order_lines_raw):>10,}")
    print(f"  Lines clean    : {len(order_lines_clean):>10,}")


if __name__ == "__main__":
    main()
