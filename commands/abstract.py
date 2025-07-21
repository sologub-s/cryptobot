from abc import ABC

class AbstractCommand(ABC):

    def __init__(self):
        super().__init__()
        self._initialized = False
        self._service_component = None
        self._payload = {}

    def execute(self):
        pass