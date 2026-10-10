import random, datetime

URLS   = ["/api/users", "/api/login", "/health", "/api/orders", "/api/secret", "/static/app.js"]
IPS    = ["10.0.0.1", "10.0.0.2", "192.168.1.10", "203.0.113.5", "198.51.100.9"]
STATUS = [200]*70 + [201]*10 + [301]*5 + [400]*5 + [401]*3 + [404]*4 + [500]*2 + [503]*1

with open("sample.log", "w") as f:
    for i in range(500):
        dt  = datetime.datetime(2024, 3, 1, 0, 0, 0) + datetime.timedelta(seconds=i*10)
        ts  = dt.strftime("%d/%b/%Y:%H:%M:%S +0000")
        ip  = random.choice(IPS)
        url = random.choice(URLS)
        st  = random.choice(STATUS)
        sz  = random.randint(100, 5000)
        f.write(f'{ip} - - [{ts}] "GET {url} HTTP/1.1" {st} {sz} "-" "curl/7.68.0"\n')

print("sample.log created")
