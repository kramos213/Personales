import pandas as pd
import os
import chardet
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import platform

# Configurar rutas según el sistema operativo
if platform.system() == "Windows":
    database_path = "Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db"
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
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

# Cargar lista de archivos procesados
if os.path.exists(processed_files_path):
    with open(processed_files_path, 'r') as f:
        processed_files = set(f.read().splitlines())
else:
    processed_files = set()

# Obtener archivos no procesados
all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.csv')]
unprocessed_files = [f for f in all_files if f not in processed_files]

# Salir si no hay archivos nuevos
if not unprocessed_files:
    print("No hay archivos nuevos para procesar.")
    exit()

# Procesar archivos nuevos
dataframes = []
for i, file in enumerate(unprocessed_files):
    print(f"Leyendo archivo {i + 1}/{len(unprocessed_files)}: {file}")
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
            f.write(f"{file}\n")
    except Exception as e:
        print(f"  - Error al leer el archivo {file}: {e}")

# Verificar si hay DataFrames consolidados
if not dataframes:
    print("\nNo se pudieron consolidar archivos.")
    exit()

# Concatenar solo los DataFrames exitosos
df = pd.concat(dataframes, ignore_index=True)
print("\nConsolidación completada.")

# Limpiar y normalizar datos
df_cleaned = df.dropna()
df_cleaned['Fecha'] = pd.to_datetime(df_cleaned['Fecha'], errors='coerce')
df_cleaned.rename(columns=lambda x: x.strip().lower().replace(' ', '_'), inplace=True)

# Convertir tipos de datos
df_cleaned['ip_del_switch'] = df_cleaned['ip_del_switch'].astype(str)
df_cleaned['área'] = df_cleaned['área'].astype(str)
df_cleaned['evento'] = df_cleaned['evento'].astype(str)
df_cleaned['puerto'] = df_cleaned['puerto'].astype(str)
df_cleaned['detalles'] = df_cleaned['detalles'].astype(str)

# Conectar al Data Warehouse
engine = create_engine(f'sqlite:///{database_path}')

# Verificar la existencia de la tabla
with engine.connect() as connection:
    try:
        query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='Reporte_switches';")
        result = connection.execute(query)
        table_exists = result.fetchone()
        if table_exists:
            print("La tabla 'Reporte Switches' ya existe.")
        else:
            print("La tabla 'Reporte Switches' no existe, creando tabla nueva.")
    except Exception as e:
        print(f"Error al verificar la existencia de la tabla: {e}")
        exit()

# Cargar los datos en la base de datos
try:
    table_name = "Reporte_switches"
    df_cleaned.to_sql(table_name, engine, if_exists='append', index=False)
    print(f"Datos cargados en el Data Warehouse en la tabla '{table_name}'.")
except Exception as e:
    print(f"Error al cargar los datos en la base de datos: {e}")
    exit()

# Validar que los datos están en la base de datos
try:
    with engine.connect() as connection:
        query = text(f"SELECT COUNT(*) FROM {table_name}")
        result = connection.execute(query)
        print(f"Total de registros en el Data Warehouse: {result.scalar()}")
except Exception as e:
    print(f"Error al validar los datos en la base de datos: {e}")
    exit()
