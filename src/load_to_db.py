"""
load_to_db.py
-------------
Charge le modèle dimensionnel dans une base SQLite locale.

Étapes :
  1. Suppression de la base existante (recréation propre à chaque run)
  2. Chargement des CSV du modèle en étoile (dimensions + faits)
  3. Création des index pour optimiser les requêtes Power BI
  4. Application des vues SQL analytiques (views.sql)
  5. Vérification du chargement avec comptage par table

Usage :
    python src/load_to_db.py
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DB_PATH, OUTPUT_FILES, SQL_DIR
from src.utils import ensure_dirs, get_logger, load_csv

logger = get_logger("load_to_db")

# Ordre de chargement respectant les contraintes de clés étrangères :
# les dimensions doivent être chargées avant la table de faits.
TABLE_FILES = {
    "dim_date": OUTPUT_FILES["dim_date"],
    "dim_customer": OUTPUT_FILES["dim_customer"],
    "dim_product": OUTPUT_FILES["dim_product"],
    "dim_carrier": OUTPUT_FILES["dim_carrier"],
    "dim_warehouse": OUTPUT_FILES["dim_warehouse"],
    "fact_orders": OUTPUT_FILES["fact_orders"],
}


# ─── Connexion ────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Ouvre la connexion SQLite avec WAL et foreign keys activés.

    WAL (Write-Ahead Logging) améliore les performances en lecture/écriture
    simultanées et évite les corruptions sur interruption.
    """
    ensure_dirs(DB_PATH.parent)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─── Schéma et vues ───────────────────────────────────────────────────────────

def apply_schema(conn: sqlite3.Connection) -> None:
    """Applique le DDL depuis schema.sql (CREATE TABLE IF NOT EXISTS).

    Non appelé par défaut dans main() car to_sql() crée les tables
    automatiquement. Disponible pour forcer le schéma strict.
    """
    schema_path = SQL_DIR / "schema.sql"
    if not schema_path.exists():
        logger.warning(f"schema.sql not found at {schema_path}, skipping DDL.")
        return
    with open(schema_path, "r", encoding="utf-8") as f:
        ddl = f.read()
    conn.executescript(ddl)
    conn.commit()
    logger.info("Schema applied from schema.sql")


def apply_views(conn: sqlite3.Connection) -> None:
    """Applique les vues analytiques depuis views.sql.

    Exécute les instructions une par une car SQLite ne supporte pas
    executescript() avec des SELECT dans certaines versions.
    Les erreurs de vue sont loggées mais n'interrompent pas le pipeline.
    """
    views_path = SQL_DIR / "views.sql"
    if not views_path.exists():
        logger.warning("views.sql not found, skipping.")
        return
    with open(views_path, "r", encoding="utf-8") as f:
        sql = f.read()
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        try:
            conn.execute(stmt)
        except sqlite3.Error as e:
            logger.warning(f"View error: {e} — {stmt[:60]}...")
    conn.commit()
    logger.info("Views applied from views.sql")


# ─── Chargement des tables ────────────────────────────────────────────────────

def load_table(
    conn: sqlite3.Connection,
    table_name: str,
    csv_path: Path,
    if_exists: str = "replace",
) -> int:
    """Charge un CSV dans une table SQLite via pandas to_sql.

    Les colonnes de type category et datetimetz sont converties
    car SQLite ne les supporte pas nativement.

    Args:
        conn: Connexion SQLite active.
        table_name: Nom de la table cible.
        csv_path: Chemin du fichier CSV source.
        if_exists: Comportement si la table existe déjà ("replace" par défaut).

    Returns:
        Nombre de lignes insérées (0 si le fichier est absent).
    """
    if not Path(csv_path).exists():
        logger.warning(f"File not found, skipping: {csv_path}")
        return 0

    df = pd.read_csv(csv_path, low_memory=False)

    # Conversion des types non supportés par SQLite
    for col in df.select_dtypes(include=["category"]).columns:
        df[col] = df[col].astype(str)
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    df.to_sql(table_name, conn, if_exists=if_exists, index=False, chunksize=5_000)
    logger.info(f"  Loaded table [{table_name}]: {len(df):,} rows")
    return len(df)


# ─── Indexation ───────────────────────────────────────────────────────────────

def create_indexes(conn: sqlite3.Connection) -> None:
    """Crée les index sur fact_orders pour accélérer les requêtes analytiques.

    Les colonnes indexées correspondent aux axes de filtrage les plus fréquents
    dans les dashboards Power BI (date, carrier, warehouse, région, statut).
    """
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_fact_order_date "
        "ON fact_orders(order_date)",
        "CREATE INDEX IF NOT EXISTS idx_fact_carrier "
        "ON fact_orders(carrier_id)",
        "CREATE INDEX IF NOT EXISTS idx_fact_warehouse "
        "ON fact_orders(warehouse_id)",
        "CREATE INDEX IF NOT EXISTS idx_fact_customer "
        "ON fact_orders(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_fact_status "
        "ON fact_orders(order_status)",
        "CREATE INDEX IF NOT EXISTS idx_fact_is_late "
        "ON fact_orders(is_late)",
        "CREATE INDEX IF NOT EXISTS idx_fact_year_month "
        "ON fact_orders(order_year_month)",
        "CREATE INDEX IF NOT EXISTS idx_fact_region "
        "ON fact_orders(region)",
        "CREATE INDEX IF NOT EXISTS idx_dim_date_key "
        "ON dim_date(date_key)",
        "CREATE INDEX IF NOT EXISTS idx_dim_carrier_name "
        "ON dim_carrier(carrier_name)",
    ]
    for idx_sql in indexes:
        conn.execute(idx_sql)
    conn.commit()
    logger.info(f"  {len(indexes)} indexes created")


# ─── Vérification ─────────────────────────────────────────────────────────────

def verify_load(conn: sqlite3.Connection) -> None:
    """Affiche le nombre de lignes par table pour valider le chargement."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    print("\nDatabase verification:")
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t:<25} {count:>10,} rows")


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def main():
    """Point d'entrée du pipeline de chargement SQLite.

    Recrée la base de zéro à chaque exécution pour garantir la cohérence
    avec les dernières données transformées.
    """
    logger.info("=== Load to SQLite Pipeline ===")

    # Suppression de la base existante pour éviter des données obsolètes.
    # L'exception OSError couvre les cas de fichier verrouillé ou protégé.
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
            logger.info(f"Removed existing database: {DB_PATH}")
        except OSError as e:
            logger.error(f"Cannot remove existing database: {e}")
            raise

    conn = get_connection()

    try:
        total_rows = 0
        for table_name, csv_path in TABLE_FILES.items():
            n = load_table(conn, table_name, csv_path)
            total_rows += n

        create_indexes(conn)
        apply_views(conn)
        verify_load(conn)

        logger.info(
            f"=== Load complete — {total_rows:,} total rows inserted ==="
        )
        print(f"\nDatabase: {DB_PATH}")

    finally:
        # La connexion est toujours fermée, même en cas d'erreur
        conn.close()


if __name__ == "__main__":
    main()
