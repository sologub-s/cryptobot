import os

from jinja2 import Environment, FileSystemLoader

from config import get_config
from components import ServiceComponent, dispatch, parse_args
from helpers import get_project_root
from views.view import View
from views import view_helper

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from peewee import MySQLDatabase
from models import database_proxy


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

    di = { # fuck that Python...
        'config': config,
        'view': view,
        'plt': plt,
        'db': db,
        'service_component': ServiceComponent.create(config, db, view),
    }

    # commands dispatching
    err, command = dispatch(di, args)
    if err is not None:
        print(err)

    if not command.execute():
        print("ERROR: Command '{}' failed.".format(args.command))


if __name__ == "__main__":
    main()