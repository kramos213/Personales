import os
import pandas as pd
from sqlalchemy import create_engine, text
import chardet
from pathlib import Path
from datetime import datetime, timedelta

# Configurar rutas según el sistema operativo
base_path = Path("Z:/Monitoreo de red" if os.name == "nt" else "/Volumes/Sophos/Monitoreo de red")
database_path = base_path / "DataWarehouse/DataWarehouse.db"
folder_path = base_path / "Reporte de Switches"
processed_files_path = base_path / "DataWarehouse/processed_files_RepSwitch.txt"

# Crear directorios necesarios
processed_files_path.parent.mkdir(parents=True, exist_ok=True)

# Función para detectar la codificación de un archivo
def detectar_codificacion(file_path):
    try:
        with open(file_path, 'rb') as f:
            rawdata = f.read(10000)  # Leer los primeros 10 KB
        resultado = chardet.detect(rawdata)
        return resultado['encoding'] or 'utf-8'
    except Exception as e:
        print(f"Error detectando la codificación del archivo {file_path}: {e}")
        return 'utf-8'  # Valor predeterminado si falla la detección

# Función para procesar archivos CSV
def procesar_archivos_csv(folder_path, processed_files_path, debug=False):
    processed_files = set(processed_files_path.read_text().splitlines()) if processed_files_path.exists() else set()
    all_files = [file for file in folder_path.glob("*.csv")]

    unprocessed_files = [
        file for file in all_files if str(file) not in processed_files
    ]

    if debug:
        print("Archivos procesados:", processed_files)
        print("Archivos encontrados:", all_files)
        print("Archivos no procesados:", unprocessed_files)

    if not unprocessed_files:
        print("No hay archivos nuevos para procesar.")
        return None

    dataframes = []
    for file in unprocessed_files:
        try:
            encoding = detectar_codificacion(file)
            df = pd.read_csv(file, encoding=encoding, on_bad_lines='skip')
            dataframes.append(df)
            with processed_files_path.open('a') as f:
                f.write(f"{file}\n")
        except Exception as e:
            print(f"Error al procesar el archivo {file}: {e}")

    return pd.concat(dataframes, ignore_index=True) if dataframes else None

# Función para limpiar y normalizar un DataFrame
def limpiar_y_normalizar_df(df):
    try:
        df_cleaned = df.dropna()
        df_cleaned.columns = [col.strip().lower().replace(' ', '_') for col in df_cleaned.columns]

        for col in df_cleaned.columns:
            if 'fecha' in col or 'date' in col:
                df_cleaned[col] = pd.to_datetime(df_cleaned[col], errors='coerce')

        return df_cleaned
    except Exception as e:
        print(f"Error al limpiar y normalizar el DataFrame: {e}")
        return None

# Función para cargar datos en la base de datos sin duplicados
def cargar_datos_bd_sin_duplicados(df, database_path, table_name):
    engine = create_engine(f'sqlite:///{database_path}')
    with engine.connect() as connection:
        # Crear tabla si no existe
        if not connection.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")).fetchone():
            print(f"La tabla '{table_name}' no existe. Creando tabla nueva.")
            df.to_sql(table_name, engine, if_exists='replace', index=False)
        else:
            print("Actualizando datos existentes.")
            existing_df = pd.read_sql_query(f"SELECT * FROM {table_name}", engine)
            combined_df = pd.concat([existing_df, df]).drop_duplicates()
            combined_df.to_sql(table_name, engine, if_exists='replace', index=False)

        # Validar datos cargados
        total_records = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        print(f"Total de registros en la tabla '{table_name}': {total_records}")

# Main
def main():
    df = procesar_archivos_csv(folder_path, processed_files_path, debug=True)
    if df is not None:
        df_cleaned = limpiar_y_normalizar_df(df)
        if df_cleaned is not None:
            cargar_datos_bd_sin_duplicados(df_cleaned, database_path, "Reporte_switches")
        else:
            print("El DataFrame no pudo ser limpiado.")
    else:
        print("No se encontraron datos para procesar.")

if __name__ == "__main__":
    main()
