import pandas as pd
import datetime
from datetime import date
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
import yaml
from etl import extract, transform, load, utils_etl
import psycopg2

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)


with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)
    config_co = config['CO_SA']
    config_etl = config['ETL_PRO']

# Construct the database URL
url_co = (f"{config_co['drivername']}://{config_co['user']}:{config_co['password']}@{config_co['host']}:"
          f"{config_co['port']}/{config_co['dbname']}")
url_etl = (f"{config_etl['drivername']}://{config_etl['user']}:{config_etl['password']}@{config_etl['host']}:"
           f"{config_etl['port']}/{config_etl['dbname']}")
# Create the SQLAlchemy Engine
co_sa = create_engine(url_co)
etl_conn = create_engine(url_etl)

inspector = inspect(etl_conn)
tnames = inspector.get_table_names()

if not tnames:
    conn = psycopg2.connect(dbname=config_etl['dbname'], user=config_etl['user'], password=config_etl['password'],
                            host=config_etl['host'], port=config_etl['port'])
    cur = conn.cursor()
    with open('sqlscripts.yml', 'r') as f:
        sql = yaml.safe_load(f)
        for key, val in sql.items():
            cur.execute(val)
            conn.commit()

if utils_etl.new_data(etl_conn):

    if config['LOAD_DIMENSIONS']:
        dim_ips = extract.extract_ips(co_sa)
        dim_persona = extract.extract_persona(co_sa)
        dim_medico = extract.extract_medico(co_sa)
        trans_servicio = extract.extract_trans_servicio(co_sa)
        dim_demo = extract.extract_demografia(co_sa)
        dim_diag = extract.extract_enfermedades(co_sa)
        dim_drug = extract.extract_medicamentos(config['medicamentos'])
        dim_servicio = extract.extract_servicios(co_sa)


        # transform
        dim_ips = transform.transform_ips(dim_ips)
        dim_persona = transform.transform_persona(dim_persona)
        dim_medico = transform.transform_medico(dim_medico)
        trans_servicio = transform.transform_trans_servicio(trans_servicio)
        dim_fecha = transform.transform_fecha()
        dim_demo = transform.transform_demografia(dim_demo)
        dim_diag = transform.transform_enfermedades(dim_diag)



        load.load(dim_ips, etl_conn, 'dim_ips', True)
        load.load(dim_fecha, etl_conn, 'dim_fecha', True)
        load.load(dim_servicio, etl_conn, 'dim_servicio', True)
        load.load(dim_persona, etl_conn, 'dim_persona', True)
        load.load(dim_medico, etl_conn, 'dim_medico', True)
        load.load(trans_servicio, etl_conn, 'trans_servicio', True)
        load.load(dim_diag, etl_conn, 'dim_diag', True)
        load.load(dim_demo, etl_conn, 'dim_demografia', True)
        load.load(dim_drug,etl_conn,'dim_medicamentos',True)


    #hecho Atencion
    hecho_atencion = extract.extract_hecho_atencion(etl_conn)
    hecho_atencion = transform.transform_hecho_atencion(hecho_atencion)
    load.load_hecho_atencion(hecho_atencion, etl_conn)
    print('Done atencion fact')
    # Hecho Entrega medicamentos
    hecho_entrega = extract.extract_hecho_entrega(co_sa,etl_conn)
    hecho_entrega, masrecetados = transform.transform_hecho_entrega(hecho_entrega)
    load.load_hecho_entrega(hecho_entrega, etl_conn)
    print('Done entrega fact')
    # medicamentos que mas se recetan juntos
    masrecetados = masrecetados.astype('string')
    load.load(masrecetados,etl_conn, 'mas_recetados', False)
    # Hecho retrios
    hecho_retiros = extract.extract_retiros(co_sa,etl_conn)
    hecho_retiros = transform.transform_hecho_retiros(hecho_retiros,1)
    load.load(hecho_retiros, etl_conn, 'hecho_retiros', False)
    print('Done retiros fact')

    print('success all facts loaded')
else:
    print('done not new data')

#%%
