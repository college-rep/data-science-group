import sys
import time
from pathlib import Path

import yaml
import psycopg2
from sqlalchemy import create_engine, inspect, text

import nbformat
from nbclient import NotebookClient

BASE_DIR = Path(__file__).resolve().parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
CONFIG_PATH = BASE_DIR / "config.yml"
SQLSCRIPTS_PATH = BASE_DIR / "sqlscripts.yml"

DIMENSIONES = [
    "dim_fecha.ipynb",
    "dim_hora.ipynb",
    "dim_cliente.ipynb",
    "dim_sede.ipynb",
    "dim_mensajero.ipynb",
    "dim_estado.ipynb",
    "dim_novedad.ipynb",
    "dim_tipo_servicio.ipynb",
]

HECHOS = [
    "hecho_servicio.ipynb",
    "hecho_seguimiento_fases.ipynb",
    "hecho_novedad.ipynb",
]


TABLAS_A_LIMPIAR = [
    "dim_fecha",
    "dim_hora",
    "dim_estado",
    "dim_sede",
    "dim_tipo_servicio",
]


def cargar_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def crear_engines(config):
    co = config["CO_SA"]
    etl = config["ETL_PRO"]
    url_co = (f"{co['drivername']}://{co['user']}:{co['password']}@{co['host']}:"
              f"{co['port']}/{co['dbname']}")
    url_etl = (f"{etl['drivername']}://{etl['user']}:{etl['password']}@{etl['host']}:"
               f"{etl['port']}/{etl['dbname']}")
    return create_engine(url_co), create_engine(url_etl)


def crear_tablas(config, etl_conn):

    existentes = set(inspect(etl_conn).get_table_names())

    with open(SQLSCRIPTS_PATH, "r") as f:
        scripts = yaml.safe_load(f)

    faltantes = {k.strip(): v for k, v in scripts.items() if k.strip() not in existentes}

    if not faltantes:
        print("[DDL] Todas las tablas de sqlscripts.yml ya existen.")
        return

    etl = config["ETL_PRO"]
    conn = psycopg2.connect(dbname=etl["dbname"], user=etl["user"],
                            password=etl["password"], host=etl["host"], port=etl["port"])
    cur = conn.cursor()
    for tabla, ddl in faltantes.items():
        cur.execute(ddl)
        conn.commit()
        print(f"[DDL] Tabla creada: {tabla}")
    cur.close()
    conn.close()


def limpiar_tablas(etl_conn):
    """Vacia las tablas que se cargan con append, para permitir recargas."""
    existentes = set(inspect(etl_conn).get_table_names())
    with etl_conn.begin() as conn:
        for tabla in TABLAS_A_LIMPIAR:
            if tabla in existentes:
                conn.execute(text(f"TRUNCATE TABLE {tabla} RESTART IDENTITY CASCADE"))
                print(f"[CLEAN] {tabla} vaciada")


def ejecutar_notebook(nombre):
    """Ejecuta un notebook con notebooks/ como directorio de trabajo."""
    ruta = NOTEBOOKS_DIR / nombre
    if not ruta.exists():
        print(f"[SKIP]  {nombre} (no existe)")
        return False

    inicio = time.time()
    try:
        nb = nbformat.read(ruta, as_version=4)
        cliente = NotebookClient(
            nb,
            timeout=1800,
            kernel_name="python3",
            resources={"metadata": {"path": str(NOTEBOOKS_DIR)}},
        )
        cliente.execute()
        print(f"[OK]    {nombre}  ({time.time() - inicio:.1f}s)")
        return True
    except Exception as e:
        mensaje = str(e).strip().split("\n")[-1][:120]
        print(f"[ERROR] {nombre}: {mensaje}")
        return False


def main():
    solo_ddl = "--solo-ddl" in sys.argv
    limpiar = "--no-limpiar" not in sys.argv

    config = cargar_config()
    co_sa, etl_conn = crear_engines(config)

    with co_sa.connect():
        print(f"[CONN] Origen OK: {config['CO_SA']['dbname']}")
    with etl_conn.connect():
        print(f"[CONN] Bodega OK: {config['ETL_PRO']['dbname']}")

    crear_tablas(config, etl_conn)
    if solo_ddl:
        return

    if limpiar:
        limpiar_tablas(etl_conn)

    fallidos = []

    print("\n=== Dimensiones ===")
    for nb in DIMENSIONES:
        if not ejecutar_notebook(nb):
            fallidos.append(nb)

    print("\n=== Hechos ===")
    for nb in HECHOS:
        if not ejecutar_notebook(nb):
            fallidos.append(nb)

    print("\n" + "=" * 50)
    total = len(DIMENSIONES) + len(HECHOS)
    print(f"Completados: {total - len(fallidos)}/{total}")
    if fallidos:
        print("Fallidos:")
        for nb in fallidos:
            print(f"  - {nb}")
        sys.exit(1)
    print("ETL finalizado sin errores.")


if __name__ == "__main__":
    main()