# tappay implement
import requests

from payment_gateway_sdk.core.request import Request


class TappayRequest(Request):
    tappay_base_url = "https://sandbox.tappaysdk.com/tpc"

    def __init__(self, **kwargs):
        super(TappayRequest, self).__init__(**kwargs)

    def send_request(self):
        # 送資訊到tappay伺服器
        url = TappayRequest.tappay_base_url + self.url
        requests.post(url=url, headers=self.headers, data=self.data, timeout=300).json()
