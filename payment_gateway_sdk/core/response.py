from abc import ABC, abstractmethod


class ResponseSerializer(ABC):
    @abstractmethod
    def serialize(self, raw_response):
        """將原始回應序列化的抽象方法"""
        pass


class Response(ABC):
    def __init__(self, raw_response):
        self.raw_response = raw_response

    @abstractmethod
    def process_response(self):
        """處理回應的抽象方法"""
        pass



