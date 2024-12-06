import pandas as pd
import os
import chardet
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from datetime import datetime, timedelta

# Rutas y configuración
folder_path = "Z:/Monitoreo de red/Monitoreo red"
database_path = "Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db"
processed_files_path = "Z:/Monitoreo de red/DataWarehouse/processed_files_mred.txt"

os.makedirs(os.path.dirname(database_path), exist_ok=True)

# Función para detectar la codificación de un archivo
def detectar_codificacion(file_path):
    try:
        with open(file_path, 'rb') as f:
            rawdata = f.read(10000)
        resultado = chardet.detect(rawdata)
        return resultado['encoding'] or 'utf-8'
    except Exception as e:
        print(f"Error detectando la codificación de {file_path}: {e}")
        return 'utf-8'

# Función para consolidar y cargar datos
def procesar_archivos_csv(folder_path, processed_files_path, database_path):
    # Leer lista de archivos procesados
    processed_files = set()
    if os.path.exists(processed_files_path):
        with open(processed_files_path, 'r') as file:
            processed_files = set(file.read().splitlines())

    # Obtener lista de archivos no procesados
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.csv')]
    unprocessed_files = [
        f for f in all_files if os.path.abspath(f) not in processed_files
    ]

    if not unprocessed_files:
        print("No hay archivos nuevos para procesar.")
        return None

    # Consolidar datos en un único DataFrame
    dataframes = []
    for file in unprocessed_files:
        try:
            encoding = detectar_codificacion(file)
            df = pd.read_csv(file, encoding=encoding, delimiter=None, on_bad_lines='skip')
            dataframes.append(df)

            # Registrar archivo como procesado
            with open(processed_files_path, 'a') as processed_file:
                processed_file.write(f"{os.path.abspath(file)}\n")
            print(f"Archivo procesado: {file}")
        except Exception as e:
            print(f"Error al procesar el archivo {file}: {e}")

    if dataframes:
        return pd.concat(dataframes, ignore_index=True)
    return None

# Procesar archivos y cargar al Data Warehouse
df = procesar_archivos_csv(folder_path, processed_files_path, database_path)
if df is not None:
    # Limpieza básica
    df_cleaned = df.dropna()
    df_cleaned.columns = [col.strip().lower().replace(' ', '_') for col in df_cleaned.columns]

    # Normalización de datos
    for col in df_cleaned.columns:
        if 'fecha' in col or 'date' in col:
            try:
                df_cleaned[col] = pd.to_datetime(df_cleaned[col], errors='coerce')
            except Exception as e:
                print(f"Error al convertir la columna {col} a formato de fecha: {e}")

    # Conectar al Data Warehouse
    engine = create_engine(f'sqlite:///{database_path}')
    table_name = "Monitoreo_red"

    try:
        with engine.connect() as connection:
            # Verificar si la tabla ya existe
            query = text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            table_exists = connection.execute(query).fetchone() is not None

            if table_exists:
                print("La tabla ya existe. Actualizando datos...")
                existing_df = pd.read_sql(f"SELECT * FROM {table_name}", connection)
                combined_df = pd.concat([existing_df, df_cleaned], ignore_index=True).drop_duplicates()
                combined_df.to_sql(table_name, engine, if_exists='replace', index=False)
            else:
                print("Creando nueva tabla y cargando datos.")
                df_cleaned.to_sql(table_name, engine, if_exists='replace', index=False)

            # Validar datos cargados
            query = text(f"SELECT COUNT(*) FROM {table_name}")
            total_records = connection.execute(query).scalar()
            print(f"Total de registros en la tabla '{table_name}': {total_records}")
    except Exception as e:
        print(f"Error al cargar datos en el Data Warehouse: {e}")
else:
    print("No se consolidaron datos.")
