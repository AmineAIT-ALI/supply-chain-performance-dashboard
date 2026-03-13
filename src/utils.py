"""
utils.py
--------
Fonctions utilitaires partagées entre les modules du pipeline.

Contient :
- Logging centralisé
- Chronomètre de blocs
- I/O CSV (chargement / sauvegarde)
- Résumés qualité (nulls, doublons, outliers)
- Helpers de feature engineering (délais, ratios)
- Construction du rapport qualité avant/après nettoyage
"""

import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ─── Logging ──────────────────────────────────────────────────────────────────

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Retourne un logger formaté de façon uniforme pour le pipeline.

    Chaque module doit appeler get_logger(__name__) en tête de fichier
    pour garantir des messages cohérents dans la console.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# ─── Chronomètre ──────────────────────────────────────────────────────────────

class Timer:
    """Context manager pour mesurer le temps d'exécution d'un bloc.

    Usage :
        with Timer("étape chargement"):
            df = pd.read_csv(...)
    """

    def __init__(self, label: str = ""):
        self.label = label

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed = time.perf_counter() - self._start
        print(f"  [{self.label}] {elapsed:.2f}s")


# ─── I/O ──────────────────────────────────────────────────────────────────────

def ensure_dirs(*paths: Path) -> None:
    """Crée les répertoires manquants (équivalent mkdir -p)."""
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def save_csv(df: pd.DataFrame, path: Path, label: str = "") -> None:
    """Sauvegarde un DataFrame en CSV UTF-8 et journalise le résultat."""
    logger = get_logger("utils")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info(f"Saved {label or path.name}: {len(df):,} rows → {path}")


def load_csv(
    path: Path,
    parse_dates: Optional[list] = None,
) -> pd.DataFrame:
    """Charge un CSV avec message d'erreur explicite si le fichier est absent."""
    logger = get_logger("utils")
    if not Path(path).exists():
        raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_csv(path, parse_dates=parse_dates or [], low_memory=False)
    logger.info(
        f"Loaded {path.name}: {len(df):,} rows × {df.shape[1]} cols"
    )
    return df


# ─── Qualité des données ──────────────────────────────────────────────────────

def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne un DataFrame résumant les valeurs manquantes par colonne.

    Seules les colonnes avec au moins un null apparaissent dans le résultat.
    """
    miss = df.isnull().sum()
    pct = (miss / len(df) * 100).round(2)
    return (
        pd.DataFrame({"missing_count": miss, "missing_pct": pct})
        .query("missing_count > 0")
    )


def duplicate_summary(
    df: pd.DataFrame,
    subset: Optional[list] = None,
) -> dict:
    """Retourne le nombre et le pourcentage de lignes dupliquées."""
    n_dup = df.duplicated(subset=subset).sum()
    return {"duplicates": int(n_dup), "pct": round(n_dup / len(df) * 100, 3)}


def zscore_outliers(
    series: pd.Series,
    threshold: float = 3.5,
) -> pd.Series:
    """Masque booléen : True si la valeur dépasse le seuil z-score.

    Le seuil 3.5 (vs 3.0 classique) est utilisé pour réduire les
    faux positifs sur des distributions légèrement asymétriques.
    """
    z = np.abs((series - series.mean()) / series.std(ddof=0))
    return z > threshold


def safe_to_numeric(series: pd.Series, fill: float = 0.0) -> pd.Series:
    """Conversion robuste en numérique : les valeurs non convertibles → fill."""
    return pd.to_numeric(series, errors="coerce").fillna(fill)


def safe_parse_dates(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Parse plusieurs colonnes de dates en ignorant les erreurs de format."""
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=False)
    return df


# ─── Feature engineering ──────────────────────────────────────────────────────

def compute_delay_days(df: pd.DataFrame) -> pd.Series:
    """Calcule le retard en jours (positif = retard, négatif = avance).

    Formule : actual_delivery_date - expected_delivery_date
    """
    return (
        df["actual_delivery_date"] - df["expected_delivery_date"]
    ).dt.days


def is_late(delay_series: pd.Series) -> pd.Series:
    """Retourne True si la commande est livrée après la date promise."""
    return delay_series > 0


def delivery_lead_time(df: pd.DataFrame) -> pd.Series:
    """Délai total entre la date de commande et la livraison effective (jours)."""
    return (df["actual_delivery_date"] - df["order_date"]).dt.days


def shipping_cost_ratio(df: pd.DataFrame) -> pd.Series:
    """Ratio coût logistique / valeur commande, arrondi à 4 décimales.

    Les commandes à valeur nulle sont exclues (division par NaN)
    pour éviter des ratios infinis.
    """
    return (
        df["shipping_cost"] / df["order_value"].replace(0, np.nan)
    ).round(4)


# ─── Rapport qualité ──────────────────────────────────────────────────────────

def build_quality_report(
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    dataset_name: str,
) -> pd.DataFrame:
    """Construit un rapport qualité comparatif avant/après nettoyage.

    Pour chaque colonne du dataset brut, le rapport indique :
    - le nombre et pourcentage de valeurs manquantes avant nettoyage
    - le nombre de valeurs manquantes restantes après nettoyage
    - le nombre de valeurs uniques
    - le delta de lignes supprimées
    """
    records = []
    for col in df_before.columns:
        miss_before = df_before[col].isnull().sum()
        miss_after = (
            df_after[col].isnull().sum()
            if col in df_after.columns
            else None
        )
        records.append({
            "dataset": dataset_name,
            "column": col,
            "dtype": str(df_before[col].dtype),
            "missing_before": miss_before,
            "missing_pct_before": round(
                miss_before / len(df_before) * 100, 2
            ),
            "missing_after": miss_after,
            "n_unique": df_before[col].nunique(),
        })

    report = pd.DataFrame(records)
    report["rows_before"] = len(df_before)
    report["rows_after"] = len(df_after)
    report["rows_dropped"] = len(df_before) - len(df_after)
    return report
