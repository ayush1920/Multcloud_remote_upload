from Crypto.Cipher import AES
from binascii import unhexlify
from base64 import b64encode,b64decode
from pkcs7 import PKCS7Encoder
import json

# change the enc string with response string
enc = "E546EBB1FEE06C7F14AF0E6AACC642E70957C6D6C5A4E9482811DFBA6DA585885CF27AA15F9557D8B41E5914611A81ED"
cipher = AES.new( b64decode('Ns1F8bpJ1LJcHvvcH2sqFA=='), AES.MODE_ECB)
p = cipher.decrypt(unhexlify(enc))
m = PKCS7Encoder()
p = json.loads(m.decode(p).decode("utf-8"))
print(p)
