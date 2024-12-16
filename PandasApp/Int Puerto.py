import pandas as pd
import os
import glob
from sqlalchemy import create_engine, text
import logging

# Configuración de logs
logging.basicConfig(
    filename='procesamiento.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Definir el directorio donde están los archivos CSV
directorio = 'C:/Users/kramos/Desktop/Log de Script/Reporte Puerto/'

# Usar glob para encontrar todos los archivos CSV en cualquier subcarpeta que empiece con "P"
archivos_csv = glob.glob(os.path.join(directorio, 'P*/**/*.csv'), recursive=True)

# Configurar la conexión al Data Warehouse (SQLite en este caso)
database_path = 'Z:/Monitoreo de red/DataWarehouse/DataWarehouse.db'  # Cambia la ruta según tu configuración
engine = create_engine(f'sqlite:///{database_path}')

# Especificar las columnas esperadas en la tabla
columnas = ['Área', 'IP', 'Port', 'Name', 'Status', 'Vlan', 'Duplex', 'Speed', 'Type']

# Función para detectar delimitador automáticamente
def detectar_delimitador(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)  # Leer una muestra del archivo
        dialect = pd.io.parsers.csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except Exception:
        return ','  # Si falla, usar coma como predeterminado

# Procesar y cargar cada archivo CSV
# Procesar y cargar cada archivo CSV
for archivo in archivos_csv:
    try:
        # Detectar el delimitador
        delimitador = detectar_delimitador(archivo)
        
        # Leer y procesar el archivo CSV en lotes
        for chunk in pd.read_csv(archivo, delimiter=delimitador, chunksize=10000, encoding='utf-8', names=columnas, header=0, on_bad_lines='skip'):
            
            # Filtrar los datos donde la columna 'Status' no sea nula
            chunk_filtrado = chunk[chunk['Status'].notna()]
            
            # Validar si después del filtrado quedan datos
            if chunk_filtrado.empty:
                logging.warning(f"No se encontraron registros con 'Status' no nulo en el archivo {archivo}. Omitiendo...")
                continue
            
            # Validar las columnas del DataFrame
            if set(chunk_filtrado.columns) != set(columnas):
                logging.warning(f"El archivo {archivo} no tiene las columnas esperadas. Omitiendo...")
                continue
            
            # Cargar los datos filtrados al Data Warehouse
            with engine.begin() as connection:
                chunk_filtrado.to_sql('Inter_puertos', connection, if_exists='append', index=False)
            
            logging.info(f"Se procesaron {len(chunk_filtrado)} registros con 'Status' no nulo del archivo {archivo}.")
        
    except pd.errors.ParserError as e:
        logging.error(f"Error de análisis en el archivo {archivo}. Detalles: {e}")
    except Exception as e:
        logging.error(f"Error al procesar el archivo {archivo}. Detalles: {e}")


# Verificar la cantidad total de registros cargados
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM Inter_puertos;"))
        total_registros = result.fetchone()[0]
        logging.info(f"Total de registros en la tabla 'Inter_puertos': {total_registros}")
        print(f"Total de registros en la tabla 'Inter_puertos': {total_registros}")
except Exception as e:
    logging.error(f"Error al verificar la cantidad total de registros. Detalles: {e}")
    print(f"Error al verificar la cantidad total de registros. Detalles: {e}")
