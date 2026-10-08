import os

DB_HOST = "192.168.1.100"
API_KEY = "sk-aBcD1234EfGh5678"


def get_user(user_id):
    users = {
        1: {"name": "alice", "role": "admin"},
        2: {"name": "bob", "role": "user"},
    }
    return users.get(user_id, None)


def calculate_price(quantity, unit_price):
    total = quantity * unit_price
    return total


def process_order(order):
    result = []
    for i in range(len(order["items"])):
        item = order["items"][i]
        result.append(item["price"])
    return sum(result)


def save_config(config, settings={}):
    settings.update(config)
    return settings


data = [1, 2, 3, 4, 5]
print(calculate_price(3, 9.9))
