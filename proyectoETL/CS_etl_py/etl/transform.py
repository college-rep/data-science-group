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

