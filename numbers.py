import requests
import json
import datetime
import pytz

# returns dictionary with keys "base_url", "iex_secret", "stocks"
def iex_environtment_selection(env):
    with open("config.json", 'r') as json_data_file:
        config = json.load(json_data_file)

    if env == "prod":
        environment = {
            "base_url": "https://cloud.iexapis.com/stable",
            "iex_secret": config["iex_token"]["production"],
            "stocks": ['AAXN', 'MRNA', 'AMZN', 'VOO', 'VTI']
        }
    else:
        environment = {
            "base_url": "https://sandbox.iexapis.com/stable",
            "iex_secret": config["iex_token"]["sandbox"],
            "stocks": ['AMZN', 'VOO']
        }
    return(environment)

# returns datetime object with utc time from a time given in milliseconds
def epoch_to_utc(epoch_milliseconds):
    return(datetime.datetime.utcfromtimestamp(epoch_milliseconds/1000).replace(tzinfo=pytz.UTC))

# returns datetime object converted to nyc timezone
def utc_to_nyc(utc_datetime):
    # print list of all common timezones
    # print("\n".join(pytz.common_timezones))
    return(utc_datetime.astimezone(pytz.timezone("America/New_York")))

# for getting current stock info based on stocks in environment
def stock_quote(environment):
    # Parameters for query string
    params = {
        "token": environment["iex_secret"]
        # "symbols": environment["stocks"]
    }
    stock_info = {}

    # TODO: https://iexcloud.io/docs/api/#batch-requests
    for stock in environment["stocks"]:
        print("\nAPI call: ",environment["base_url"]+"/stock/{}/quote".format(stock))
        req = requests.get(
            environment["base_url"]+"/stock/{}/quote".format(stock),
            params
        )
        print(req.status_code)
        stock_info[stock] = req.json() #type == dictionary
        for key in stock_info[stock]:
            print(key,":",stock_info[stock][key])
            if ("Time" in key and
                key != "latestTime" and
                stock_info[stock][key] != None):
                market_time = utc_to_nyc(epoch_to_utc(stock_info[stock][key]))
                print(key,":",market_time)

    return(stock_info)

environment = iex_environtment_selection("")

stock_quote(environment)
