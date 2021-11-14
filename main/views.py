from django.views.generic import TemplateView
from django.template.response import TemplateResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django import template

import json
from accounts.models import BotSetting

from main.config import *
from main.alpaca import Alpaca
from main.coinbase import Coinbase
from binance.client import Client as Binance

from decimal import Decimal as D, ROUND_DOWN, ROUND_UP
import decimal


def index(request, template_name="main/index.html"):
    botSettings = BotSetting.objects.all()
    if botSettings.count() < 1:
        isStarted = 0
    else:
        botSetting = botSettings[0]
        if botSetting.started == "YES":
            isStarted = 1
        else:
            isStarted = 0
    return TemplateResponse(request, template_name, {"isStarted": isStarted})


def start_bot(request):
    botSettings = BotSetting.objects.all()
    try:
        botSetting = botSettings[0]
    except Exception as e:
        botSetting = BotSetting(
            user=request.user,
            started="YES"
            )
        botSetting.save()
        return redirect("/")

    botSetting.started = "YES"
    botSetting.save()
    return redirect("/")


def stop_bot(request):
    botSettings = BotSetting.objects.all()
    try:
        botSetting = botSettings[0]
    except Exception as e:
        botSetting = BotSetting(
            user=request.user,
            started="NO"
            )
        botSetting.save()
        return redirect("/")

    botSetting.started = "NO"
    botSetting.save()
    return redirect("/")


def check_bot_status():
    botSettings = BotSetting.objects.all()
    botSetting = botSettings[0]
    if botSetting.started == "YES":
        return True
    else:
        return False

@csrf_exempt
def execute(request):
    # check if the bot is on or off, if its off, it won't execute the message
    if not check_bot_status():
        res = {"info": "The bot is off, make sure to turn it on."}
        return JsonResponse(res, safe=False)

    # request.body contains the webhook message we are sending.
    # and here we want to convert them into json data.
    data=json.loads(request.body)
    print("Message from webhook: ", data)

    # check for the platform from the webhook message 
    # and determines the next action
    platform = "ALPACA"
    if "platform" in data:
        platform = str(data["platform"]).upper()
    if platform not in PLATFORMS:
        res = {"error": f"not supported platform. must be one of these {PLATFORMS}."}
        return JsonResponse(res, safe=False)

    # if the platform is Alpaca
    if platform == "ALPACA":
        # retrieves alpaca API key and secret
        api_key = ALPACA_API_KEY
        api_secret = ALPACA_API_SECRET
        api_url = ALPACA_BASE_URL

        # if it can't read keys from the environment variables, it will
        # try to read them from the webhook message, if it can't still
        # read them, it will return an error message
        if not api_key or not api_secret or not api_url:
            try:
                api_key = data["ALPACA_API_KEY"]
                api_secret = data["ALPACA_API_SECRET"]
                if "trade_mode" in data:
                    trade_mode = data["trade_mode"]
                if str(trade_mode).upper() != "LIVE":
                    api_url = "https://paper-api.alpaca.markets"
                else:
                    api_url = "https://api.alpaca.markets"
            except Exception as e:
                res = {"error":f"{e} must be defined in webhook message"}
                return JsonResponse(res, safe=False)

        # initializes Alpaca API class with api key, secret and url
        client = Alpaca(api_key, api_secret, api_url)

        # tries to retrieve some must-be-present parameters from the
        # webhook message (order_type, symbol, size, side)
        # if it can't find them, it will response with an error
        try:
            order_type = data["order_type"].lower()
            symbol = data["symbol"]
            quantity = int(data["size"])
            side = data["side"].lower()
        except Exception as e:
            res = {"error":f"{e} must be defined in webhook message"}
            return JsonResponse(res, safe=False)

        # checks for open orders in the opposite direction and cancels them
        side1 = "sell" if side=="buy" else "buy"
        open_orders = client.list_orders(params={"symbols":symbol})
        open_orders = [order for order in open_orders if order["side"]==side1]
        for order in open_orders:
            client.cancel_order(order)

        time_in_force = "day"
        limit_price = None
        stop_price = None
        client_order_id = None
        extended_hours = None
        order_class = None
        take_profit = None
        stop_loss = None
        trail_price = None
        trail_percent = None

        # retrieves all other parameters if present in the message
        if "limit_price" in data:
            limit_price = data["limit_price"]
        if "stop_price" in data:
            stop_price = data["stop_price"]
        if "extended_hours" in data:
            extended_hours = data["extended_hours"]
        if "order_class" in data:
            order_class = data["order_class"]
        if "take_profit" in data:
            take_profit = data["take_profit"]
        if "stop_loss" in data:
            stop_loss = data["stop_loss"]
        if "trail_price" in data:
            trail_price = data["trail_price"]
        if "trail_percent" in data:
            trail_percent = data["trail_percent"]

        # submits an order with the given parameters
        res = client.submit_order(
            symbol=symbol,
            quantity=quantity,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            stop_price=stop_price,
            extended_hours=extended_hours,
            order_class=order_class,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trail_price=trail_price,
            trail_percent=trail_percent
        )

        # sends json response back after the execution
        # we can view this response from postman after we hit send
        return JsonResponse(res, safe=False)

    # if the platform is Coinbase
    elif platform == "COINBASE":
        # retrieves API credentials from environment variables
        api_key = CB_API_KEY
        api_secret = CB_API_SECRET
        passphrase = CB_PASS_PHRASE
        api_url = CB_API_URL

        # if it can't find them there, it tries to find them from
        # the webhook message, if it can't still find them, it will
        # send an error message back
        if not api_key or not api_secret or not passphrase:
            try:
                api_key = data["CB_API_KEY"]
                api_secret = data["CB_API_SECRET"]
                passphrase = data["CB_PASS_PHRASE"]
                if "trade_mode" in data:
                    trade_mode = data["trade_mode"]
                if str(trade_mode).upper() != "LIVE":
                    api_url = "https://api-public.sandbox.pro.coinbase.com"
                else:
                    api_url = "https://api.pro.coinbase.com"
            except Exception as e:
                res = {"error":f"{e} must be defined in webhook message"}
                return JsonResponse(res, safe=False)
        
        # initializes Coinbase API class with coinbase API credentials
        client = Coinbase(api_key, api_secret, passphrase, api_url=api_url)

        # tries to find some must-be-present parameters from the webhook message,
        # if it can't find any of them, it will reply with an error message.
        try:
            order_type = data["order_type"].lower()
            product_id = data["symbol"]
            side = data["side"].lower()
        except Exception as e:
            res = {"error":f"{e} must be defined in webhook message"}
            return JsonResponse(res, safe=False)

        # tries to validate if the symbol is in coinbase market list
        if product_id not in CB_MARKETS["MARKET"].tolist():
            res = {"error": "invalid symbol for coinbase pro"}
            return JsonResponse(res, safe=False)

        # if the order type is limit, the price and size must be present in the message
        if order_type == "limit":
            if "price" not in data:
                res = {"error": "'price' must be defined for limit orders."}
                return JsonResponse(res, safe=False)
            if "size" not in data:
                res = {"error": "'size' must be defined for limit orders."}
                return JsonResponse(res, safe=False)

            price = data["price"]
            size = data["size"]

            # normalize the price and size based on the rules defined in CB_MARKET.csv
            price = normalize_price(product_id, price)
            size = normalize_size(product_id, size)

            # if stop parameter is in the message, its a stop order, and
            # thus, it needs to have stop_price in its message, otherwise,
            # responses with an error
            if "stop" in data:
                stop = data["stop"]
                if "stop_price" not in data:
                    res = {"error": "'stop_price' must be specified for stop orders."}
                    return JsonResponse(res, safe=False)
                stop_price = data["stop_price"]
                res = client.place_order(product_id, side, "limit", size=size, price=price, stop=stop, stop_price=stop_price)
                print(res)
                return JsonResponse(res, safe=False)

            # if all good, places an order in coinbase
            res = client.place_order(product_id, side, "limit", size=size, price=price)
            print(res)
            return JsonResponse(res, safe=False)

        # if order type is market, we specify order amount either by
        # funds and size, so either parameter should be present in the message.
        elif order_type == "market":
            if "funds" in data:
                funds = data["funds"]
                funds = normalize_price(product_id, funds)
                res = client.place_order(product_id, side, "market", funds=funds)
                print(res)
                return JsonResponse(res, safe=False)
            elif "size" in data:
                size = data["size"]
                size = normalize_size(product_id, size)
                res = client.place_order(product_id, side, "market", size=size)
                print(res)
                return JsonResponse(res, safe=False)
            else:
                res = {"error": "'size' or 'funds' must be defined for market orders."}
                return JsonResponse(res, safe=False)

        else:
            res = {"error": "invalid order type for coinbase pro"}
            return JsonResponse(res, safe=False)

    # if the platform is Binance US
    elif platform == "BINANCEUS":
        # retrieves API credentials from environment variables
        api_key = BN_API_KEY
        api_secret = BN_API_SECRET

        # if it can't find them there, it tries to find them from
        # the webhook message, if it can't still find them, it will
        # send an error message back
        if not api_key or not api_secret:
            try:
                api_key = data["BN_API_KEY"]
                api_secret = data["BN_API_SECRET"]
            except Exception as e:
                res = {"error":f"{e} must be defined."}
                return JsonResponse(res, safe=False)
        
        # initializes Coinbase API class with coinbase API credentials
        client = Binance(api_key, api_secret, tld="us")
        try:
            order_type = data["order_type"].upper()
            product_id = data["symbol"].upper()
            side = data["side"].upper()
            quantity = data["size"]
        except Exception as e:
            res = {"error":f"{e} must be defined."}
            return JsonResponse(res, safe=False)

        try:
            info = client.get_symbol_info(symbol=product_id)
        except:
            res = {"code":"error", "message": f"Invalid symbol - '{product_id}'"}
            return JsonResponse(res, safe=False)
        else:
            if not info:
                res = {"code":"error", "message": f"Invalid symbol - '{product_id}'"}
                return JsonResponse(res, safe=False)

        price_filter = float(info['filters'][0]['tickSize'])
        if "price" in data:
            price = float(data['price'])
            price = D.from_float(price).quantize(D(str(price_filter)))

        minimum = float(info['filters'][2]['minQty'])
        quantity = D.from_float(quantity).quantize(D(str(minimum)))
        timeInForce = "GTC"

        params = {
            "symbol": product_id,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }

        try:
            price_filter = float(info['filters'][0]['tickSize'])
            if order_type == "LIMIT" or order_type == "STOP_LOSS_LIMIT" or order_type == "TAKE_PROFIT_LIMIT":
                if "price" in data:
                    price = float(data['price'])
                    price = D.from_float(price).quantize(D(str(price_filter)))
                    params["price"] = price
                    params["timeInForce"] = "GTC"
                # else:
                #     res = {"code": "error", "message": f"'price' must be defined for {order_type} orders."}
                #     return JsonResponse(res, safe=False)
            if order_type == "STOP_LOSS" or order_type == "STOP_LOSS_LIMIT" or order_type == "TAKE_PROFIT" or order_type == "TAKE_PROFIT_LIMIT":
                if "stopPrice" in data:
                    stopPrice = float(data['stopPrice'])
                    stopPrice = D.from_float(stopPrice).quantize(D(str(price_filter)))
                    params["stopPrice"] = stopPrice
                # else:
                #     res = {"code": "error", "message": f"'stopPrice' must be defined for {order_type} orders."}
                #     return JsonResponse(res, safe=False)

            if "trade_mode" in data:
                if str(data["trade_mode"]).lower() != "live":
                    print(params)
                    res = client.create_test_order(**params)
                    return JsonResponse(res, safe=False)
            try:
                if str(trade_mode).lower() != "live":
                    print(params)
                    res = client.create_test_order(**params)
                    return JsonResponse(res, safe=False)
            except:
                pass

            print(params)
            res = client.create_order(**params)
        except Exception as e:
            res = {"code": e.__dict__["code"], "message": e.__dict__["message"]}

        return JsonResponse(res, safe=False)


# normalizes the order size based on the base currency
def normalize_size(product_id, size):
    sizeMin = CB_MARKETS[CB_MARKETS["MARKET"]==product_id].iloc[0]["BASE ORDER MIN"]
    sizeMax = CB_MARKETS[CB_MARKETS["MARKET"]==product_id].iloc[0]["BASE ORDER MAX"]
    tick = CB_MARKETS[CB_MARKETS["MARKET"]==product_id].iloc[0]["BASE TICK SIZE"]

    if float(size) > sizeMax:
        size = sizeMax
        return size
    if float(size) < sizeMin:
        size = sizeMin
        return size

    size = int(float(size) * round(1/tick)) / round(1/tick)
    return size


# normalize the price, based on the quote currency
def normalize_price(product_id, price):
    tick = CB_MARKETS[CB_MARKETS["MARKET"]==product_id].iloc[0]["QUOTE TICK SIZE"]

    price = int(float(price) * round(1/tick)) / round(1/tick)
    return price
