from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader

def format_time(timestamp: int, format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
    return datetime.fromtimestamp(timestamp).strftime(format_string)


class View:
    def __init__(
            self,
            environment: Environment,
            default_vars=None,
    ):
        super().__init__()
        if default_vars is None:
            default_vars = {}
        self._environment = environment
        self._default_vars = default_vars

    def set_default_vars(self, default_vars: dict):
        self._default_vars = default_vars

    def alter_default_vars(self, default_vars: dict):
        self.set_default_vars(self._default_vars | default_vars)

    def render(self, template: str, render_vars = None):
        if render_vars is None:
            render_vars = {}
        #template = self._environment.get_template(template + '.j2')
        template = self._environment.get_template(template)
        #print(f'Rendering template: \'{template}\'')
        return template.render(self._default_vars | render_vars)


