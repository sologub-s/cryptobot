from cryptobot.commands import AbstractCommand
from cryptobot.components import ServiceComponent
from cryptobot.views.view import View

import logging
from logging import info

logging.basicConfig(level=logging.INFO)

class CronNotifyWorkingCommand(AbstractCommand):

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
        
        info(f"CronNotifyWorking execution started")

        message = self._view.render('telegram/up_and_running.j2', {})
        self._service_component.send_telegram_message(self._payload["chat_id"], message, None, True)
        return True