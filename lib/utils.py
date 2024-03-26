
def uint32_from_be(byte_list):
    """
    Convert an array of bytes to UINT32 using big endian
    """
    return (byte_list[0] << 24) + (byte_list[1] << 16) \
         + (byte_list[2] << 8)  + byte_list[3]

def int_to_be(num):
    """
    Convert UINT32 to an array of bytes using big endian
    """
    if not 0 <= num < 1<<32:
        raise ValueError
    mask = 255
    b1 = (num & (mask << 24)) >> 24
    b2 = (num & (mask << 16)) >> 16
    b3 = (num & (mask << 8))  >> 8
    b4 = num & mask
    return bytes([b1, b2, b3, b4])
