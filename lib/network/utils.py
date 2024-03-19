
def uint32_from_le(byte_list):
    # parse from little endian
    return (byte_list[3] << 24) + (byte_list[2] << 16) \
         + (byte_list[1] << 8)  + byte_list[0]

def int_to_le(num):
    if not 0 <= num < 1<<32:
        raise ValueError
    mask = 255
    b1 = (num & (mask << 24)) >> 24
    b2 = (num & (mask << 16)) >> 16
    b3 = (num & (mask << 8))  >> 8
    b4 = num & mask
    return bytes([b4, b3, b2, b1])
