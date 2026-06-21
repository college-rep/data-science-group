from sqlalchemy import Engine, text

def new_data(conne: Engine) -> bool:
    queryo = text('select saved from hecho_atencion order by saved desc limit 1;')
    queryt = text(''' select date from dim_fecha where key_dim_fecha =
    (select key_fecha_atencion from hecho_atencion order by key_fecha_atencion desc limit 1) ;''')
    with conne.connect() as con:
        try:
            rs1 = con.execute(queryo)
            rs2 = con.execute(queryt)
            lastupdate = rs1.fetchone()
            lastdate = rs2.fetchone()
            if lastupdate is None or lastdate is None:
                return True
            if lastdate.date() > lastupdate:
                return True
            print(f'''No hay datos nuevos desde la ultima fecha de carga {lastupdate}''')
            return False
        except Exception as e:
            print('[*]', e)
            return False


def push_dimensions(co_sa, etl_conn):
    dim_ips = extract.extract_ips(co_sa)
    dim_persona = extract.extract_persona(co_sa)
    dim_medico = extract.extract_medico(co_sa)
    trans_servicio = extract.extract_trans_servicio(co_sa)
    dim_demo = extract.extract_demografia(co_sa)
    dim_diag = extract.extract_enfermedades(co_sa)
    dim_servicio = extract.extract_servicios(co_sa)

    # transform
    dim_ips = transform.transform_ips(dim_ips)
    dim_persona = transform.transform_persona(dim_persona)
    dim_medico = transform.transform_medico(dim_medico)
    trans_servicio = transform.transform_trans_servicio(trans_servicio)
    dim_fecha = transform.transform_fecha()

    dim_demo = transform.transform_demografia(dim_demo)
    dim_diag = transform.transform_enfermedades(dim_diag)

    load.load(dim_ips, etl_conn, 'dim_ips')
    load.load(dim_fecha, etl_conn, 'dim_fecha')
    load.load(dim_servicio, etl_conn, 'dim_servicio')
    load.load(dim_persona, etl_conn, 'dim_persona')
    load.load(dim_medico, etl_conn, 'dim_medico')
    load.load(trans_servicio, etl_conn, 'trans_servicio')
    load.load(dim_diag, etl_conn, 'dim_diag')
    load.load(dim_demo, etl_conn, 'dim_demografia')