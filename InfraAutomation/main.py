import os
import sys
import importlib
from getpass import getpass
from datetime import datetime
from core.inventory import load_inventory
from core.logger import setup_logger

LOG_DIR = "logs"

def select_option(options, prompt):
    """
    Permite seleccionar una opción de una lista mostrada por pantalla.
    Valida que la opción sea un número válido dentro del rango.
    """
    for i, option in enumerate(options, 1):
        print(f"{i}) {option}")
    while True:
        try:
            choice = int(input(prompt))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print(f"Elija un número entre 1 y {len(options)}")
        except ValueError:
            print("Entrada inválida, intente nuevamente.")

def load_modules():
    """
    Detecta dinámicamente los módulos disponibles en la carpeta 'modules'.
    Solo considera carpetas que tengan un archivo '__init__.py' (paquetes Python).
    """
    modules_path = os.path.join(os.path.dirname(__file__), "modules")
    modules = []
    if not os.path.exists(modules_path):
        print(f"Error: No se encontró la carpeta de módulos en {modules_path}")
        return modules

    for item in os.listdir(modules_path):
        full_path = os.path.join(modules_path, item)
        if os.path.isdir(full_path) and "__init__.py" in os.listdir(full_path):
            modules.append(item)
    return modules

def load_module_scripts(module_name):
    """
    Dado un módulo (carpeta), devuelve una lista de scripts Python disponibles
    (sin incluir __init__.py) para que el usuario elija qué acción ejecutar.
    """
    module_path = os.path.join(os.path.dirname(__file__), "modules", module_name)
    scripts = []
    if not os.path.exists(module_path):
        return scripts
    for f in os.listdir(module_path):
        if f.endswith(".py") and f != "__init__.py":
            scripts.append(f[:-3])
    return scripts

def main():
    # Crear carpeta para logs si no existe
    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"execution_{now}.log")
    
    # Configurar logger para registrar la ejecución
    logger = setup_logger(log_file)

    # Cargar inventario de servidores desde archivo ini
    inventory = load_inventory("inventory/servers.txt")
    
    # Detectar módulos disponibles para ejecutar
    modules = load_modules()
    if not modules:
        print("No se encontraron módulos disponibles.")
        sys.exit(1)

    print("Selecciona módulo:")
    module_name = select_option(modules, "Opción módulo: ")

    # Detectar scripts disponibles dentro del módulo seleccionado
    scripts = load_module_scripts(module_name)
    if not scripts:
        print(f"No se encontraron scripts Python en el módulo '{module_name}'.")
        sys.exit(1)

    print(f"Selecciona acción dentro del módulo '{module_name}':")
    script_name = select_option(scripts, "Opción acción: ")

    # Cargar el script seleccionado dinámicamente
    try:
        module = importlib.import_module(f"modules.{module_name}.{script_name}")
    except ImportError as e:
        print(f"No se pudo cargar el script '{script_name}' del módulo '{module_name}'. Error: {e}")
        sys.exit(1)

    # Validar que el módulo tenga la función execute
    if not hasattr(module, "execute"):
        print(f"El script '{script_name}' del módulo '{module_name}' no tiene función 'execute'.")
        sys.exit(1)

    # Mostrar servicios disponibles según inventario
    print("\nSelecciona servicio:")
    services = list(inventory.keys())
    service_name = select_option(services, "Opción servicio: ")

    # Pedir credenciales SSH
    user = input("Usuario SSH: ")
    password = getpass("Password SSH: ")

    servers = inventory[service_name]

    logger.info(f"Ejecutando script '{script_name}' del módulo '{module_name}' en servicio '{service_name}'")
    logger.info(f"Servidores: {servers}")

    success = 0
    failure = 0

    # Ejecutar script en cada host del servicio
    for host in servers:
        logger.info(f"Iniciando ejecución en {host}")
        try:
            output = module.execute(host, user, password)
            print(f"✅ {host} - {script_name} ejecutado correctamente")
            print(f"Salida:\n{output}")
            logger.info(f"✅ {host} - éxito")
            success += 1
        except Exception as e:
            print(f"❌ {host} - Error: {e}")
            logger.error(f"❌ {host} - Error: {e}")
            failure += 1

    # Resultado final
    print(f"\n📊 Resultado final: {success} OK / {failure} FALLIDOS")
    logger.info(f"Resultado final: {success} OK / {failure} FALLIDOS")

if __name__ == "__main__":
    main()
