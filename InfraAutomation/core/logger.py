import logging

def setup_logger(log_file):
    """
    Configura un logger que escribe en archivo y consola.
    Niveles:
    - DEBUG en archivo
    - INFO en consola para no saturar
    """
    logger = logging.getLogger("InfraAutomation")

    # Evita agregar múltiples handlers si se llama más de una vez
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)  # Captura todos los niveles

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Archivo log
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        # Consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
