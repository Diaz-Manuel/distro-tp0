import signal
import logging
from lib.serde import Message, AckPayload, WinnerPayload
from lib.network import OTPSocket
from .utils import Bet, store_bets, load_bets, has_won

def signal_handler(signalnum, stack_frame):
    raise StopIteration


class Server:
    def __init__(self, port, listen_backlog, agency_count):
        # Initialize server socket
        self._server_socket = OTPSocket()
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.agency_ready = [False] * agency_count
        self.waiting_agencies = []


    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        signal.signal(signal.SIGTERM, signal_handler)
        try:
            # UNBLOCK signals now that exceptions can be caught and handled
            signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})
            while True:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
        except StopIteration:
            self._server_socket.close()
            logging.debug(f"action: close_server_socket | result: success")
            for (_, socket) in self.waiting_agencies:
                socket.close()
                logging.debug(f"action: close_client_socket | result: success")


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = client_sock.recv()
            addr = client_sock.getpeername()
            if msg.kind == Message.MSG_BET:
                self.handle_bet_message(client_sock, msg)
                client_sock.close()
                logging.debug(f"action: close_client_socket | result: success")
            elif msg.kind == Message.MSG_FIN:
                self.handle_fin_message(msg)
                client_sock.close()
                logging.debug(f"action: close_client_socket | result: success")
            elif msg.kind == Message.MSG_QUERY:
                self.handle_query_message(client_sock, msg)
            else:
                raise NotImplementedError(f'Received unsupported message of kind {msg.kind}')
            logging.debug(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")


    def handle_bet_message(self, socket, msg):
        bets = [Bet(**msg.data) for msg in msg.data]
        store_bets(bets)
        msg = []
        for bet in bets:
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
            payload = AckPayload(bet.document, bet.number)
            msg.append(payload)
        batch_msg = Message(Message.MSG_ACK, msg)
        socket.send(batch_msg)


    def handle_fin_message(self, msg):
        agency = int(msg.data[0].data['agency'])
        self.agency_ready[agency - 1] = True
        if all(self.agency_ready):
            logging.info(f'action: sorteo | result: success')


    def handle_query_message(self, new_socket, msg):
        agency = int(msg.data[0].data['agency'])
        self.waiting_agencies.append((agency, new_socket))
        if all(self.agency_ready):
            winners = self.get_winners()
            for (agency, socket) in self.waiting_agencies:
                # send winners to all waiting agencies
                msg = []
                for winner in winners.get(agency, []):
                    payload = WinnerPayload(winner)
                    msg.append(payload)
                batch_msg = Message(Message.MSG_WINNER, msg)
                socket.send(batch_msg)
                socket.close()
                logging.debug(f"action: close_client_socket | result: success")
            self.waiting_agencies = []


    def get_winners(self, winners_by_agency={}):
        if not winners_by_agency:
            for bet in load_bets():
                if has_won(bet):
                    winners_by_agency[bet.agency] = winners_by_agency.get(bet.agency, [])
                    winners_by_agency[bet.agency].append(bet.document)
        return winners_by_agency

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        # TODO:
        # This function creates a socket that will not be closed if a signal handlers
        # raises an exception at just the wrong time. This can't be avoided even with the use
        # of context managers, the safe way to manage signals with sockets is with the use of selectors.
        # More details in https://docs.python.org/3/library/signal.html#note-on-signal-handlers-and-exceptions

        # Connection arrived
        logging.debug('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.debug(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
