import os
import pandas as pd
from sqlalchemy import create_engine, text
import chardet

# Ruta de la base de datos (SQLite en este caso)
database_path = "Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db"

# Definir la carpeta con los archivos CSV
carpeta = r"Z:/Monitoreo de red/Prueba"

# Obtener todos los archivos CSV en la carpeta
archivos_csv = [os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.endswith('.csv')]

# Crear una lista para almacenar los DataFrames
df_lista = []

# Función para detectar codificación de archivos CSV
def detectar_codificacion(archivo):
    with open(archivo, 'rb') as file:
        raw_data = file.read()
        resultado = chardet.detect(raw_data)
        return resultado['encoding']

# Función para limpiar y filtrar el DataFrame
def limpiar_df(df):
    # Filtrar las columnas necesarias
    columnas = ['Fecha y Hora', 'Área', 'Switch IP', 'Interface', 'Admin', 'Pri', 'Oper', 'Power (mW)', 'Device', 'Class', 'Max (mW)']
    df = df[columnas]
    
    # Limpiar filas vacías o con valores no deseados
    df = df.dropna(subset=columnas, how='all')  # Eliminar filas donde todas las columnas están vacías
    df = df[df['Interface'] != 'Interface']  # Eliminar filas con 'Interface' como valor en la columna 'Interface'
    df = df[df['Oper'] != 'Off']  # Eliminar filas con 'Interface' como valor en la columna 'Interface'
    df = df.drop(columns=['Device'])

    return df

# Leer los archivos CSV y concatenarlos
for i, archivo in enumerate(archivos_csv, 1):
    try:
        # Detectar la codificación
        encoding = detectar_codificacion(archivo)
        
        # Cargar el archivo CSV en un DataFrame
        df = pd.read_csv(archivo, encoding=encoding)
        
        # Mostrar información sobre el archivo
        print(f"Leyendo archivo {i}/{len(archivos_csv)}: {archivo}")
        print(f"  - Codificación detectada: {encoding}")
        print(f"  - Columnas en el archivo: {df.columns.tolist()}")
        #print(f"  - Primeras filas:\n{df.head()}")
        
        # Limpiar el DataFrame y agregarlo a la lista
        df_lista.append(limpiar_df(df))
    except Exception as e:
        print(f"Error al procesar el archivo {archivo}: {e}")
        continue  # Continúa con el siguiente archivo en caso de error

# Concatenar todos los DataFrames
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
