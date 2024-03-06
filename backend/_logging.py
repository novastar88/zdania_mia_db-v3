from loguru import logger
import sys
import utilities

config = utilities.config_reader()
logging_config = config["logging"]

file = {"sink": "logs\\log.log",
        "format": logging_config["format_file"], "level": logging_config["level_file"], "rotation": "1 day", "retention": "1 week"}
console = {"sink": sys.stderr, "format": logging_config["format_console"],
           "colorize": True, "level": logging_config["level_console"]}


logger.configure(handlers=[file, console])
