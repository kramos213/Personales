import pandas as pd
import os
import chardet
from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Ruta a la carpeta con tus CSV
folder_path = "Z:/Monitoreo de red/Monitoreo red"

# Ruta para almacenar el Data Warehouse
database_path = "Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db"
os.makedirs(os.path.dirname(database_path), exist_ok=True)

# Función para detectar la codificación de un archivo
def detectar_codificacion(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000)  # Leer solo los primeros 10 KB para acelerar
    resultado = chardet.detect(rawdata)
    return resultado['encoding']

# Consolidar todos los CSV en un solo DataFrame
all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.csv')]

dataframes = []
for i, file in enumerate(all_files):
    print(f"Leyendo archivo {i + 1}/{len(all_files)}: {file}")
    try:
        # Detectar la codificación del archivo
        encoding = detectar_codificacion(file)
        print(f"  - Codificación detectada: {encoding}")
        
        # Intentar leer el archivo con la codificación detectada
        df = pd.read_csv(file, encoding=encoding, delimiter=',', on_bad_lines='skip')
        print(f"  - Columnas detectadas: {df.columns}")
        dataframes.append(df)
    except Exception as e:
        print(f"  - Error al leer el archivo {file}: {e}")

# Concatenar solo los DataFrames exitosos
if dataframes:
    df = pd.concat(dataframes, ignore_index=True)
    print("\nConsolidación completada.")
else:
    print("\nNo se pudieron consolidar archivos.")
    exit()  # Salir si no hay datos consolidados

# Limpiar datos
df_cleaned = df.dropna()  # Eliminar filas con valores nulos

# Renombrar columnas de forma segura
df_cleaned = df_cleaned.rename(columns=lambda x: x.strip().lower().replace(' ', '_'))

# Conectar a un Data Warehouse (SQLite como ejemplo)
engine = create_engine(f'sqlite:///{database_path}')

# Verificar si la tabla 'Monitoreo red' existe antes de cargar los datos
with engine.connect() as connection:
    try:
        query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='Monitoreo red';")
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
    table_name = "Monitoreo red"
    df_cleaned.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Datos cargados en el Data Warehouse en la tabla '{table_name}'.")
except Exception as e:
    print(f"Error al cargar los datos en la base de datos: {e}")
    exit()

# Validar que los datos están en la base de datos
try:
    with engine.connect() as connection:
        query = text(f"SELECT COUNT(*) FROM 'Monitoreo red'")
        result = connection.execute(query)
        print(f"Total de registros en el Data Warehouse: {result.scalar()}")
except Exception as e:
    print(f"Error al validar los datos en la base de datos: {e}")
    exit()
