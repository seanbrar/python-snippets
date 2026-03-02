import base64

encoded_str = "MCECDwCb6SVwNccXxsQULOnHfAIOOZL2jHOouuNUJJZss6w="
decoded_bytes = base64.b64decode(encoded_str)

# Parse ASN.1 structure
if decoded_bytes[0] != 0x30:
    raise ValueError("Expected SEQUENCE")
seq_length = decoded_bytes[1]

index = 2  # Start after SEQUENCE tag and length

# Parse 'r' INTEGER
if decoded_bytes[index] != 0x02:
    raise ValueError("Expected INTEGER for 'r'")
r_length = decoded_bytes[index + 1]
r_start = index + 2
r_end = r_start + r_length
r_bytes = decoded_bytes[r_start:r_end]
index = r_end

# Parse 's' INTEGER
if decoded_bytes[index] != 0x02:
    raise ValueError("Expected INTEGER for 's'")
s_length = decoded_bytes[index + 1]
s_start = index + 2
s_end = s_start + s_length
s_bytes = decoded_bytes[s_start:s_end]

# Convert to integers
r_int = int.from_bytes(r_bytes, byteorder='big')
s_int = int.from_bytes(s_bytes, byteorder='big')

print("r (hex):", r_bytes.hex())
print("s (hex):", s_bytes.hex())
print("r (int):", r_int)
print("s (int):", s_int)
