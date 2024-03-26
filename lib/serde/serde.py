from lib.utils import uint32_from_be, int_to_be
class Message:
    """
    Generic Batch Message where all of the items in a given batch share the same type.
    Decouples the network layer from the different kinds of Messages specific to the Lottery
    """
    MSG_ACK = 0
    MSG_BET = 1
    MSG_FIN = 2
    MSG_QUERY = 3
    MSG_WINNER = 4

    def __init__(self, msg_kind: int, data: list):
        self.kind = msg_kind
        self.data = data

    def serialize(self):
        accumulator = b''
        for msg in self.data:
            msg = msg.serialize() 
            accumulator += len(msg).to_bytes(1, 'big') + msg
        return self.kind.to_bytes(1, 'big') + accumulator

    @classmethod
    def deserialize(cls, stream: bytes):
        msg_kind = stream[0]
        if msg_kind == Message.MSG_ACK:
            msg_class = AckPayload
        elif msg_kind == Message.MSG_BET:
            msg_class = BetPayload
        elif msg_kind == Message.MSG_FIN:
            msg_class = FinPayload
        elif msg_kind == Message.MSG_QUERY:
            msg_class = QueryPayload
        elif msg_kind == Message.MSG_WINNER:
            msg_class = WinnerPayload
        else:
            raise ValueError('Unsupported message type')
        offset = 1
        items = []
        while offset < len(stream):
            item_size = uint32_from_be(stream[offset:offset+4])
            offset += 4
            deserialized = msg_class.deserialize(stream[offset:offset+item_size])
            items.append(deserialized)
            offset += item_size
        return cls(msg_kind, items)

    @classmethod
    def from_csv(cls, bets: list[bytes], agency):
        parsed_bets = [BetPayload.deserialize(bet, agency) for bet in bets]
        return cls(Message.MSG_BET, parsed_bets)


class BetPayload:
    """
    A kind of Message used by agencies to notify the server of a new bet
    """
    def __init__(self, agency: int, first_name: str, last_name: str, document: str, birthdate: str, number: str):
        data = {
            'agency': agency,
            'first_name': first_name,
            'last_name': last_name,
            'document': document,
            'birthdate': birthdate,
            'number': number
        }
        self.data = data

    def serialize(self):
        string = f"{self.data['agency']},{self.data['first_name']},{self.data['last_name']},{self.data['document']},{self.data['birthdate']},{self.data['number']}"
        return string.encode('utf-8')

    @classmethod
    def deserialize(cls, msg: bytes, agency=None):
        if agency:
            # agency passed as argument when reading from csv
            return cls(agency, *msg.decode('utf-8').split(','))
        else:
            # when not reading from csv, agency is sent as part of the message
            return cls(*msg.decode('utf-8').split(','))


class AckPayload:
    """
    A kind of Message used by servers to notify agencies that a bet has saved
    """
    def __init__(self, document: str, number: str):
        data = {
            'document': document,
            'number': number
        }
        self.data = data

    def serialize(self):
        string = f"{self.data['document']},{self.data['number']}"
        return string.encode('utf-8')

    @classmethod
    def deserialize(cls, msg: bytes):
        return cls(*msg.decode('utf-8').split(','))


class FinPayload:
    """
    A kind of Message used by agencies to notify the server that the agency won't make any more bets
    """
    def __init__(self, agency: str):
        data = {
            'agency': agency
        }
        self.data = data

    def serialize(self):
        string = self.data['agency']
        return string.encode('utf-8')

    @classmethod
    def deserialize(cls, msg: bytes):
        return cls(msg.decode('utf-8'))


class QueryPayload:
    """
    A kind of Message used by agencies to query the server for the winners of the lottery
    """
    def __init__(self, agency: str):
        data = {
            'agency': agency
        }
        self.data = data

    def serialize(self):
        string = self.data['agency']
        return string.encode('utf-8')

    @classmethod
    def deserialize(cls, msg: bytes):
        return cls(msg.decode('utf-8'))


class WinnerPayload:
    """
    A kind of Message used by the server to notify the agencies of their winning bets
    """
    def __init__(self, document: str):
        data = {
            'document': document
        }
        self.data = data

    def serialize(self):
        string = self.data['document']
        return string.encode('utf-8')

    @classmethod
    def deserialize(cls, msg: bytes):
        return cls(msg.decode('utf-8'))
