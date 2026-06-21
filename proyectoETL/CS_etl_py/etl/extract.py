import pandas as pd
from sqlalchemy.engine import Engine


def extract(tables : list,conection: Engine)-> pd.DataFrame:
    """
    :param conection: the conectionnection to the database
    :param tables: the tables to extract
    :return: a list of tables in df format
    """
    a = []
    for i in tables:
        aux = pd.read_sql_table(i, conection)
        a.append(aux)
    return a



def extract_ips(conection: Engine):
    """
    Extract data from database where the conectionexion established
    :param conection:
    :return:
    """
    dim_ips = pd.read_sql_table('ips', conection)
    return dim_ips



def extract_medico(conection: Engine):
    dim_medico = pd.read_sql_table('medico', conection)
    return dim_medico




def extract_persona(conection: Engine):
    beneficiarios = pd.read_sql_table("beneficiario", conection)
    cotizantes = pd.read_sql_table("cotizante", conection)
    cotizante_beneficiario = pd.read_sql_table("cotizante_beneficiario", conection)
    return [beneficiarios, cotizantes, cotizante_beneficiario]




def extract_trans_servicio(conection: Engine):
    df_citas = pd.read_sql_table('citas_generales', conection)
    df_urgencias = pd.read_sql_table('urgencias', conection)
    df_hosp = pd.read_sql_table('hospitalizaciones', conection)
    remisiones = pd.read_sql_table('remisiones', conection)
    return [df_citas, df_urgencias, df_hosp,remisiones]




def extract_hecho_atencion(conection: Engine):
    df_diag = pd.read_sql_table('dim_diag', conection)
    df_demo = pd.read_sql_table('dim_demografia', conection)
    df_trans = pd.read_sql_table('trans_servicio', conection)
    dim_persona = pd.read_sql_table('dim_persona', conection)
    dim_medico = pd.read_sql_table('dim_medico', conection)
    dim_servicio = pd.read_sql_table('dim_servicio', conection)
    dim_ips = pd.read_sql_table('dim_ips', conection)
    dim_fecha = pd.read_sql_table('dim_fecha', conection)
    return [df_trans,dim_persona,dim_medico,dim_servicio,dim_ips,dim_fecha,df_diag,df_demo ]

def extract_medicamentos(path):
    df_medicamentos = pd.read_excel(path)
    df_medicamentos = df_medicamentos.rename(columns={'Código':'codigo', 'Nombre Genérico':'nombre','Forma Farmacéutica':'forma',
                                    'Laboratorio y Registro':'laboratorio', 'Tipo Medicamento':'tipo', 'Presentación':'presentacion','Precio':'precio'})
    return df_medicamentos




def extract_receta(conection:Engine):
    df_receta = pd.read_sql_query('''select codigo_formula , id_medico, id_usuario, fecha, 
    medicamentos_recetados as medicamentos from formulas_medicas''',conection)
    return df_receta

def extract_demografia(conection: Engine):
    df_benco= pd.read_sql_table('cotizante_beneficiario', conection)
    df_cotizantes = pd.read_sql_query(
        '''select cedula as numero_identificacion, tipo_cotizante, estado_civil, sexo, fecha_nacimiento,
            nivel_escolaridad, estracto, proviene_otra_eps,salario_base,tipo_discapacidad,id_ips from cotizante''', conection)
    df_beneficiarios = pd.read_sql_query(
        '''select id_beneficiario as numero_identificacion, fecha_nacimiento, sexo, estado_civil,
         tipo_discapacidad from beneficiario ''', conection)
    df_ips = pd.read_sql_query('select id_ips,municipio,departamento from ips', conection )
    empresa = pd.read_sql_query('select nit , nombre as empresa from empresa', conection)
    empcot = pd.read_sql_query('select empresa as nit, cotizante as numero_identificacion from empresa_cotizante', conection)
    return [df_benco,df_cotizantes,df_beneficiarios,df_ips, empresa, empcot]

def extract_enfermedades(conection : Engine):
    urgencias = pd.read_sql_query('select id_usuario, diagnostico,fecha_atencion from urgencias', conection)
    hospitalizaciones = pd.read_sql_query('select id_usuario, diagnostico, fecha_atencion  from hospitalizaciones', conection)
    citas_generales = pd.read_sql_query('select id_usuario, diagnostico,fecha_atencion  from citas_generales', conection)
    remisiones = pd.read_sql_query('select id_usuario, diagnostico, fecha_atencion  from remisiones', conection)

    return [urgencias, citas_generales, hospitalizaciones, remisiones]

def extract_paymetns(conection: Engine):
    df = pd.read_sql_query('select * from pagos', conection)
    return df

def extract_retiros(conection: Engine,conection_etl):
    df_retiros = pd.read_sql_query('select * from retiros', conection)
    df_pagos = pd.read_sql_query('select * from pagos', conection)
    df_per = pd.read_sql_table('dim_persona', conection_etl)
    df_dom = pd.read_sql_query('select * from dim_demografia', conection_etl)
    df_fecha = pd.read_sql_query('select * from dim_fecha', conection_etl)
    return [df_pagos, df_retiros,df_per, df_dom,df_fecha]

def extract_hecho_entrega(source, etl):
    df_med = pd.read_sql_table('dim_medicamentos',etl)
    df_form = extract_receta(source)
    df_demo = pd.read_sql_table('dim_demografia', etl)
    df_per = pd.read_sql_table('dim_persona', etl)
    df_doc = pd.read_sql_table('dim_medico', etl)
    df_fecha = pd.read_sql_table('dim_fecha',etl)
    return [df_med,df_form,df_per, df_doc,df_fecha,df_demo]

def extract_remisiones(conection : Engine,etl):
    df_demo = pd.read_sql_table('dim_demografia', etl)
    df_persona = pd.read_sql_query('select key_dim_persona, numero_identificacion from dim_persona', etl)
    df_medico = pd.read_sql_query('select key_dim_medico, cedula from  dim_medico',etl)
    df_fecha = pd.read_sql_query('select date, key_dim_fecha  from dim_fecha',etl)
    df_remisiones = pd.read_sql_query('select id_usuario, servicio_pos, id_medico, fecha_remision, codigo_remision from remisiones', conection)
    df_servicio_pos = pd.read_sql_query('select key_dim_servicio, id_servicio_pos servicio_pos,costo from dim_servicio', etl)
    return [df_remisiones, df_servicio_pos,df_persona,df_medico,df_fecha,df_demo]

def extract_servicios(conectionn):
    df_servicios = pd.read_sql_table('servicios_pos', conectionn)
    return df_servicios




#%%
