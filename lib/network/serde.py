
def serialize(obj):
    return "{}\n".format(obj).encode('utf-8')

def deserialize(byte_list):
    return bytes(byte_list).rstrip().decode('utf-8')
