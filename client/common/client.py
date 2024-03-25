import time
import signal
import logging
from io import BufferedReader
from lib.serde import Message, FinPayload, QueryPayload
from lib.network import MINTSocket

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
        self.socket = MINTSocket()

    def run(self):
        """
        Client top level logic for handling exceptions, cleanup resources
        and querying winners once the message loop finishes
        """
        signal.signal(signal.SIGALRM, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        try:
            with open(f'agency.csv', 'rb') as betsfile:
                self.send_bets_to_server(BufferedReader(betsfile))
            self.get_lottery_winners()
        except (StopIteration, KeyboardInterrupt):
            # avoid Traceback if process was interrupted, quit silently
            pass
        finally:
            self.socket.close()
            logging.debug(f"action: close_socket | result: success | client_id: {self.id}")


    def send_bets_to_server(self, bets_reader):
        """
        Client message loop
        Send messages to the server until a time threshold is met
        """
        self.buffer = b''
        try:
            # UNBLOCK signals now that exceptions can be caught and handled
            signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})
            # set alarm to break out of the while loop
            signal.alarm(self.loop_lapse)
            while (bytes_read := bets_reader.read(self.batch_max_size - len(self.buffer))):
                self.buffer += bytes_read
                bets = [bet.rstrip() for bet in self.buffer.split(b'\n')]
                # assume that it didn't finish reading bets, the last item in the list is incomplete
                # the file is newline terminated so there's no need to consume the last element after the last iteration
                self.buffer = bets[-1]
                bets = bets[:-1]
                batch = Message.from_csv(bets, self.id)
                self.connect_to_server()
                self.send_message(batch)
                self.recv_ack_message(batch)
                self.socket.close()
                time.sleep(self.loop_period)
                if len(self.buffer) == self.batch_max_size:
                    raise ValueError('BATCH_MAX_SIZE is too small to read a single bet')
            # clear alarm to avoid interrupting process once the loop is complete
            signal.alarm(0)
        except TimeoutError:
            logging.warning(f"action: timeout_detected | result: success | client_id: {self.id}")
            logging.info(f"action: loop_finished | result: success | client_id: {self.id}")


    def get_lottery_winners(self):
        self.connect_to_server()
        self.send_message(Message(Message.MSG_FIN, [FinPayload(self.id)]))
        self.socket.close()
        # this could be done in a single connection, or even a single message
        # leaving it this way to match the TP0 requirements
        self.connect_to_server()
        self.send_message(Message(Message.MSG_QUERY, [QueryPayload(self.id)]))
        self.recv_winner_message()
        self.socket.close()


    def connect_to_server(self):
        try:
            self.socket = MINTSocket()
            self.socket.connect((self.server_host, self.server_port))
        except Exception as e:
            logging.error(f"action: connect | result: fail | client_id: {self.id} | error: {e}")
            raise e


    def recv_ack_message(self, batch):
        try:
            msg = self.socket.recv()
            if msg.kind == Message.MSG_ACK:
                for idx, ack_msg in enumerate(msg.data):
                    if ack_msg.data['document'] != batch.data[idx].data['document'] or ack_msg.data['number'] != batch.data[idx].data['number']:
                        raise ValueError(f'Ack {ack_msg.data} doesnt match bet {batch.data[idx].data} in batch position {idx}')
                    logging.info(f'action: apuesta_enviada | result: success | dni: {ack_msg.data["document"]:<8} | numero: {ack_msg.data["number"]}')
            else:
                raise NotImplementedError(f'Unexpected message kind "{msg.kind}"')
        except OSError as e:
            self.socket.close()
            logging.error(f"action: receive_message | result: fail | client_id: {self.id} | error: {e}")
            raise e


    def recv_winner_message(self):
        try:
            msg = self.socket.recv()
            if msg.kind == Message.MSG_WINNER:
                logging.warning(f'action: consulta_ganadores | result: success | cant_ganadores: {len(msg.data)}')
            else:
                raise NotImplementedError(f'Unexpected message kind "{msg.kind}"')
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

