import os
import pandas as pd
from sqlalchemy import create_engine, text
import chardet
import platform

if platform.system() == "Windows":
    # Ruta de la base de datos (SQLite en este caso)
    database_path = "Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db"
    # Definir la carpeta con los archivos CSV
    carpeta = "Z:/Monitoreo de red/Poe Puertos"
    processed_files_path = "Z:/Monitoreo de red/DataWarehouse/processed_files.txt"
else:  # macOS o Linux
    database_path = "/Volumes/Sophos/Monitoreo de red/DataWarehouse/DataWarehouse.db"
    carpeta = "/Volumes/Sophos/Monitoreo de red/Poe Puertos"
    processed_files_path = "/Volumes/Sophos/Monitoreo de red/DataWarehouse/processed_files.txt"


# Obtener todos los archivos CSV en la carpeta
archivos_csv = [os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.endswith('.csv')]

# Leer archivos procesados previamente
if os.path.exists(processed_files_path):
    with open(processed_files_path, 'r') as file:
        archivos_procesados = set(file.read().splitlines())
else:
    archivos_procesados = set()

# Filtrar archivos que aún no se han procesado
archivos_pendientes = [archivo for archivo in archivos_csv if archivo not in archivos_procesados]

# Crear una lista para almacenar los DataFrames
df_lista = []

# Función para detectar codificación de archivos CSV
def detectar_codificacion(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000)  # Leer los primeros 10 KB
    resultado = chardet.detect(rawdata)
    return resultado['encoding']

# Función para limpiar y filtrar el DataFrame
def limpiar_df(df):
    columnas = ['Fecha y Hora', 'Área', 'Switch IP', 'Interface', 'Admin', 'Pri', 'Oper', 'Power (mW)', 'Device', 'Class', 'Max (mW)']
    df = df[columnas]
    df = df.dropna(subset=columnas, how='all')  # Eliminar filas donde todas las columnas están vacías
    df = df[df['Interface'] != 'Interface']  # Eliminar filas con 'Interface' como valor en la columna 'Interface'
    df = df[df['Oper'] != 'Off']  # Eliminar filas con 'Oper' como 'Off'
    df = df.drop(columns=['Device'])
    return df

# Leer los archivos CSV pendientes y concatenarlos
for i, archivo in enumerate(archivos_pendientes, 1):
    try:
        # Detectar la codificación
        encoding = detectar_codificacion(archivo)
        
        # Cargar el archivo CSV en un DataFrame
        df = pd.read_csv(archivo, encoding=encoding)
        
        # Mostrar información sobre el archivo
        print(f"Leyendo archivo {i}/{len(archivos_pendientes)}: {archivo}")
        print(f"  - Codificación detectada: {encoding}")
        print(f"  - Columnas en el archivo: {df.columns.tolist()}")
        
        # Limpiar el DataFrame y agregarlo a la lista
        df_lista.append(limpiar_df(df))
    except Exception as e:
        print(f"Error al procesar el archivo {archivo}: {e}")
        continue  # Continúa con el siguiente archivo en caso de error

# Concatenar todos los DataFrames
if df_lista:
    df_combinado = pd.concat(df_lista, ignore_index=True)

    # Conectar a la base de datos
    engine = create_engine(f'sqlite:///{database_path}')

    # Verificar si la tabla 'Reporte_POE' existe antes de cargar los datos
    with engine.connect() as connection:
        try:
            query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='Reporte_POE';")
            result = connection.execute(query)
            table_exists = result.fetchone()
            
            if table_exists:
                print("La tabla 'Reporte_POE' ya existe.")
            else:
                print("La tabla 'Reporte_POE' no existe, creando tabla nueva.")
                # Crear tabla si no existe
                df_combinado.head(0).to_sql('Reporte_POE', engine, if_exists='replace', index=False)
        except Exception as e:
            print(f"Error al verificar la existencia de la tabla: {e}")
            exit()

    # Cargar los datos en la tabla del Data Warehouse
    try:
        table_name = "Reporte_POE"
        df_combinado.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Datos cargados en el Data Warehouse en la tabla '{table_name}'.")
    except Exception as e:
        print(f"Error al cargar los datos en la base de datos: {e}")
        exit()

    # Validar que los datos están en la base de datos
    try:
        with engine.connect() as connection:
            query = text(f"SELECT COUNT(*) FROM 'Reporte_POE'")
            result = connection.execute(query)
            print(f"Total de registros en el Data Warehouse: {result.scalar()}")
    except Exception as e:
        print(f"Error al validar los datos en la base de datos: {e}")
        exit()

    # Actualizar la lista de archivos procesados
    with open(processed_files_path, 'a') as file:
        for archivo in archivos_pendientes:
            file.write(f"{archivo}\n")
else:
    print("No hay archivos nuevos para procesar.")
