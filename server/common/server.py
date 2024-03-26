import signal
import logging
import multiprocessing as mp
from lib.network import MINTSocket
from lib.serde import Message, AckPayload, WinnerPayload
from .utils import Bet, store_bets, load_bets, has_won

def signal_handler(signalnum, stack_frame):
    raise StopIteration


class Server:
    def __init__(self, port, listen_backlog, agency_count):
        # Initialize server socket
        self.server_socket = MINTSocket()
        self.server_socket.bind(('', port))
        self.server_socket.listen(listen_backlog)
        self.betsfile_lock = mp.Lock()
        # Use a semaphore to track the amount of agencies that are ready for the lottery
        self.agency_tracker = mp.Semaphore(agency_count - 1)
        # Use an event to notify all agencies when the lottery takes place
        self.lottery_ready = mp.Event()

    def run(self):
        """
        Multiprocess Server loop

        Server that accept a new connections and establishes a
        communication with a client. The established connection is dispatched
        for a new process to handle the messages.
        """
        signal.signal(signal.SIGTERM, signal_handler)
        try:
            # UNBLOCK signals now that exceptions can be caught and handled
            signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})
            while True:
                client_sock = self.accept_new_connection()
                dispatch_connection(client_sock, self.agency_tracker, self.lottery_ready, self.betsfile_lock)
        except StopIteration:
            self.server_socket.close()
            logging.debug(f"action: close_server_socket | result: success")
            for (_, socket) in self.waiting_agencies:
                socket.close()
                logging.debug(f"action: close_client_socket | result: success")
        finally:
            for process in mp.active_children():
                process.terminate()
                process.join()

    def accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        # This function creates a socket that will not be closed if a signal handlers
        # raises an exception at just the wrong time. This can't be avoided even with the use
        # of context managers, the safe way to manage signals with sockets is with the use of selectors.
        # More details in https://docs.python.org/3/library/signal.html#note-on-signal-handlers-and-exceptions
        # TODO: Use selectors and events instead of exceptions for signal handling

        # Connection arrived
        logging.debug('action: accept_connections | result: in_progress')
        socket, addr = self.server_socket.accept()
        logging.debug(f'action: accept_connections | result: success | ip: {addr[0]}')
        return socket


class ClientHandler:
    def __init__(self, socket: MINTSocket, agency_tracker: mp.Semaphore, lottery_ready: mp.Event, betsfile_lock: mp.Lock):
        # Initialize server socket
        self.socket = socket
        self.agency_tracker = agency_tracker
        self.lottery_ready = lottery_ready
        self.betsfile_lock = betsfile_lock

    def run(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = self.socket.recv()
            addr = self.socket.getpeername()
            if msg.kind == Message.MSG_BET:
                self.handle_bet_message(msg)
                self.socket.close()
                logging.debug(f"action: close_client_socket | result: success")
            elif msg.kind == Message.MSG_FIN:
                self.handle_fin_message(msg)
                self.socket.close()
                logging.debug(f"action: close_client_socket | result: success")
            elif msg.kind == Message.MSG_QUERY:
                self.handle_query_message(msg)
            else:
                raise NotImplementedError(f'Received unsupported message of kind {msg.kind}')
            logging.debug(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
            return e

    def handle_bet_message(self, msg):
        """
        Read new bets from client, store them and notify the client once all of them have been stored
        """
        bets = [Bet(**msg.data) for msg in msg.data]
        with self.betsfile_lock:
            store_bets(bets)
        msg = []
        for bet in bets:
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
            payload = AckPayload(bet.document, bet.number)
            msg.append(payload)
        batch_msg = Message(Message.MSG_ACK, msg)
        self.socket.send(batch_msg)

    def handle_fin_message(self, _):
        """
        Receive FIN message from client indicating no more bets will be sent by the client.
        If this is the last agency no notify, run the lottery which would allow any agency to query the winners.
        """
        # If the Semaphore blocks, it means that all other agencies have already sent their FIN messages.
        # Since this was the last agency, run the lottery and notify blocked queries by setting an Event
        all_agencies_finished = not self.agency_tracker.acquire(block=False)
        if all_agencies_finished:
            logging.info(f'action: sorteo | result: success')
            self.lottery_ready.set()

    def handle_query_message(self, msg):
        """
        Receives QUERY message from an agency asking about the lottery winners.
        The query will remain unanswered until all agencies have finished betting.
        """
        self.lottery_ready.wait()
        agency = int(msg.data[0].data['agency'])
        winners = self.get_winners(agency)
        msg = [WinnerPayload(winner) for winner in winners]
        batch_msg = Message(Message.MSG_WINNER, msg)
        self.socket.send(batch_msg)
        self.socket.close()
        logging.debug(f"action: close_client_socket | result: success")

    def get_winners(self, agency):
        with self.betsfile_lock:
            return [bet.document for bet in load_bets() if has_won(bet) and bet.agency == agency]


def dispatch_connection(client_sock: MINTSocket, agency_tracker: mp.Semaphore, lottery_ready: mp.Event, betsfile_lock: mp.Lock):
    """
    Start a new process to handle a client connection.
    """
    handler = ClientHandler(client_sock, agency_tracker, lottery_ready, betsfile_lock)
    mp.Process(target=ClientHandler.run, args=[handler]).start()
