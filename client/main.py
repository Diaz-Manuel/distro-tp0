#!/usr/bin/env python3

import os
import signal
import logging
from common.client import Client
from configparser import ConfigParser


def initialize_config():
    """ Parse env variables or config file to find program config params

    Function that search and parse program configuration parameters in the
    program environment variables first and the in a config file. 
    If at least one of the config parameters is not found a KeyError exception 
    is thrown. If a parameter could not be parsed, a ValueError is thrown. 
    If parsing succeeded, the function returns a ConfigParser object 
    with config parameters
    """

    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    config.read("config.ini")

    config_params = {}
    try:
        server_address = os.getenv('CLI_SERVER_ADDRESS', config["DEFAULT"]["SERVER_ADDRESS"])
        # split using last colon to get port number, in case ipv6 is supported in the future
        port_idx = server_address.rfind(':')
        if port_idx < 0:
            raise ValueError("Key could not be parsed. Error: Server address doesn't specify a port. Aborting client".format(e))
        config_params["server_host"] = server_address[:port_idx]
        config_params["server_port"] = int(server_address[port_idx+1:])
        config_params["loop_lapse"] = int(os.getenv('CLI_LOOP_LAPSE_SECONDS', config["DEFAULT"]["LOOP_LAPSE_SECONDS"]))
        config_params["loop_period"] = int(os.getenv('CLI_LOOP_PERIOD_SECONDS', config["DEFAULT"]["LOOP_PERIOD_SECONDS"]))
        config_params["log_level"] = os.getenv('CLI_LOG_LEVEL', config["DEFAULT"]["LOG_LEVEL"])
        config_params["client_id"] = os.getenv('CLI_ID', config["DEFAULT"]["CLI_ID"])

        config_params["bet_firstname"] = os.environ['NOMBRE']
        config_params["bet_lastname"] = os.environ['APELLIDO']
        config_params["bet_id"] = os.environ['DOCUMENTO']
        config_params["bet_dob"] = os.environ['NACIMIENTO']
        config_params["bet_number"] = os.environ['NUMERO']
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting client".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting client".format(e))

    return config_params


def main():
    config_params = initialize_config()
    server_host = config_params["server_host"]
    server_port = config_params["server_port"]
    client_id = config_params["client_id"]
    loop_lapse = config_params["loop_lapse"]
    loop_period = config_params["loop_period"]
    log_level = config_params["log_level"]

    initialize_log(log_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | client_id: {client_id}"
        f" | server_address: {server_host}:{server_port} | loop_lapse: {loop_lapse}"
        f" | loop_period: {loop_period} | log_level: {log_level}"
    )

    # BLOCK SIGTERM signals to process them later.
    # This prevents the process from being interrupted by a signal before
    # it enters the try/except block that would free the resources that
    # have to be allocated before the block
    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
    del config_params['log_level']
    client = Client(config_params)
    client.run()


def initialize_log(log_level):
    """
    Python custom logging initialization

    Current timestamp is added to be able to identify in docker
    compose logs the date when the log has arrived
    """
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=log_level,
        datefmt='%Y-%m-%d %H:%M:%S',
    )


if __name__ == "__main__":
    main()
