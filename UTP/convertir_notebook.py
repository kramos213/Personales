import json

def json_a_notebook(json_file, output_file):
    """
    Convierte un archivo JSON con la estructura de un notebook
    en un archivo Jupyter (.ipynb).
    
    Parámetros:
        json_file (str): Ruta al archivo JSON de entrada.
        output_file (str): Ruta al archivo .ipynb de salida.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        notebook_json = json.load(f)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(notebook_json, f, ensure_ascii=False, indent=2)

    print(f"✅ Notebook creado: {output_file}")


# Ejemplo de uso
if __name__ == "__main__":
    # Archivo JSON de entrada (con la estructura del notebook)
    archivo_json = "/Users/kevinramos/Documents/Git File/Personales/UTP/TOP-II.1/JSON/Actividad-01.json"
    
    # Archivo Jupyter de salida
    archivo_ipynb = "/Users/kevinramos/Documents/Git File/Personales/UTP/TOP-II.1/IPYNB/Actividad-01.ipynb"
    
    json_a_notebook(archivo_json, archivo_ipynb)
