from cryptobot.commands import AbstractCommand
from cryptobot.components import ServiceComponent
from cryptobot.helpers import many
from cryptobot.views.view import View


class ShowSettingsCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None

    def set_payload(self, chat_id: int):
        self._payload["chat_id"] = chat_id
        self._initialized = True
        return self

    def set_deps(self, service_component: ServiceComponent, view: View):
        self._service_component = service_component
        self._view = view
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False
        settings_dict = many()
        message = self._view.render('telegram/settings/settings_list.j2', {
            'settings_dict': settings_dict,
        })
        self._service_component.send_telegram_message(self._payload["chat_id"], message)
        return True