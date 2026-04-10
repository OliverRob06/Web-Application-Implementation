from models import APIkey

for k in APIkey.query.all():
    print(k.key, k.role, k.request_count)