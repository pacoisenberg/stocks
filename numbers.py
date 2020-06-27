import requests
import json
import datetime
import pytz

def iex_environtment_selection(env):
    with open("config.json", 'r') as json_data_file:
        config = json.load(json_data_file)

    if env == "prod":
        base_url = "https://cloud.iexapis.com/stable"
        iex_secret = iex_secret = config["iex_token"]["production"]
        stocks = ['AAXN', 'MRNA', 'AMZN', 'VOO', 'VTI']
    else:
        base_url = "https://sandbox.iexapis.com/stable"
        iex_secret = config["iex_token"]["sandbox"]
        stocks = ['AMZN', 'VOO']

    return(base_url, iex_secret, stocks)

def epoch_to_utc(epoch_milliseconds):
    return(datetime.datetime.utcfromtimestamp(epoch_milliseconds/1000).replace(tzinfo=pytz.UTC))

def utc_to_nyc(utc_datetime):
    # print list of all common timezones
    # print("\n".join(pytz.common_timezones))
    return(utc_datetime.astimezone(pytz.timezone("America/New_York")))

def stock_quote(stocks):
    stock_info = {}

    # TODO: https://iexcloud.io/docs/api/#batch-requests
    for stock in stocks:
        print("\nAPI call: ",base_url+endpoint_paths["price"].format(stock))
        req = requests.get(
            base_url+endpoint_paths["price"].format(stock),
            params
        )
        print(req.status_code)
        stock_info[stock] = req.json() #type == dictionary
        for key in stock_info[stock]:
            print(key,":",stock_info[stock][key])

    return(stock_info)

base_url, iex_secret, stocks = iex_environtment_selection("")

# Parameters for query string
params = {
    "token": iex_secret
    # "symbols": stocks"
}

# headers = {
# }


endpoint_paths = {
    "price":"/stock/{}/quote"
}
