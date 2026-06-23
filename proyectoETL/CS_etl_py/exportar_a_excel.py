"""
Exporta las 5 dimensiones de la base ETL a un solo archivo Excel
(una hoja por tabla), listo para subir directo a Power BI Online.

Requiere: pip install openpyxl  (ademas de pandas y sqlalchemy que ya tienes)
"""
import pandas as pd
from sqlalchemy import create_engine

# Ajusta estos datos a los de tu config.yml (seccion ETL_PRO)
engine = create_engine("postgresql://postgres:postgres@localhost:5432/fast_and_safe_etl")

tablas = ["dim_fecha", "dim_hora", "dim_estado", "dim_sede", "dim_tipo_servicio"]

with pd.ExcelWriter("fast_and_safe_dw.xlsx") as writer:
    for tabla in tablas:
        df = pd.read_sql_table(tabla, engine)
        df.to_excel(writer, sheet_name=tabla, index=False)
        print(f"{tabla}: {len(df)} filas exportadas")

print("\nListo: fast_and_safe_dw.xlsx creado en esta carpeta")