from decimal import Decimal
from typing import Optional
from cryptobot.components.settings import SettingsComponent

_settings_component: Optional[SettingsComponent] = None

def init_settings_component(component: SettingsComponent) -> None:
    global _settings_component
    if _settings_component is None:
        _settings_component = component # instance of SettingsComponent IS THE SAME AS IN di['settings_component']

def many(only_keys = None): # get all settings as dict
    if _settings_component is None:
        raise RuntimeError("settings not initialized")
    return _settings_component.get_many(only_keys)

def sg(key: str, default=None):
    if _settings_component is None:
        raise RuntimeError("settings not initialized")
    return _settings_component.get(key, default)

def ss(key: str, value: int|float|Decimal|bool|str):
    if _settings_component is None:
        raise RuntimeError("settings not initialized")
    return _settings_component.set(key, value)
