import hashlib
TapoEmailVictim=b"fortunato.moretti123@gmail.com"
OWNER = hashlib.md5(TapoEmailVictim).hexdigest().upper()
print(OWNER)





