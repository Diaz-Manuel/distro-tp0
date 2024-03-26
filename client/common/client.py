import time
import signal
import logging
from io import BufferedReader
from lib.serde import MessageBatch
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
        self.batch_max_size = config['batch_max_size']
        self.socket = OTPSocket()

    def run(self):
        """
        Client message loop

        Send messages to the server until a time threshold is met
        Autoincrement msg_id after each iteration to tell messages apart
        """
        signal.signal(signal.SIGALRM, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        try:
            # UNBLOCK signals now that exceptions can be caught and handled
            signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})
            # set alarm to break out of the while loop
            signal.alarm(self.loop_lapse)
            with open(f'agency.csv', 'rb') as betsfile:
                self.send_bets_to_server(BufferedReader(betsfile))
        except TimeoutError:
            logging.debug(f"action: timeout_detected | result: success | client_id: {self.id}")
            logging.info(f"action: loop_finished | result: success | client_id: {self.id}")
        except (StopIteration, KeyboardInterrupt):
            # avoid Traceback if process was interrupted, quit silently
            pass
        finally:
            self.socket.close()
            logging.debug(f"action: close_socket | result: success | client_id: {self.id}")


    def send_bets_to_server(self, bets_reader):
        self.buffer = b''
        while (bytes_read := bets_reader.read(self.batch_max_size - len(self.buffer))):
            self.buffer += bytes_read
            bets = self.buffer.split(b'\n')
            # assume that it didn't finish reading bets, the last item in the list is incomplete
            # the file is newline terminated so there's no need to consume the last element after the last iteration
            self.buffer = bets[-1]
            bets = bets[:-1]
            batch = MessageBatch.from_csv(bets, self.id)
            self.connect_to_server()
            self.send_message(batch)
            self.recv_message()
            time.sleep(self.loop_period)
            if len(self.buffer) == self.batch_max_size:
                raise ValueError('BATCH_MAX_SIZE is too small to read a single bet')


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
            for ack_msg in msg.data:
                logging.info(f'action: apuesta_enviada | result: success | dni: {ack_msg.data["document"]:<8} | numero: {ack_msg.data["number"]}')
        except OSError as e:
            self.socket.close()
            logging.error(f"action: receive_message | result: fail | client_id: {self.id} | error: {e}")
            raise e


    def send_message(self, msg):
        """
        Send message to the server

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            self.socket.send(msg)
        except OSError as e:
            self.socket.close()
            logging.error(f"action: send_message | result: fail | error: {e}")
            raise e
