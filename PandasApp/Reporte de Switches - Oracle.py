import pandas as pd
import os
import chardet
from sqlalchemy import create_engine, text

# Configuración de conexión a Oracle
oracle_host = 'TPCDB.THEPANAMACLINIC.LOCAL'
oracle_port = '1521'
oracle_sid = 'TPCMVSML'
oracle_user = 'TPCAPPS'
oracle_password = 'tpcapps2019'

# Crear engine SQLAlchemy
oracle_connection_string = f'oracle+cx_oracle://{oracle_user}:{oracle_password}@{oracle_host}:{oracle_port}/{oracle_sid}'
engine = create_engine(oracle_connection_string)

# Ruta de los archivos CSV
folder_path = "Z:/Monitoreo de red/Reporte de Switches"

def detectar_codificacion(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000)
    resultado = chardet.detect(rawdata)
    return resultado['encoding']

# Leer y consolidar archivos CSV
def leer_archivos_csv(folder_path):
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.csv')]
    dataframes = []
    for file in all_files:
        try:
            encoding = detectar_codificacion(file)
            df = pd.read_csv(file, encoding=encoding, delimiter=',', on_bad_lines='skip')
            dataframes.append(df)
        except Exception as e:
            print(f"Error al leer {file}: {e}")
    return pd.concat(dataframes, ignore_index=True) if dataframes else None

# Crear tabla si no existe
def crear_tabla(engine):
    create_table_query = """
    CREATE TABLE REPORTE_SWITCHES (
        ip_del_switch VARCHAR2(100),
        area VARCHAR2(100),
        evento VARCHAR2(255),
        puerto VARCHAR2(100),
        detalles CLOB,
        fecha DATE
    )
    """
    with engine.connect() as connection:
        result = connection.execute(text("SELECT table_name FROM all_tables WHERE table_name = 'REPORTE_SWITCHES'"))
        if not result.fetchone():
            connection.execute(text(create_table_query))
            print("Tabla 'REPORTE_SWITCHES' creada exitosamente.")

# Cargar datos a Oracle
def cargar_datos_oracle(df, engine, table_name="REPORTE_SWITCHES"):
    try:
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Datos cargados en la tabla '{table_name}'.")
    except Exception as e:
        print(f"Error al cargar datos en Oracle: {e}")

# Validar carga de datos
def validar_carga_datos(engine, table_name="REPORTE_SWITCHES"):
    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        print(f"Total de registros en '{table_name}': {result.scalar()}")

# Main
if __name__ == "__main__":
    df = leer_archivos_csv(folder_path)
    if df is not None:
        df.rename(columns=lambda x: x.strip().lower().replace(' ', '_'), inplace=True)
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df.dropna(inplace=True)
        crear_tabla(engine)
        cargar_datos_oracle(df, engine)
        validar_carga_datos(engine)
    else:
        print("No se encontraron datos para cargar.")
