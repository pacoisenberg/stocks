import requests
import pymongo
import json
import datetime
import pytz

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
        return(db, collections)

# returns current stock info based on stocks in environment and the message credits used
def stock_quote(environment):
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
        print(f'\nAPI Call: {environment["base_url"]}/stock/{stock}/quote')
        try:
            req = requests.get(
                f'{environment["base_url"]}/stock/{stock}/quote',
                params
            )
            print(req.status_code)
            iex_current_message_count += int(req.headers["iexcloud-messages-used"])
            stock_info.append(req.json()) #type == dictionary
        except Exception as err:
            print("Unable to complete IEX Request")
            raise
        else:
            stock_info.append(change_stock_info_to_market_time(stock_info.pop()))
    print(f'This call used {iex_current_message_count} message credits.')
    return(stock_info, iex_current_message_count)

#insert all of the stock quote information into mongodb
def insert_docs(collection, dict_array):
    print("Inserting stocks into Mongo...")
    results = {}
    try:
        for stock_dict in dict_array:
            result = collection.insert_one(stock_dict)
            results[stock_dict["symbol"]] = result
    except Exception as err:
        raise
    else:
        for result in results:
            print(f"{result}: {results[result].inserted_id}")

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
                f"have been used since last cleared.")

        if updated_doc['message_count'] > 45000:
            print("If you are using prod, you are getting close to the monthly limit")

if __name__ == '__main__':
    try:
        environment = iex_environtment_selection()
        db, collections = mongo_initialize(environment["env"])
        stock_info, iex_message_use = stock_quote(environment)
        insert_docs(collections["stocks_collection"], stock_info)
        update_message_count(collections["configValues_collection"], iex_message_use)
        if iex_message_use > 100:
            print(f"This call used {iex_message_use} messages. Do you know what you're doing?")
    except:
        print("Too bad.")
        raise
    finally:
        print(f'Used the {environment["env"]} environment.')
