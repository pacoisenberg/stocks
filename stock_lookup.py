import requests
import pymongo
import json
import datetime
import pytz

# returns datetime object with utc time from a time given in milliseconds
def epoch_to_utc(epoch_milliseconds):
    return(datetime.datetime.utcfromtimestamp(epoch_milliseconds/1000).replace(tzinfo=pytz.UTC))

# returns datetime object converted to nyc timezone
def utc_to_nyc(utc_datetime):
    # print list of all common timezones
    # print("\n".join(pytz.common_timezones))
    return(utc_datetime.astimezone(pytz.timezone("America/New_York")))

# Takes a dict with keys with 'time' in the name values in milliseconds
# and replaces it with a datetime object
def change_stock_info_to_market_time(stock_dict):
    for stock_key in stock_dict:
        print(stock_key,":",stock_dict[stock_key])
        if ("Time" in stock_key and
            stock_key != "latestTime" and
            stock_dict[stock_key] != None):
            stock_dict[stock_key] = utc_to_nyc(epoch_to_utc(stock_dict[stock_key]))
            print(stock_key,":",stock_dict[stock_key])
    return stock_dict

# returns dictionary with keys "base_url", "iex_secret", "stocks"
def iex_environtment_selection():
    with open("config.json", 'r') as json_data_file:
        config = json.load(json_data_file)

    if config["env"] == "prod":
        environment = {
            "env": "prod",
            "base_url": "https://cloud.iexapis.com/stable",
            "iex_secret": config["iex_token"]["production"],
            "stocks": ['AAXN', 'MRNA', 'AMZN', 'VOO', 'VTI'],
        }
    else:
        environment = {
            "env": "sandbox",
            "base_url": "https://sandbox.iexapis.com/stable",
            "iex_secret": config["iex_token"]["sandbox"],
            "stocks": ['AMZN', 'VOO'],
        }
    print(f"Environment is {environment['env']}.")
    return(environment)

# returns db and stocks_collection
def mongo_initialize(environment):
    print("Initializing mongo...")
    mongo_client = pymongo.MongoClient(serverSelectionTimeoutMS = 10)
    try:
        mongo_client.server_info()
    except Exception as err:
        print(err)
        print("Connection to mongodb failed. Try starting the server")
    else:
        if environment == "prod":
            db = mongo_client.finances_db
        else:
            db = mongo_client.finances_db_test
        collections = {}
        collections["stocks_collection"] = db.stocks
        collections["configValues_collection"] = db.configValues
        collections["timeseriesInventory"] = db.timeseriesInventory
        return(db, collections)

#updates mongodb with the additional messages used by the iex api call
def update_message_count(configValues_collection, iex_messages):
    print("Updating message count in mongo")
    try:
        result = configValues_collection.update_one(
            {"messages" : "iex"},
            {"$inc":{"message_count": iex_messages}}
            )
    except Exception as err:
        raise
    else:
        updated_doc = configValues_collection.find_one({"messages":"iex"})
        print (f"{updated_doc['message_count']} message credits "
                f"have been used since last cleared in the db.")

        if updated_doc['message_count'] > 45000:
            print("If you are using prod, you are getting close to the monthly limit")

#insert all of the stock quote information into mongodb
def insert_docs(collection, dict_array):
    print("Inserting into Mongo...")
    print(type(dict_array[0]))
    try:
        result = collection.insert_many(dict_array)
        print(result.inserted_ids)
    except Exception as err:
        raise

# gets inventory of available time series data from iex. Shouldn't need to run after loaded in db
def get_time_series_inventory(environment, collections):

    print("Getting timeseries inventory. Comment out this function after single use.")
    params = {"token":environment["iex_secret"]}

    url_endpoint_path = f'{environment["base_url"]}/time-series'
    print(f'\nAPI Call: {url_endpoint_path}')

    try:
        req = requests.get(url_endpoint_path, params)
    except Exception as err:
        raise
    else:
        print(req.status_code)
        iex_current_message_count = int(req.headers["iexcloud-messages-used"])
        print(f'This call used {iex_current_message_count} message credits.')

        if iex_current_message_count > 0:
            update_message_count(collections["configValues_collection"], iex_current_message_count)
        timeseries_inventory = req.json()
        insert_docs(collections["timeseriesInventory"], timeseries_inventory)

        return timeseries_inventory

# returns current stock info based on stocks in environment and the message credits used
def get_stock_quote(environment, configValues_collection):
    print("Getting stock quotes...")
    # Parameters for query string
    params = {
        "token": environment["iex_secret"]
        # "symbols": environment["stocks"]
    }
    stock_info = []
    iex_current_message_count = 0

    # TODO: https://iexcloud.io/docs/api/#batch-requests
    for stock in environment["stocks"]:

        url_endpoint_path = f'{environment["base_url"]}/stock/{stock}/quote'

        print(f'\nAPI Call: {url_endpoint_path}')
        try:
            req = requests.get(url_endpoint_path, params)

        except Exception as err:
            print("Unable to complete IEX Request")
            raise

        else:
            print(req.status_code)
            iex_current_message_count += int(req.headers["iexcloud-messages-used"])
            stock_info.append(change_stock_info_to_market_time(req.json())) #type == dictionary

    print(f'This call used {iex_current_message_count} message credits.')
    update_message_count(collections["configValues_collection"], iex_current_message_count)
    insert_docs(collections["stocks_collection"], stock_info)

    return(stock_info)

if __name__ == '__main__':
    try:
        environment = iex_environtment_selection()
        db, collections = mongo_initialize(environment["env"])

        # timeseries inventory should generally be commented out. Don't need this each time.
        # timeseries_inventory = get_time_series_inventory(environment, collections)
        stock_info = get_stock_quote(environment, collections["configValues_collection"])
    except:
        print("Too bad.")
        raise
    finally:
        print(f'Used the {environment["env"]} environment.')
