import gevent.pool
from locust import FastHttpUser, task


class MyUser(FastHttpUser):
    @task
    def t(self):
        def concurrent_request(url):
            self.client.get(url)

        pool = gevent.pool.Pool()
        urls = ["/courses", "/BTC-USDT", "/ETH-USDT", "/XRP-USDT"]
        for url in urls:
            pool.spawn(concurrent_request, url)
        pool.join()
