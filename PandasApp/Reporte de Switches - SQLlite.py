import os
import pandas as pd
from sqlalchemy import create_engine, text
import chardet
import platform

# Configurar rutas según el sistema operativo
if platform.system() == "Windows":
    database_path = "Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db"
    folder_path = "Z:/Monitoreo de red/Reporte de Switches"
    processed_files_path = "Z:/Monitoreo de red/DataWarehouse/processed_files.txt"
else:  # macOS o Linux
    database_path = "/Volumes/Sophos/Monitoreo de red/DataWarehouse/DataWarehouse.db"
    folder_path = "/Volumes/Sophos/Monitoreo de red/Reporte de Switches"
    processed_files_path = "/Volumes/Sophos/Monitoreo de red/DataWarehouse/processed_files.txt"

# Función para detectar la codificación de un archivo
def detectar_codificacion(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000)  # Leer los primeros 10 KB
    resultado = chardet.detect(rawdata)
    return resultado['encoding']

# Función para cargar y procesar los archivos CSV
def procesar_archivos_csv(folder_path, processed_files_path):
    # Leer lista de archivos procesados
    if os.path.exists(processed_files_path):
        with open(processed_files_path, 'r') as file:
            processed_files = set(file.read().splitlines())
    else:
        processed_files = set()

    # Obtener lista de archivos no procesados
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.csv')]
    unprocessed_files = [f for f in all_files if f not in processed_files]

    if not unprocessed_files:
        print("No hay archivos nuevos para procesar.")
        return None

    dataframes = []
    for i, file in enumerate(unprocessed_files, 1):
        print(f"Leyendo archivo {i}/{len(unprocessed_files)}: {file}")
        try:
            # Detectar codificación
            encoding = detectar_codificacion(file)
            print(f"  - Codificación detectada: {encoding}")
            
            # Leer el archivo CSV
            df = pd.read_csv(file, encoding=encoding, delimiter=',', on_bad_lines='skip')
            dataframes.append(df)


            # Registrar el archivo como procesado
            with open(processed_files_path, 'a') as f:
                f.write(f"{file}\n")
        except Exception as e:
            print(f"Error al procesar el archivo {file}: {e}")

    if dataframes:
        return pd.concat(dataframes, ignore_index=True)
    else:
        print("No se pudieron consolidar archivos.")
        return None

# Función para limpiar y normalizar el DataFrame
def limpiar_y_normalizar_df(df):
    df_cleaned = df.dropna()
    df_cleaned['Fecha'] = pd.to_datetime(df_cleaned['Fecha'], errors='coerce')
    df_cleaned.rename(columns=lambda x: x.strip().lower().replace(' ', '_'), inplace=True)

    # Convertir tipos de datos
    df_cleaned['ip_del_switch'] = df_cleaned['ip_del_switch'].astype(str)
    df_cleaned['área'] = df_cleaned['área'].astype(str)
    df_cleaned['evento'] = df_cleaned['evento'].astype(str)
    df_cleaned['puerto'] = df_cleaned['puerto'].astype(str)
    df_cleaned['detalles'] = df_cleaned['detalles'].astype(str)
    return df_cleaned

# Función para cargar datos a la base de datos
def cargar_datos_bd(df, database_path, table_name):
    engine = create_engine(f'sqlite:///{database_path}')
    with engine.connect() as connection:
        # Verificar si la tabla existe
        query = text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        result = connection.execute(query)
        table_exists = result.fetchone()

        if table_exists:
            print(f"La tabla '{table_name}' ya existe.")
        else:
            print(f"La tabla '{table_name}' no existe. Creando tabla nueva.")
            df.head(0).to_sql(table_name, engine, if_exists='replace', index=False)

    # Cargar datos
    try:
        df.to_sql(table_name, engine, if_exists='append', index=False)
        print(f"Datos cargados en la tabla '{table_name}'.")
    except Exception as e:
        print(f"Error al cargar los datos en la base de datos: {e}")
        return

    # Validar datos cargados
    with engine.connect() as connection:
        query = text(f"SELECT COUNT(*) FROM {table_name}")
        result = connection.execute(query)
        print(f"Total de registros en la tabla '{table_name}': {result.scalar()}")

# Main
df = procesar_archivos_csv(folder_path, processed_files_path)
if df is not None:
    df_cleaned = limpiar_y_normalizar_df(df)
    cargar_datos_bd(df_cleaned, database_path, "Reporte_switches")
