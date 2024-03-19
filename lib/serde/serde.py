MSG_ACK = 0
MSG_DATA = 1

class Message:
    # 0        8            ?                        ?
    # |--------|------------|------------------------|
    # |msg_type| str(msg_id), payload...             |
    # |--------|------------|------------------------|

    def __init__(self, msg_type, msg_id, **kwargs):
        self.id: int = msg_id
        self.type: int = msg_type
        self.data: dict = kwargs

    def __repr__(self):
        if self.type == MSG_ACK:
                return f'{{"type": MSG_ACK, "id": {self.id}}}'
        elif self.type == MSG_DATA:
                return f'{{"type": MSG_DATA, "id": {self.id}, "client_id": "{self.data["client_id"]}", ' \
                    f'"NOMBRE": "{self.data["firstname"]}", "APELLIDO": "{self.data["lastname"]}", ' \
                    f'"DOCUMENTO": "{self.data["id"]}", "NACIMIENTO": "{self.data["dob"]}", "NUMERO": "{self.data["number"]}"}}'

    @classmethod
    def ack(cls, msg_id):
        return cls(MSG_ACK, msg_id)

    @classmethod
    def bet(cls, msg_id: int, client_id: int, firstname: str, lastname: str, id: str, dob: str, number: str):
        kwargs = {
            'client_id': client_id,
            'firstname': firstname,
            'lastname': lastname,
            'id': id,
            'dob': dob,
            'number': number
        }
        return cls(MSG_DATA, msg_id, **kwargs)

    def serialize(self):
        if self.type == MSG_ACK:
                string = self.id
        elif self.type == MSG_DATA:
                string = f"{self.id},{self.data['client_id']},{self.data['firstname']},{self.data['lastname']},{self.data['id']},{self.data['dob']},{self.data['number']}"
        return bytes([self.type]) + string.encode('utf-8')

    @classmethod
    def deserialize(cls, msg: bytes):
        msg_type = msg[0]
        if msg_type == MSG_ACK:
            return cls.ack(msg[1:].decode('utf-8'))
        elif msg_type == MSG_DATA:
            return cls.bet(*msg[1:].decode('utf-8').split(','))  
