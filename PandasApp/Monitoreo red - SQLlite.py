import pandas as pd
import os
import chardet
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from datetime import datetime, timedelta

# Ruta a la carpeta con tus CSV
folder_path = "Z:/Monitoreo de red/Monitoreo red"

# Ruta para almacenar el Data Warehouse
database_path = "Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db"
os.makedirs(os.path.dirname(database_path), exist_ok=True)

# Ruta para almacenar los archivos procesados
processed_files_path = "Z:/Monitoreo de red/DataWarehouse/processed_files.txt"

# Función para detectar la codificación de un archivo
def detectar_codificacion(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000)  # Leer solo los primeros 10 KB para acelerar
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

    # Obtener lista de archivos en la carpeta
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.csv')]

    # Considerar archivos modificados en las últimas 24 horas
    last_24_hours = datetime.now() - timedelta(hours=24)
    unprocessed_files = [
        f for f in all_files if f not in processed_files and
        datetime.fromtimestamp(os.path.getmtime(f)) > last_24_hours
    ]

    # Imprimir información para depuración
    print("Archivos procesados:", processed_files)
    print("Archivos encontrados:", all_files)
    print("Archivos no procesados o recientes:", unprocessed_files)

    if not unprocessed_files:
        print("No hay archivos nuevos para procesar.")
        return None

    dataframes = []
    for i, file in enumerate(unprocessed_files, 1):
        print(f"Leyendo archivo {i}/{len(unprocessed_files)}: {file}")
        try:
            # Detectar la codificación del archivo
            encoding = detectar_codificacion(file)
            print(f"  - Codificación detectada: {encoding}")
            
            # Intentar leer el archivo con la codificación detectada
            df = pd.read_csv(file, encoding=encoding, delimiter=',', on_bad_lines='skip')
            print(f"  - Columnas detectadas: {df.columns}")
            dataframes.append(df)

            # Registrar el archivo como procesado
            with open(processed_files_path, 'a') as f:
                f.write(f"{os.path.abspath(file)}\n")
        except Exception as e:
            print(f"  - Error al leer el archivo {file}: {e}")

    if dataframes:
        return pd.concat(dataframes, ignore_index=True)
    else:
        print("No se pudieron consolidar archivos.")
        return None

# Consolidar archivos CSV recientes
df = procesar_archivos_csv(folder_path, processed_files_path)
if df is None:
    exit()  # Salir si no hay archivos para procesar

# Limpiar datos
df_cleaned = df.dropna()  # Eliminar filas con valores nulos

# Renombrar columnas de forma segura
df_cleaned = df_cleaned.rename(columns=lambda x: x.strip().lower().replace(' ', '_'))

# Conectar a un Data Warehouse (SQLite como ejemplo)
engine = create_engine(f'sqlite:///{database_path}')

# Verificar si la tabla 'Monitoreo red' existe antes de cargar los datos
with engine.connect() as connection:
    try:
        query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='Monitoreo_red';")
        result = connection.execute(query)
        table_exists = result.fetchone()
        if table_exists:
            print("La tabla 'Monitoreo red' ya existe.")
        else:
            print("La tabla 'Monitoreo red' no existe, creando tabla nueva.")
    except Exception as e:
        print(f"Error al verificar la existencia de la tabla: {e}")
        exit()

# Cargar los datos
try:
    table_name = "Monitoreo_red"
    df_cleaned.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Datos cargados en el Data Warehouse en la tabla '{table_name}'.")
except Exception as e:
    print(f"Error al cargar los datos en la base de datos: {e}")
    exit()

# Validar que los datos están en la base de datos
try:
    with engine.connect() as connection:
        query = text(f"SELECT COUNT(*) FROM 'Monitoreo_red'")
        result = connection.execute(query)
        print(f"Total de registros en el Data Warehouse: {result.scalar()}")
except Exception as e:
    print(f"Error al validar los datos en la base de datos: {e}")
    exit()
