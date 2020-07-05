import pymongo

client = pymongo.MongoClient()

db = client.pymongo_test_db

stocks_collection = db.stocks

stock = {
    "symbol": "VTI",
    "open": "159.3",
    "close": "158.07"
}

result = stocks_collection.insert_one(stock)

print("entered as id: {result}".format(result=result.inserted_id))
