import logging

class LoggerManager:
    def __init__(self, name="my_app", log_file=None, level=logging.INFO):
        """
        Initializes a global logger with an option to write to a file.
        """
        self._logger = logging.getLogger(name) 
        self._logger.setLevel(level)
        if not self._logger.handlers:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)

    @property
    def logger(self):
        """Returns the configured logger"""
        return self._logger


log = LoggerManager(log_file="app.log", level=logging.DEBUG).logger