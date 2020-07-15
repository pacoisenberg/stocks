import pymongo
import pprint

client = pymongo.MongoClient()

db = client.finances_db_test

stocks_collection = db.stocks

stock = stocks_collection.find_one()

print(type(stock))
print(f'{stock}')

pprint.pprint(stock)
print("====================")

print(stocks_collection.database)
