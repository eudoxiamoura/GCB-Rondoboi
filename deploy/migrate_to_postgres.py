"""Migra os dados do SQLite atual (instance/bovinos.db) para um Postgres.
Preserva os IDs originais (importante pras foreign keys) e ajusta as
sequences do Postgres no final pra não colidir com inserts futuros.

Rode da raiz do projeto, com o venv ativado:

    DATABASE_URL_DESTINO=postgresql+psycopg://usuario:senha@localhost/rondoboi \
    python deploy/migrate_to_postgres.py
"""
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine, select, text  # noqa: E402

from config import Config  # noqa: E402
from app import create_app, db  # noqa: E402

SQLITE_PATH = os.environ.get(
    "SQLITE_ORIGEM", os.path.join(BASE_DIR, "instance", "bovinos.db")
)
SQLITE_URL = f"sqlite:///{SQLITE_PATH}"


def main():
    pg_url = os.environ.get("DATABASE_URL_DESTINO")
    if not pg_url:
        print("Defina DATABASE_URL_DESTINO com a URL do Postgres de destino.")
        sys.exit(1)

    if not os.path.exists(SQLITE_PATH):
        print(f"Banco SQLite de origem não encontrado em: {SQLITE_PATH}")
        sys.exit(1)

    class PgConfig(Config):
        SQLALCHEMY_DATABASE_URI = pg_url

    app = create_app(PgConfig)
    with app.app_context():
        db.create_all()
        meta = db.metadata

        src_engine = create_engine(SQLITE_URL)
        dst_engine = create_engine(pg_url)

        with src_engine.connect() as src_conn, dst_engine.connect() as dst_conn:
            for table in meta.sorted_tables:
                rows = [dict(row._mapping) for row in src_conn.execute(select(table))]
                if not rows:
                    print(f"{table.name}: 0 linhas (pulando)")
                    continue

                dst_conn.execute(table.insert(), rows)

                if "id" in table.c:
                    dst_conn.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                        f"(SELECT MAX(id) FROM {table.name}))"
                    ))

                dst_conn.commit()
                print(f"{table.name}: {len(rows)} linha(s) migrada(s)")

    print("\nMigração concluída.")


if __name__ == "__main__":
    main()
