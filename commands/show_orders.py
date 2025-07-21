from commands import AbstractCommand
from components import ServiceComponent

class ShowOrdersCommand(AbstractCommand):

    def set_payload(self, chat_id: int):
        self._payload["chat_id"] = chat_id
        self._initialized = True
        return self

    def set_deps(self, service_component: ServiceComponent):
        self._service_component = service_component
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False
        self._service_component.show_orders(self._payload['chat_id'])
        return True