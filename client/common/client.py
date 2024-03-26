import time
import socket
import signal
import logging


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
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


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
            logging.info(f"action: timeout_detected | result: success | client_id: {self.id}")
            logging.info(f"action: loop_finished | result: success | client_id: {self.id}")
        except (StopIteration, KeyboardInterrupt):
            self.die()
            logging.info(f"action: loop_finished | result: success | client_id: {self.id}")


    def die(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        logging.info(f"action: close_socket | result: success | client_id: {self.id}")


    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
        except Exception as e:
            logging.error(f"action: connect | result: fail | client_id: {self.id} | error: {e}")
            raise e


    def recv_message(self):
        try:
            # TODO: Modify the receive to avoid short-reads
            msg = self.socket.recv(1024).rstrip().decode('utf-8')
            logging.info(f'action: receive_message | result: success | client_id: {self.id} | msg: {msg}')
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | client_id: {self.id} | error: {e}")


    def send_message(self, msg_id):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        msg = f"[CLIENT {self.id}] Message N°{msg_id}\n"
        try:
            # TODO: Modify the send to avoid short-writes
            addr = self.socket.getpeername()
            self.socket.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error(f"action: send_message | result: fail | error: {e}")

