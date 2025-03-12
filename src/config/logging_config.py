import logging
import colorlog

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Eliminar todos los manejadores existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Crear un manejador de consola con colorlog
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Crear un formateador con colorlog y añadirlo al manejador
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(formatter)

    # Añadir el manejador al logger
    logger.addHandler(console_handler)