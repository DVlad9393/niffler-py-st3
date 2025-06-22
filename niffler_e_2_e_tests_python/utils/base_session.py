import httpx

class BaseSession:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.Client(base_url=self.base_url)

    def get(self, url: str, **kwargs):
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.client.post(url, **kwargs)

    def patch(self, url: str, **kwargs):
        return self.client.patch(url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.client.delete(url, **kwargs)

    def close(self):
        self.client.close()