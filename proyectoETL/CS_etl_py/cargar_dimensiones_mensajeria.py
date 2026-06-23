"""
Carga las dimensiones de mensajeria que ya estan terminadas:
dim_fecha, dim_hora, dim_estado, dim_sede, dim_tipo_servicio.

NO toca: Cliente, Geografia, Novedad, dim_servicio (de companeros)
ni los hechos (Servicio, Seguimiento_Fases, Registro_Novedades),
que se reparten en una reunion futura.

Requisito: las 5 tablas deben existir en la base ETL_PRO con su DDL
(ver sqlscripts.yml). main.py ya las crea automaticamente si la base
esta vacia; si prefieres crearlas a mano, corre el DDL en pgAdmin/psql.
"""
import sys
import yaml
from sqlalchemy import create_engine, inspect
from etl import extract, transform, load

with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)
    config_co = config['CO_SA']
    config_etl = config['ETL_PRO']

url_co = (f"{config_co['drivername']}://{config_co['user']}:{config_co['password']}@{config_co['host']}:"
          f"{config_co['port']}/{config_co['dbname']}")
url_etl = (f"{config_etl['drivername']}://{config_etl['user']}:{config_etl['password']}@{config_etl['host']}:"
           f"{config_etl['port']}/{config_etl['dbname']}")

co_sa = create_engine(url_co)
etl_conn = create_engine(url_etl)

inspector = inspect(etl_conn)
tablas_necesarias = {'dim_fecha', 'dim_hora', 'dim_estado', 'dim_sede', 'dim_tipo_servicio'}
tablas_existentes = set(inspector.get_table_names())
faltantes = tablas_necesarias - tablas_existentes
if faltantes:
    print(f"ATENCION: faltan estas tablas en la base ETL: {faltantes}")
    print("Corre el DDL de sqlscripts.yml antes de continuar.")
    sys.exit(1)

print("Cargando dim_fecha...")
dim_fecha = transform.transform_fecha_mensajeria()
load.load(dim_fecha, etl_conn, 'dim_fecha', replace=True)
print(f"  -> {len(dim_fecha)} filas")

print("Cargando dim_hora...")
dim_hora = transform.transform_hora()
load.load(dim_hora, etl_conn, 'dim_hora', replace=True)
print(f"  -> {len(dim_hora)} filas")

print("Cargando dim_estado...")
dim_estado_raw = extract.extract_estado(co_sa)
dim_estado = transform.transform_estado(dim_estado_raw)
load.load(dim_estado, etl_conn, 'dim_estado', replace=True)
print(f"  -> {len(dim_estado)} filas")

print("Cargando dim_sede...")
dim_sede_raw = extract.extract_sede(co_sa)
dim_sede = transform.transform_sede(dim_sede_raw)
load.load(dim_sede, etl_conn, 'dim_sede', replace=True)
print(f"  -> {len(dim_sede)} filas")

print("Cargando dim_tipo_servicio...")
prioridades_raw = extract.extract_tipo_servicio(co_sa)
dim_tipo_servicio = transform.transform_tipo_servicio(prioridades_raw)
load.load(dim_tipo_servicio, etl_conn, 'dim_tipo_servicio', replace=True)
print(f"  -> {len(dim_tipo_servicio)} filas")

print("\nListo: 5 dimensiones de mensajeria cargadas.")