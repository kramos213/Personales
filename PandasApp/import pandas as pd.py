import pandas as pd
import chardet

file_path = "Z:/Monitoreo de red/Prueba/ports_report_20241128124745.csv"

try:
    # Detecta la codificación automáticamente
    with open(file_path, 'rb') as f:
        encoding = chardet.detect(f.read())['encoding']

    # Lee el archivo con la codificación detectada y el encabezado correcto
    df = pd.read_csv(file_path, encoding=encoding, header=0)

    # Muestra las primeras filas del DataFrame para verificar los valores
    print("Primeras filas del DataFrame:")
    print(df.head())

    # Filtra las filas que contienen "Interface" en la columna 'Interface'
    df = df[df['Interface'] != 'Interface']

    # Muestra las primeras filas después del filtrado
    print("Después de filtrar las filas con 'Interface' en la columna 'Interface':")
    print(df.head())
    
    if df.empty:
        print("El DataFrame está vacío.")
    else:
        print(f"El DataFrame tiene {df.shape[0]} filas y {df.shape[1]} columnas.")
        
except UnicodeDecodeError as e:
    print(f"Error de decodificación: {e}")
except Exception as e:
    print(f"Ocurrió un error: {e}")
