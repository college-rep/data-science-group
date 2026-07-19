"""
Consultas de negocio - Fast and Safe.

Ejecuta las nueve preguntas del proyecto sobre la bodega de datos y muestra
los resultados en consola.

Uso:
    python consultas.py           # ejecuta las nueve preguntas
    python consultas.py 3 8       # ejecuta solo las preguntas indicadas
"""

import sys

import yaml
import pandas as pd
from sqlalchemy import create_engine, text

pd.set_option("display.max_rows", 60)
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

etl = config["ETL_PRO"]
etl_conn = create_engine(
    f"{etl['drivername']}://{etl['user']}:{etl['password']}@{etl['host']}:{etl['port']}/{etl['dbname']}"
)

# Servicios que completaron el flujo (llegaron a "Entregado en destino").
SERVICIOS_COMPLETOS = """
    SELECT servicio_id FROM hecho_seguimiento_fases WHERE estado_id = 5
"""

CONSULTAS = {
1: ("En qué meses del año los clientes solicitan más servicios", """
    SELECT to_char(fecha_solicitud, 'YYYY-MM') AS mes,
           count(*) AS servicios
    FROM hecho_servicio
    GROUP BY mes
    ORDER BY mes
"""),

2: ("Cuáles son los días donde más solicitudes hay", """
    SELECT CASE extract(isodow FROM fecha_solicitud)
               WHEN 1 THEN 'Lunes'
               WHEN 2 THEN 'Martes'
               WHEN 3 THEN 'Miercoles'
               WHEN 4 THEN 'Jueves'
               WHEN 5 THEN 'Viernes'
               WHEN 6 THEN 'Sabado'
               ELSE 'Domingo'
           END AS dia_semana,
           extract(isodow FROM fecha_solicitud)::int AS orden,
           count(*) AS servicios
    FROM hecho_servicio
    GROUP BY dia_semana, orden
    ORDER BY orden
"""),

3: ("A qué hora los mensajeros están más ocupados", """
    SELECT h.hora,
           count(*) AS asignaciones
    FROM hecho_seguimiento_fases f
    JOIN dim_hora h ON f.id_hora = h.minute_of_day
    WHERE f.estado_id = 2
    GROUP BY h.hora
    ORDER BY h.hora
"""),

4: ("Número de servicios por cliente y por mes", """
    SELECT c.nombre_empresa,
           to_char(s.fecha_solicitud, 'YYYY-MM') AS mes,
           count(*) AS servicios
    FROM hecho_servicio s
    JOIN dim_cliente c ON s.id_cliente = c.id_cliente
    GROUP BY c.nombre_empresa, mes
    ORDER BY c.nombre_empresa, mes
"""),

5: ("Mensajeros más eficientes (los que más servicios prestan)", f"""
    SELECT f.mensajero_id::int AS mensajero_id,
           count(DISTINCT f.servicio_id) AS servicios
    FROM hecho_seguimiento_fases f
    WHERE f.mensajero_id IS NOT NULL
      AND f.servicio_id IN ({SERVICIOS_COMPLETOS})
    GROUP BY f.mensajero_id
    ORDER BY servicios DESC
    LIMIT 15
"""),

6: ("Sedes que más servicios solicitan por cada cliente", """
    SELECT c.nombre_empresa,
           d.nombre_sede,
           count(*) AS servicios
    FROM hecho_servicio s
    JOIN dim_cliente c ON s.id_cliente = c.id_cliente
    JOIN dim_sede d ON s.id_sede = d.sede_id
    GROUP BY c.nombre_empresa, d.sede_id, d.nombre_sede
    ORDER BY servicios DESC
"""),

7: ("Tiempo promedio de entrega (solicitud -> cierre)", f"""
    WITH tiempo_por_servicio AS (
        SELECT servicio_id, sum(tiempo_espera_min) AS total_min
        FROM hecho_seguimiento_fases
        WHERE servicio_id IN ({SERVICIOS_COMPLETOS})
        GROUP BY servicio_id
    )
    SELECT count(*) AS servicios,
           round(avg(total_min)::numeric, 1) AS promedio_min,
           round(percentile_cont(0.5) WITHIN GROUP (ORDER BY total_min)::numeric, 1) AS mediana_min
    FROM tiempo_por_servicio
"""),

8: ("Tiempos de espera por fase / dónde hay más demoras", f"""
    SELECT e.nombre_estado,
           e.orden_secuencia::int AS orden_secuencia,
           round(avg(f.tiempo_espera_min)::numeric, 1) AS promedio_min,
           round(percentile_cont(0.5) WITHIN GROUP (ORDER BY f.tiempo_espera_min)::numeric, 1) AS mediana_min,
           count(DISTINCT f.servicio_id) AS servicios
    FROM hecho_seguimiento_fases f
    JOIN dim_estado e ON f.estado_id = e.id
    WHERE f.servicio_id IN ({SERVICIOS_COMPLETOS})
      AND e.nombre_estado <> 'Terminado completo'
      AND e.orden_secuencia IS NOT NULL
    GROUP BY e.nombre_estado, e.orden_secuencia
    ORDER BY e.orden_secuencia NULLS LAST
"""),

9: ("Novedades que más se presentan durante la prestación", """
    SELECT n.categoria_novedad,
           sum(f.num_novedades)::int AS total_novedades
    FROM hecho_novedad f
    JOIN dim_novedad n ON f.tipo_novedad_id = n.id_novedad
    GROUP BY n.categoria_novedad
    ORDER BY total_novedades DESC
"""),
}


def ejecutar(numero):
    titulo, sql = CONSULTAS[numero]
    print("=" * 70)
    print(f"PREGUNTA {numero}. {titulo}")
    print("=" * 70)
    try:
        df = pd.read_sql_query(text(sql), etl_conn)
        if df.empty:
            print("(sin resultados)")
        else:
            print(df.to_string(index=False))
    except Exception as e:
        print(f"ERROR: {str(e).splitlines()[0]}")
    print()


def main():
    args = [a for a in sys.argv[1:] if a.isdigit()]
    numeros = [int(a) for a in args] if args else sorted(CONSULTAS)
    for n in numeros:
        if n in CONSULTAS:
            ejecutar(n)
        else:
            print(f"La pregunta {n} no existe.\n")


if __name__ == "__main__":
    main()