import os
import pandas as pd
from sqlalchemy import create_engine, text
import chardet
import platform

# Configuración de rutas según el sistema operativo
if platform.system() == "Windows":
    database_path = "Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db"
    carpeta = "Z:/Monitoreo de red/Poe Puertos"
    processed_files_path = "Z:/Monitoreo de red/DataWarehouse/processed_files.txt"
else:
    database_path = "/Volumes/Sophos/Monitoreo de red/DataWarehouse/DataWarehouse.db"
    carpeta = "/Volumes/Sophos/Monitoreo de red/Poe Puertos"
    processed_files_path = "/Volumes/Sophos/Monitoreo de red/DataWarehouse/processed_files.txt"

# Listar archivos CSV en la carpeta
archivos_csv = [os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.endswith('.csv')]

# Leer lista de archivos procesados previamente
if os.path.exists(processed_files_path):
    with open(processed_files_path, 'r') as file:
        archivos_procesados = set(file.read().splitlines())
else:
    archivos_procesados = set()

# Identificar archivos pendientes de procesar
archivos_pendientes = [archivo for archivo in archivos_csv if archivo not in archivos_procesados]

# Lista para almacenar los DataFrames procesados
df_lista = []

# Función para detectar la codificación de un archivo
def detectar_codificacion(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000)  # Leer hasta 10 KB
    resultado = chardet.detect(rawdata)
    return resultado['encoding']

# Función para limpiar el DataFrame
def limpiar_df(df):
    columnas = ['Fecha y Hora', 'Área', 'Switch IP', 'Interface', 'Admin', 'Pri', 'Oper', 'Power (mW)', 'Device', 'Class', 'Max (mW)']
    df = df[columnas]  # Seleccionar columnas relevantes
    df = df.dropna(subset=columnas, how='all')  # Eliminar filas vacías
    df = df[df['Interface'] != 'Interface']  # Excluir filas que contienen encabezados repetidos
    df = df[df['Oper'] != 'Off']  # Filtrar filas donde 'Oper' sea 'Off'
    df = df.drop(columns=['Device'])  # Eliminar columna innecesaria
    return df

# Leer y procesar archivos pendientes
for i, archivo in enumerate(archivos_pendientes, 1):
    try:
        encoding = detectar_codificacion(archivo)  # Detectar codificación
        df = pd.read_csv(archivo, encoding=encoding)  # Cargar archivo en un DataFrame
        
        print(f"Leyendo archivo {i}/{len(archivos_pendientes)}: {archivo}")
        print(f"  - Codificación detectada: {encoding}")
        print(f"  - Columnas en el archivo: {df.columns.tolist()}")
        
        df_lista.append(limpiar_df(df))  # Limpiar y almacenar DataFrame
    except Exception as e:
        print(f"Error al procesar el archivo {archivo}: {e}")
        continue

# Concatenar DataFrames si hay datos
if df_lista:
    df_combinado = pd.concat(df_lista, ignore_index=True)

    # Conexión a la base de datos SQLite
    engine = create_engine(f'sqlite:///{database_path}')

    # Verificar si existe la tabla 'Reporte_POE' y fusionar datos
    with engine.connect() as connection:
        try:
            # Si la tabla no existe, crearla
            query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='Reporte_POE';")
            result = connection.execute(query)
            table_exists = result.fetchone()
            
            if not table_exists:
                print("La tabla 'Reporte_POE' no existe. Creándola...")
                df_combinado.head(0).to_sql('Reporte_POE', engine, if_exists='replace', index=False)

            # Cargar solo los datos nuevos
            else:
                print("Cargando datos nuevos en 'Reporte_POE'...")
                df_db = pd.read_sql("SELECT * FROM Reporte_POE", connection)
                df_nuevos = df_combinado.merge(df_db, how='left', indicator=True).loc[lambda x: x['_merge'] == 'left_only'].drop(columns=['_merge'])
                if not df_nuevos.empty:
                    df_nuevos.to_sql('Reporte_POE', engine, if_exists='append', index=False)
                    print(f"Se han agregado {len(df_nuevos)} registros nuevos.")
                else:
                    print("No se encontraron datos nuevos para agregar.")
        except Exception as e:
            print(f"Error al cargar los datos: {e}")
            exit()

    # Actualizar lista de archivos procesados
    with open(processed_files_path, 'a') as file:
        for archivo in archivos_pendientes:
            file.write(f"{archivo}\n")
else:
    print("No hay archivos nuevos para procesar.")
