import pymongo
from stock_lookup import mongo_initialize, iex_environtment_selection
import pprint

def get_stock_info():
    print("getting stock info from mongo")
    stock = stocks_collection.find_one()

    print(type(stock))
    print(f'{stock}')

    pprint.pprint(stock)

if __name__ == '__main__':
    try:
        environment = iex_environtment_selection()
        db, stocks_collection = mongo_initialize(environment["env"])
        get_stock_info()

    except:
        print("Didn't work")
        raise

    finally:
        print(f'Used the {environment["env"]} environment.')
