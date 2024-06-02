from abc import ABC, abstractmethod


class Request(ABC):
    def __init__(self, url, headers=None, data=None):
        self.url = url
        self.headers = headers or {}
        self.data = data or {}

    @abstractmethod
    def send_request(self):
        """ request 抽象 """
        pass
