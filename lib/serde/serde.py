MSG_ACK = 0
MSG_BET = 1

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
                return f'{{"type": MSG_ACK, "id": {self.id}, "DNI": {self.data["id"]}, "NUMERO": {self.data["number"]}}}'
        elif self.type == MSG_BET:
                return f'{{"type": MSG_DATA, "id": {self.id}, "agency": "{self.data["agency"]}", ' \
                    f'"NOMBRE": "{self.data["firstname"]}", "APELLIDO": "{self.data["lastname"]}", ' \
                    f'"DOCUMENTO": "{self.data["id"]}", "NACIMIENTO": "{self.data["dob"]}", "NUMERO": "{self.data["number"]}"}}'

    @classmethod
    def confirmation(cls, msg_id, gambler_id: str, number: str):
        kwargs = {
            'id': gambler_id,
            'number': number
        }
        return cls(MSG_ACK, msg_id, **kwargs)

    @classmethod
    def bet(cls, msg_id: int, agency: int, firstname: str, lastname: str, id: str, dob: str, number: str):
        kwargs = {
            'agency': agency,
            'firstname': firstname,
            'lastname': lastname,
            'id': id,
            'dob': dob,
            'number': number
        }
        return cls(MSG_BET, msg_id, **kwargs)

    def serialize(self):
        if self.type == MSG_ACK:
                string = f"{self.id},{self.data['id']},{self.data['number']}"
        elif self.type == MSG_BET:
                string = f"{self.id},{self.data['agency']},{self.data['firstname']},{self.data['lastname']},{self.data['id']},{self.data['dob']},{self.data['number']}"
        return bytes([self.type]) + string.encode('utf-8')

    @classmethod
    def deserialize(cls, msg: bytes):
        msg_type = msg[0]
        if msg_type == MSG_ACK:
            return cls.confirmation(*msg[1:].decode('utf-8').split(','))
        elif msg_type == MSG_BET:
            return cls.bet(*msg[1:].decode('utf-8').split(','))  
