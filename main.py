import argparse

from config import get_config

from components import ServiceComponent, dispatch, parse_args


def main():
    config: dict = get_config()

    args = parse_args("Cryptobot CLI")

    args.command = args.command.lower()

    di = { # fuck that Python...
        'config': config,
        'service_component': ServiceComponent.create(config),
    }

    # commands dispatching
    err, command = dispatch(di, args)
    if err is not None:
        print(err)

    if not command.execute():
        print("ERROR: Command '{}' failed.".format(args.command))


if __name__ == "__main__":
    main()