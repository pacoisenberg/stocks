import pymongo
from stock_lookup import mongo_initialize, iex_environtment_selection
import pprint

def get_stock_info(stocks_collection):
    print("getting stock info from mongo")

    stock = stocks_collection.find_one()
    pprint.pprint(stock)

def print_timeseries_inventory(timeseriesInventory):
    print("printing inventory...")
    timeseries_inventory = timeseriesInventory.distinct("id")

    for key in timeseries_inventory:
        print(key)

if __name__ == '__main__':
    try:
        environment = iex_environtment_selection()
        db, collections = mongo_initialize(environment["env"])
        # get_stock_info(collections["stocks_collection"])
        print_timeseries_inventory(collections["timeseriesInventory"])

    except:
        print("Didn't work")
        raise

    finally:
        print(f'Used the {environment["env"]} environment.')
