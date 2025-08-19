import os

from binance import Client
from jinja2 import Environment, FileSystemLoader

from cryptobot.components.settings import SettingsComponent
from cryptobot.components.telegram_http_transport import TelegramHttpTransportComponent
from cryptobot.config import get_config
from cryptobot.components import ServiceComponent, dispatch, parse_args, TelegramComponent, BinanceGateway, \
    BinanceClientAdapter, BinanceApiAdapter
from cryptobot.helpers import get_project_root, init_settings_component
from cryptobot.ports import binance_gateway
from cryptobot.ports.binance_api_adapter import BinanceApiAdapterPort
from cryptobot.ports.binance_client_adapter import BinanceClientAdapterPort
from cryptobot.ports.binance_gateway import BinanceGatewayPort
from cryptobot.views.view import View
from cryptobot.views import view_helper

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from peewee import MySQLDatabase
from cryptobot.models import database_proxy


def main():
    config: dict = get_config()

    args = parse_args("Cryptobot CLI")

    args.command = args.command.lower()

    environment = Environment(
        loader = FileSystemLoader(
            get_project_root() + os.sep + config["view"]["views_folder"]
        )
    )

    environment.globals.update(view_helper.get_globals())

    default_vars = {}

    db = MySQLDatabase(
        config["db"]["name"], # database name
        user = config["db"]["user"], # database username
        password = config["db"]["pass"], # database password
        host = config["db"]["host"],  # database host
        port = config["db"]["port"]  # database port
    )
    database_proxy.initialize(db)
    if not db.connect():
        print(f'ERROR: Cannot connect to database {config["db"]["host"]}')

    view = View(environment, default_vars)

    settings_component = SettingsComponent.create(db)

    telegram_component = TelegramComponent.create(config["telegram"], TelegramHttpTransportComponent())

    binance_client: Client = Client(config['binance']['api']['key'], config['binance']['api']['secret'])
    binance_client_adapter: BinanceClientAdapterPort = BinanceClientAdapter.create(binance_client=binance_client)

    binance_api_adapter: BinanceApiAdapterPort = BinanceApiAdapter.create(
        base_url=config['binance']['api']['base_url'],
        binance_api_key=config['binance']['api']['key'],
        binance_api_secret=config['binance']['api']['secret'],
    )

    binance_gateway: BinanceGatewayPort = BinanceGateway.create(
        binance_client_adapter=binance_client_adapter,
        binance_api_adapter=binance_api_adapter,
    )

    di = { # fuck that Python...
        'config': config,
        'view': view,
        'plt': plt,
        'db': db,
        'service_component': ServiceComponent.create(
            db=db,
            view=view,
            telegram_component=telegram_component,
            binance_gateway=binance_gateway,
        ),
        'settings_component': settings_component,
    }

    init_settings_component(di['settings_component'])

    # commands dispatching
    err, command = dispatch(di, args)
    if err is not None:
        print(err)

    if not command.execute():
        print("ERROR: Command '{}' failed.".format(args.command))


if __name__ == "__main__":
    main()