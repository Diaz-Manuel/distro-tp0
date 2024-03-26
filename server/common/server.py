import signal
import logging
from lib.serde import Message
from lib.network import OTPSocket
from .utils import Bet, store_bets, load_bets, has_won


def signal_handler(signalnum, stack_frame):
    raise StopIteration


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = OTPSocket()
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)


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


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = client_sock.recv()
            addr = client_sock.getpeername()
            logging.debug(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            bet = Bet(msg.data['agency'], msg.data['firstname'], msg.data['lastname'], msg.data['id'], msg.data['dob'], msg.data['number'])
            store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {msg.data['id']} | numero: {msg.data['number']}')
            ack_msg = Message.confirmation(msg.id, msg.data['id'], msg.data['number'])
            client_sock.send(ack_msg)
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()
            logging.debug(f"action: close_client_socket | result: success")


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
