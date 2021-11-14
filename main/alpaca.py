
import requests
import json


class Alpaca:
    def __init__(self, API_KEY, API_SECRET, BASE_URL):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.BASE_URL = BASE_URL
        self.headers = {
            "APCA-API-KEY-ID": self.API_KEY,
            "APCA-API-SECRET-KEY": self.API_SECRET,
            "Content-Type": "application/json"
        }

    def submit_order(self,
                     symbol: str,
                     quantity: int,
                     side: str,
                     order_type: str,
                     time_in_force: str,
                     limit_price: str = None,
                     stop_price: str = None,
                     client_order_id: str = None,
                     extended_hours: bool = None,
                     order_class: str = None,
                     take_profit: dict = None,
                     stop_loss: dict = None,
                     trail_price: str = None,
                     trail_percent: str = None):

        url = self.BASE_URL + "/v2/orders"
        params = {
            'symbol':        symbol,
            'qty':           quantity,
            'side':          side.lower(),
            'type':          order_type.lower(),
            'time_in_force': "day"
        }
        if take_profit is not None:
            if 'limit_price' in take_profit:
                take_profit['limit_price'] = float(take_profit['limit_price'])
            params['take_profit'] = take_profit
        if stop_loss is not None:
            if 'limit_price' in stop_loss:
                stop_loss['limit_price'] = float(stop_loss['limit_price'])
            if 'stop_price' in stop_loss:
                stop_loss['stop_price'] = float(stop_loss['stop_price'])
            params['stop_loss'] = stop_loss
        if client_order_id is not None:
            params['client_order_id'] = client_order_id
        if extended_hours is not None:
            params['extended_hours'] = extended_hours
        if order_class is not None:
            params['order_class'] = order_class

        if order_type.lower() == "market":
            res = requests.post(url, data=json.dumps(params), headers=self.headers).json()
            return res

        elif order_type.lower() == "limit":
            params['limit_price'] = limit_price
            res = requests.post(url, data=json.dumps(params), headers=self.headers).json()
            return res

        elif order_type.lower() == "stop":
            params['stop_price'] = stop_price
            res = requests.post(url, data=json.dumps(params), headers=self.headers).json()
            return res

        elif order_type.lower() == "stop_limit":
            params['limit_price'] = limit_price
            params['stop_price'] = stop_price
            res = requests.post(url, data=json.dumps(params), headers=self.headers).json()
            return res

        elif order_type.lower() == "trailing_stop":
            params['trail_price'] = trail_price
            params['trail_percent'] = trail_percent
            res = requests.post(url, data=json.dumps(params), headers=self.headers)
            return res

        else:
            res = {"error": "invalid order type. valid order types: 'market', 'limit', 'stop', 'stop_limit', 'trailing_stop'"}
            return res

    def list_orders(self,
                    status: str = None,
                    limit: int = None,
                    after: str = None,
                    until: str = None,
                    direction: str = None,
                    params=None,
                    nested: bool = None):
        if params is None:
            params = dict()
        if limit is not None:
            params['limit'] = limit
        if after is not None:
            params['after'] = after
        if until is not None:
            params['until'] = until
        if direction is not None:
            params['direction'] = direction
        if status is not None:
            params['status'] = status
        if nested is not None:
            params['nested'] = nested

        url = self.BASE_URL+"/v2/orders"

        res = requests.get(url, params, headers=self.headers).json()
        return res

    def cancel_order(self, order):
        order_id = order["id"]
        url = self.BASE_URL+f"/v2/orders/{order_id}"

        res = requests.delete(url, headers=self.headers)
        return res.status_code
