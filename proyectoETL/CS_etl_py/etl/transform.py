#%%
import datetime
from datetime import timedelta, date, datetime
from typing import Tuple, Any

import holidays
import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori
from mlxtend.preprocessing import TransactionEncoder
from pandas import DataFrame


def transform_ips(dim_ips: DataFrame) -> DataFrame:
    dim_ips.replace({'': '0'}, inplace=True)
    dim_ips["saved"] = date.today()
    return dim_ips


def transform_medico(dim_medico: DataFrame) -> DataFrame:
    dim_medico.replace({np.nan: 'no aplica', ' ': 'no aplica','':'no_aplica'}, inplace=True)
    dim_medico["saved"] = date.today()
    return dim_medico


def transform_persona(args) -> DataFrame:
    beneficiarios, cotizantes, cot_ben = args
    cotizantes.rename(columns={'cedula': 'numero_identificacion'}, inplace=True)
    cotizantes.drop(
        columns=['direccion', 'tipo_cotizante', 'nivel_escolaridad', 'estracto', 'proviene_otra_eps', 'salario_base',
                 'fecha_afiliacion', 'id_ips'], inplace=True)
    cotizantes['tipo_documento'] = "cedula"
    cotizantes['tipo_usuario'] = "cotizante"
    cotizantes['grupo_familiar'] = cotizantes['numero_identificacion']
    beneficiarios.drop(columns=['parentesco'], inplace=True)
    beneficiarios.rename(columns={'tipo_identificacion': 'tipo_documento', 'id_beneficiario': 'numero_identificacion'},
                         inplace=True)
    beneficiarios['tipo_usuario'] = "beneficiario"
    beneficiario = beneficiarios.merge(cot_ben, left_on='numero_identificacion', right_on='beneficiario', how='left')
    beneficiario.rename(columns={'cotizante': 'grupo_familiar'}, inplace=True)
    beneficiario.drop(columns=['beneficiario'], inplace=True)
    dim_persona = pd.concat([beneficiario, cotizantes])
    dim_persona["saved"] = date.today()
    dim_persona.reset_index(drop=True, inplace=True)

    return dim_persona




def transform_fecha() -> DataFrame:
    dim_fecha = pd.DataFrame({"date": pd.date_range(start='1/1/2005', end='1/1/2009', freq='D')})
    dim_fecha["year"] = dim_fecha["date"].dt.year
    dim_fecha["month"] = dim_fecha["date"].dt.month
    dim_fecha["day"] = dim_fecha["date"].dt.day
    dim_fecha["weekday"] = dim_fecha["date"].dt.weekday
    dim_fecha["quarter"] = dim_fecha["date"].dt.quarter
    dim_fecha["day_of_year"] = dim_fecha["date"].dt.day_of_year
    dim_fecha["day_of_month"] = dim_fecha["date"].dt.days_in_month
    dim_fecha["month_str"] = dim_fecha["date"].dt.month_name()  # run locale -a en unix
    dim_fecha["day_str"] = dim_fecha["date"].dt.day_name()  # locale = 'es_CO.UTF8'
    dim_fecha["date_str"] = dim_fecha["date"].dt.strftime("%d/%m/%Y")
    co_holidays = holidays.CO(language="es")
    dim_fecha["is_Holiday"] = dim_fecha["date"].apply(lambda x: x in co_holidays)
    dim_fecha["holiday"] = dim_fecha["date"].apply(lambda x: co_holidays.get(x))
    dim_fecha["weekend"] = dim_fecha["weekday"].apply(lambda x: x > 4)
    dim_fecha["saved"] = date.today()
    return dim_fecha


def transform_trans_servicio(args) -> DataFrame:
    df_citas, df_urgencias, df_hosp,rem = args
    df_hosp.rename(columns={'codigo_hospitalizacion': 'codigo_servicio'}, inplace=True)
    df_urgencias.rename(columns={'codigo_urgencia': 'codigo_servicio'}, inplace=True)
    df_citas.rename(columns={'codigo_cita': 'codigo_servicio'}, inplace=True)
    rem.rename(columns={'codigo_rem': 'codigo_servicio',
                        'fecha_remision':'fecha_solicitud',
                        'hora_remision':'hora_solicitud'}, inplace=True)
    #rem.drop('id_medico_rem', axis=1, inplace=True)
    df_citas['servicio_pos'] = '1234'
    df_urgencias['servicio_pos'] = '1367'
    df_hosp['servicio_pos'] ='1346'

    columns = ['codigo_servicio', 'id_usuario', 'id_medico',
               'fecha_solicitud', 'fecha_atencion', 'hora_atencion',
               'hora_solicitud', 'servicio_pos']
    trans_servicio = pd.concat([df_hosp, df_urgencias, df_citas,rem], axis=0)
    trans_servicio.head()
    del_columns = set(trans_servicio.columns) - set(columns)
    trans_servicio.drop(columns=del_columns, inplace=True)
    trans_servicio['fecha_atencion'] = pd.to_datetime(trans_servicio['fecha_atencion'])
    trans_servicio['fecha_solicitud'] = pd.to_datetime(trans_servicio['fecha_solicitud'])
    trans_servicio['hora_atencion'] = trans_servicio['hora_atencion'].apply(
        lambda x: timedelta(hours=x.hour, minutes=x.minute, seconds=x.second))
    trans_servicio['hora_solicitud'] = trans_servicio['hora_solicitud'].apply(
        lambda x: timedelta(hours=x.hour, minutes=x.minute, seconds=x.second))
    trans_servicio['fecha_hora_atencion'] = trans_servicio['fecha_atencion'] + trans_servicio['hora_atencion']
    trans_servicio['fecha_hora_solicitud'] = trans_servicio['fecha_solicitud'] + trans_servicio['hora_solicitud']
    trans_servicio["saved"] = date.today()
    trans_servicio.reset_index(drop=True, inplace=True)
    return trans_servicio

def transform_hecho_entrega(args:list[DataFrame]) -> tuple[Any, Any]:
    df_med, df_form, df_per, df_doc, df_fecha, df_demo = args
    df_form['medicamentos'] = df_form['medicamentos'].apply(lambda x: x.split(';'))


    df_form_expl = df_form.explode('medicamentos')
    df_med = df_med.astype('string')
    df_mer = df_form_expl.merge(df_med[['key_dim_medicamentos','codigo','nombre','precio']], left_on='medicamentos',right_on= 'codigo')
    df_mer = df_mer.merge(df_per[['numero_identificacion','key_dim_persona']]
                          ,right_on='numero_identificacion',left_on='id_usuario')
    df_mer.drop(columns=['numero_identificacion'], inplace=True)
    df_mer = df_mer.merge(df_demo[['numero_identificacion','key_dim_demo']],
                          left_on='id_usuario',
                          right_on='numero_identificacion')
    df_mer = df_mer.merge(df_doc[['cedula','key_dim_medico']],
                          left_on='id_medico',right_on='cedula')
    df_fecha['date'] = df_fecha['date'].dt.date

    df_mer = df_mer.merge(df_fecha[['key_dim_fecha','date']],left_on='fecha',right_on='date')
    df_mer.drop(columns = ['cedula','medicamentos','id_usuario','numero_identificacion'
        ,'id_medico','codigo','fecha','date'],inplace=True)

    df_fix = df_mer[['codigo_formula','nombre']].groupby(['codigo_formula']).agg({ 'nombre' : list    }).reset_index()

    masrecetados = df_fix['nombre'].to_list()

    te = TransactionEncoder()
    te_ary = te.fit(masrecetados).transform(masrecetados)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    frequent_itemsets = apriori(df, min_support=0.02, use_colnames=True)
    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))

    frequent_itemsets = frequent_itemsets[ (frequent_itemsets['length'] >= 2) &
                       (frequent_itemsets['support'] >= 0.05) ]

    return df_mer.drop('nombre',axis=1), frequent_itemsets

# modificar para anadir demografia y enfermedades(diagnostico)
def transform_hecho_atencion(args) -> DataFrame:
    df_trans, dim_persona, dim_medico, dim_servicio, dim_ips, dim_fecha,dim_diag,dim_demo= args
    hecho_atencion = pd.merge(df_trans, dim_fecha[['date', 'key_dim_fecha']], left_on='fecha_atencion', right_on='date')
    hecho_atencion.drop(columns=['date'], inplace=True)
    hecho_atencion.rename(
        columns={'key_dim_fecha': 'key_fecha_atencion', 'id_medico': 'cedula', 'id_usuario': 'numero_identificacion'},
        inplace=True)
    hecho_atencion = pd.merge(hecho_atencion, dim_fecha[['date', 'key_dim_fecha']], left_on='fecha_solicitud',
                              right_on='date')
    hecho_atencion.drop(columns=['date'], inplace=True)

    hecho_atencion.rename(columns={'key_dim_fecha': 'key_fecha_solicitud'}, inplace=True)
    hecho_atencion = hecho_atencion.merge(dim_persona[['key_dim_persona', 'numero_identificacion']])
    hecho_atencion = hecho_atencion.merge(dim_demo[['key_dim_demo', 'numero_identificacion']])
    hecho_atencion = hecho_atencion.merge(dim_diag[['key_dim_diag', 'numero_identificacion','fecha_diagnostico']],left_on=['numero_identificacion', 'fecha_atencion'],
                                          right_on=['numero_identificacion', 'fecha_diagnostico'],)
    hecho_atencion.drop(columns=['numero_identificacion','fecha_diagnostico'], inplace=True)
    hecho_atencion = hecho_atencion.merge(dim_medico[['key_dim_medico', 'cedula', 'id_ips']])
    hecho_atencion.drop(columns=['cedula'], inplace=True)
    hecho_atencion = hecho_atencion.merge(dim_ips[['key_dim_ips', 'id_ips']])
    hecho_atencion.drop(columns=['id_ips'], inplace=True)
    hecho_atencion = hecho_atencion.merge(dim_servicio[['id_servicio_pos', 'key_dim_servicio', 'costo']], left_on='servicio_pos',
                                          right_on='id_servicio_pos')
    hecho_atencion.drop(columns=['id_servicio_pos'], inplace=True)
    hecho_atencion['tiempo_espera'] = hecho_atencion['fecha_hora_atencion'] - hecho_atencion['fecha_hora_solicitud']
    hecho_atencion['tiempo_espera_dias'] = hecho_atencion['tiempo_espera'].dt.days
    hecho_atencion['tiempo_espera_minutos'] = hecho_atencion['tiempo_espera'].dt.seconds // 60
    hecho_atencion['tiempo_espera_horas'] = hecho_atencion['tiempo_espera'].dt.seconds // (60 * 60)
    hecho_atencion['tiempo_espera_segundos'] = hecho_atencion['tiempo_espera'].dt.seconds
    hecho_atencion["saved"] = date.today()
    hecho_atencion.drop(
        columns=['servicio_pos','tiempo_espera', 'fecha_atencion', 'fecha_solicitud', 'hora_solicitud', 'hora_atencion',
                 'fecha_hora_solicitud', 'fecha_hora_atencion', 'codigo_servicio'], inplace=True)
    return hecho_atencion

def transform_pay_retiros(args) -> DataFrame:
    return args

def transform_demografia(args) -> DataFrame:
    df_benco, df_cot, df_ben, df_ips, empresa,empcot = args
    df_ben['tipo_usuario'] = 'beneficiario'
    df_ben = df_ben.merge(df_benco, left_on='numero_identificacion',right_on='beneficiario')
    df_ben = df_ben.merge(df_cot[['numero_identificacion','estracto','id_ips']],
                          left_on= 'cotizante',right_on='numero_identificacion', suffixes=('', '_cot'))
    df_cot.rename(columns={'tipo_cotizante': 'tipo_usuario'}, inplace=True)

    df_cot = df_cot.merge(empcot)
    df_cot = df_cot.merge(empresa)
    df_demo = pd.concat([df_ben, df_cot])
    df_demo['edad'] = df_demo['fecha_nacimiento'].apply(lambda x: (date.today() - x).days // 365)
    df_demo.replace(np.nan, 'NO APLICA', inplace=True)
    df_demo.drop(columns=['nit','numero_identificacion_cot','beneficiario','cotizante'], inplace=True)
    return df_demo

def transform_enfermedades(args) -> DataFrame:
    urg, citas, hosp , remi = args
    df_enfermedades = pd.concat([urg, citas, hosp, remi])
    df_enfermedades.drop_duplicates(inplace=True)
    df_enfermedades.rename(columns={'id_usuario': 'numero_identificacion','fecha_atencion':'fecha_diagnostico'}, inplace=True)
    return df_enfermedades
#%%
def lattestpayment(data:DataFrame,fecha,months=1):
    months = timedelta(days=30*months)
    data['retirado'] = data['fecha_pago'].apply(lambda x:  datetime.strptime(fecha,'%Y-%m-%d').date() - x[-1] > months )
    data['fecha_retiro']= data['fecha_pago'].apply(lambda x: x[-1])
    return data[['retirado','fecha_retiro','id_usuario']]

def transform_hecho_retiros(args,months,lastdate='2008-11-15',) -> DataFrame:
    pagos, retiros,dim_per,dim_demo,dim_fecha = args
    mask = pagos['id_usuario'].isin(retiros['id_usuario'])
    pagos =  pagos[~mask]
    testretiros = pagos.groupby('id_usuario').agg({'fecha_pago':list}).reset_index()
    pagos = lattestpayment(testretiros,lastdate,months)
    pagos['cambio_a_eps'] = 'NO'
    retiros.replace({'':'NO'},inplace=True)
    retiros['retirado'] = True
    hecho_retiros = pd.concat([pagos[pagos['retirado']==True],
                               retiros[['fecha_retiro','id_usuario','cambio_a_eps','retirado']]],ignore_index=True)
    hecho_retiros = hecho_retiros.merge(dim_per[['key_dim_persona','numero_identificacion']],left_on='id_usuario',right_on='numero_identificacion')
    hecho_retiros = hecho_retiros.merge(dim_demo[['key_dim_demo','numero_identificacion']],left_on='id_usuario',right_on='numero_identificacion')

    dim_fecha['date'] = dim_fecha['date'].dt.date

    hecho_retiros = hecho_retiros.merge(dim_fecha[['key_dim_fecha','date']],left_on='fecha_retiro',right_on='date')
    hecho_retiros.drop(columns=['numero_identificacion_y','numero_identificacion_x','date','fecha_retiro','id_usuario'],inplace=True)

    return hecho_retiros

def transform_remisiones(args) -> DataFrame:
    df_remisiones, df_servicios, persona, medico, fecha , demo= args
    df_remisiones = df_remisiones.merge(df_servicios, on='servicio_pos', how='inner')
    df_remisiones.drop(columns=['servicio_pos'], inplace=True)
    df_remisiones = df_remisiones.merge(persona, left_on='id_usuario', right_on='numero_identificacion', how='left')
    df_remisiones = df_remisiones.merge(medico, left_on='id_medico', right_on='cedula', how='left')
    df_remisiones['fecha_remision'] = pd.to_datetime(df_remisiones['fecha_remision'])
    df_remisiones = df_remisiones.merge(fecha, left_on='fecha_remision', right_on='date', how='left')
    df_remisiones = df_remisiones.merge(demo[['numero_identificacion','key_dim_demo']],
                                        left_on='id_usuario',right_on='numero_identificacion',how='left')
    df_remisiones = df_remisiones[['codigo_remision',
                                   'key_dim_demo',
                                   'key_dim_servicio',
                                   'key_dim_persona',
                                   'key_dim_medico',
                                   'key_dim_fecha',
                                   'costo']]
    return df_remisiones

# Agregar estas 5 funciones al FINAL del archivo existente:
# proyectoETL/CS_etl_py/etl/transform.py
# (no se toca nada de lo que ya esta ahi)

def transform_fecha_mensajeria() -> DataFrame:
    """
    NOTA DE NOMBRE: se llama 'transform_fecha_mensajeria' (no 'transform_fecha')
    porque ya existe una funcion transform_fecha() en este archivo para el
    proyecto medico (rango 2005-2009, plantilla de clase). Cuando el equipo
    confirme que ese codigo medico ya no se usa, se puede borrar y renombrar
    esta funcion a transform_fecha() sin el sufijo.
    """
    dim_fecha = pd.DataFrame({"fecha_completa": pd.date_range(start='1/1/2023', end='12/31/2026', freq='D')})
    dim_fecha["ano"] = dim_fecha["fecha_completa"].dt.year
    dim_fecha["mes"] = dim_fecha["fecha_completa"].dt.month
    dim_fecha["dia"] = dim_fecha["fecha_completa"].dt.day
    dim_fecha["weekday"] = dim_fecha["fecha_completa"].dt.weekday
    dim_fecha["quarter"] = dim_fecha["fecha_completa"].dt.quarter
    dim_fecha["day_of_year"] = dim_fecha["fecha_completa"].dt.day_of_year
    dim_fecha["day_of_month"] = dim_fecha["fecha_completa"].dt.days_in_month
    dim_fecha["nombre_mes"] = dim_fecha["fecha_completa"].dt.month_name()
    dim_fecha["nombre_dia"] = dim_fecha["fecha_completa"].dt.day_name()
    dim_fecha["date_str"] = dim_fecha["fecha_completa"].dt.strftime("%d/%m/%Y")
    co_holidays = holidays.CO(language="es")
    dim_fecha["is_Holiday"] = dim_fecha["fecha_completa"].apply(lambda x: x in co_holidays)
    dim_fecha["holiday"] = dim_fecha["fecha_completa"].apply(lambda x: co_holidays.get(x))
    dim_fecha["weekend"] = dim_fecha["weekday"].apply(lambda x: x > 4)
    dim_fecha["saved"] = date.today()
    return dim_fecha


def transform_hora() -> DataFrame:
    dim_hora = pd.DataFrame({"minute_of_day": range(24 * 60)})
    dim_hora["hora"] = dim_hora["minute_of_day"] // 60
    dim_hora["minuto"] = dim_hora["minute_of_day"] % 60
    dim_hora["hour_12"] = dim_hora["hora"].apply(lambda h: 12 if h % 12 == 0 else h % 12)
    dim_hora["meridiem"] = dim_hora["hora"].apply(lambda h: "AM" if h < 12 else "PM")
    dim_hora["time_str"] = dim_hora.apply(lambda r: f"{r['hora']:02d}:{r['minuto']:02d}:00", axis=1)
    dim_hora["time_12_str"] = dim_hora.apply(
        lambda r: f"{r['hour_12']:02d}:{r['minuto']:02d} {r['meridiem']}", axis=1
    )

    def franja_horaria(hour):
        if 5 <= hour < 12:
            return "Manana"
        if 12 <= hour < 18:
            return "Tarde"
        return "Noche"

    dim_hora["franja_horaria"] = dim_hora["hora"].apply(franja_horaria)
    dim_hora["is_business_hour"] = dim_hora["hora"].between(8, 17)
    dim_hora["saved"] = date.today()
    return dim_hora


def transform_estado(dim_estado: DataFrame) -> DataFrame:
    dim_estado = dim_estado.drop(columns=['descripcion'])
    orden_secuencia_map = {
        'Iniciado': 1,
        'Con mensajero Asignado': 2,
        'Recogido por mensajero': 3,
        'Entregado en destino': 4,
        'Terminado completo': 5,
        'Con novedad': None,
    }
    dim_estado['orden_secuencia'] = dim_estado['nombre'].map(orden_secuencia_map)
    sin_mapear = dim_estado[~dim_estado['nombre'].isin(orden_secuencia_map.keys())]
    if not sin_mapear.empty:
        print('ATENCION: hay estados sin mapear en transform_estado:', sin_mapear['nombre'].tolist())
    dim_estado = dim_estado.rename(columns={'nombre': 'nombre_estado'})
    dim_estado['saved'] = date.today()
    return dim_estado


def transform_sede(dim_sede: DataFrame) -> DataFrame:
    dim_sede = dim_sede.replace({np.nan: 'no aplica', ' ': 'no aplica', '': 'no_aplica'})
    dim_sede['saved'] = date.today()
    return dim_sede


def transform_tipo_servicio(prioridades: DataFrame) -> DataFrame:
    def normalizar_prioridad(valor):
        return valor.split(':')[0].strip().lower()

    prioridades = prioridades.copy()
    prioridades['grupo'] = prioridades['prioridad'].apply(normalizar_prioridad)

    grupos_esperados = {'alta', 'media', 'baja'}
    grupos_encontrados = set(prioridades['grupo'].unique())
    if grupos_encontrados - grupos_esperados:
        print('ATENCION: grupos de prioridad no contemplados:', grupos_encontrados - grupos_esperados)

    catalogo_tipo_servicio = {
        'alta': {'nombre_tipo': 'Urgente (menos de 1 hora)',
                 'descripcion': 'Entrega prioritaria inmediata. Tiempo objetivo de entrega menor a 60 minutos desde la solicitud.'},
        'media': {'nombre_tipo': 'Media (1 a 3 horas)',
                  'descripcion': 'Entrega en una ventana de 1 a 3 horas desde la solicitud.'},
        'baja': {'nombre_tipo': 'Baja (transcurso del dia)',
                 'descripcion': 'Entrega sin urgencia inmediata, dentro del transcurso del dia.'},
    }
    dim_tipo_servicio = pd.DataFrame([{'grupo': k, **v} for k, v in catalogo_tipo_servicio.items()])
    dim_tipo_servicio['saved'] = date.today()
    return dim_tipo_servicio

