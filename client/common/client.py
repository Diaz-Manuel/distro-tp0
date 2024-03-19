import time
import signal
import logging
from lib.serde import Message
from lib.network import OTPSocket


def signal_handler(signalnum, _stack_frame):
    if signalnum == signal.SIGALRM:
        raise TimeoutError
    elif signalnum == signal.SIGTERM:
        raise StopIteration


class Client:
    def __init__(self, config):
        # Initialize server socket
        self.server_host = config['server_host']
        self.server_port = config['server_port']
        self.loop_lapse = config['loop_lapse']
        self.loop_period = config['loop_period']
        self.id = config['client_id']
        self.socket = OTPSocket()
        self.bet = {
            'client_id': self.id,
            'firstname': config['bet_firstname'],
            'lastname': config['bet_lastname'],
            'id': config['bet_id'],
            'dob': config['bet_dob'],
            'number': config['bet_number'],
        }

    def run(self):
        """
        Client message loop

        Send messages to the server until a time threshold is met
        Autoincrement msg_id after each iteration to tell messages apart
        """
        signal.signal(signal.SIGALRM, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        msg_id = 1
        try:
            # UNBLOCK signals now that exceptions can be caught and handled
            signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})
            # set alarm to break out of the while loop
            signal.alarm(self.loop_lapse)
            while True:
                self.connect_to_server()
                self.send_message(msg_id)
                self.recv_message()
                msg_id += 1
                time.sleep(self.loop_period)
        except TimeoutError:
            self.socket.close()
            logging.info(f"action: timeout_detected | result: success | client_id: {self.id}")
            logging.info(f"action: loop_finished | result: success | client_id: {self.id}")
        except (StopIteration, KeyboardInterrupt):
            self.socket.close()
            logging.info(f"action: close_socket | result: success | client_id: {self.id}")
            logging.info(f"action: loop_finished | result: success | client_id: {self.id}")


    def connect_to_server(self):
        try:
            self.socket = OTPSocket()
            self.socket.connect((self.server_host, self.server_port))
        except Exception as e:
            logging.error(f"action: connect | result: fail | client_id: {self.id} | error: {e}")
            raise e


    def recv_message(self):
        try:
            msg = self.socket.recv()
            logging.info(f'action: receive_message | result: success | client_id: {self.id} | msg: {msg}')
        except OSError as e:
            self.socket.close()
            logging.error(f"action: receive_message | result: fail | client_id: {self.id} | error: {e}")
            raise e


    def send_message(self, msg_id):
        """
        Send message to the server

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        msg = Message.bet(msg_id, **self.bet)
        try:
            self.socket.send(msg)
        except OSError as e:
            self.socket.close()
            logging.error(f"action: send_message | result: fail | error: {e}")
            raise e

