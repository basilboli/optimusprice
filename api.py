from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse, abort
import logging
import os
import binascii
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)
client = MongoClient()
db = client.optimusprice

products = [
    {
        "id": 1,
        "brand": "Samsung",
        "name": "Samsung SSD 750 EVO 120 Go",
        "price": "64.94",
        "image": "http://media.ldlc.com/ld/products/00/03/53/73/LD0003537330_2_0003559375.jpg"
    },
    {
        "id": 2,
        "brand": "ASUS",
        "name": "ASUS GeForce GTX 950 GTX950-OC-2GD5",
        "price": "189.95",
        "image": "http://media.ldlc.com/ld/products/00/03/58/29/LD0003582993_2.jpg"
    },
    {
        "id": 3,
        "brand": "Acer",
        "name": "Acer 27 LED - S277HKWMJDPP",
        "price": "619.95",
        "image": "http://media.ldlc.com/ld/products/00/03/45/80/LD0003458035_2.jpg"
    },
    {
        "id": 4,
        "brand": "Synology",
        "name": "Synology DiskStation DS716+",
        "price": "489.95",
        "image": "http://media.ldlc.com/ld/products/00/03/38/90/LD0003389017_2.jpg"
    },
    {
        "id": 5,
        "brand": "Apple",
        "name": "Apple iPad Pro 12.9 Wi-Fi + Cellular 256 Go Or",
        "price": "1419.85",
        "image": "http://media.ldlc.com/ld/products/00/03/59/79/LD0003597900_2.jpg"
    },
    {
        "id": 6,
        "brand": "Lenovo",
        "name": "Lenovo ThinkPad W541 (20EF000WFR)",
        "price": "1799.95",
        "image": "http://media.ldlc.com/ld/products/00/01/51/17/LD0001511734_2_0001731179_0003006225.jpg"
    }
]

users = [
    {
        "id": 1,
        "like": [2, 1, 6]
    },
    {
        "id": 2,
        "like": [3, 2]
    }
]


def generate_token(user_id):
    return binascii.hexlify(os.urandom(user_id))


def create_user(user_id, product_id):
    user = {
        'id': user_id,
        'like': [product_id]
    }
    users.append(user)


@app.route('/optimusprice/api/v0.0.1/products/all', methods=['GET'])
def get_products():
    return jsonify({'products': products})

@app.route('/optimusprice/api/v0.0.1/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = [product for product in products if product['id'] == product_id]
    if len(product) == 0:
        abort(404)
    return jsonify({'product': product[0]})

@app.route('/optimusprice/api/v0.0.1/products/<int:product_id>/changeprice', methods=['PUT'])
def update_task(product_id):
    product = [product for product in products if product['id'] == product_id]
    if len(product) == 0:
        abort(404)
    product[0]['price'] = request.json.get('price', product[0]['price'])
    return jsonify({'product': product[0]})

@app.route('/optimusprice/api/v0.0.1/products/likes/<int:user_id>', methods=['GET'])
def user_like(user_id):
    user = [user for user in users if user['id'] == user_id]
    if len(user) == 0:
        abort(404)
    return jsonify({'like': user[0]["like"]})

@app.route('/optimusprice/api/v0.0.1/products/<int:product_id>/likeby', methods=['GET'])
def like_by(product_id):
    like = [user for user in users if product_id in user['like']]
    if len(like) == 0:
        abort(404)
    return jsonify({'likeby': like})

@app.route('/optimusprice/api/v0.0.1/get_token', methods=['POST'])
def get_token():
    product_id = request.json.get('product_id')
    user_id = request.json.get('user_id')

    product = [product for product in products if product_id  == product['id']]
    if len(product) == 0:
        abort(404)
    user = [user for user in users if user_id == user['id']]
    if len(user) == 0:
        create_user(user_id, product_id)
    else:
        x = set(user[0]['like'])
        x.add(product_id)
        user[0]['like'] = list(x)

    user[0]['token'] = generate_token(user_id)

    return jsonify({'token': user[0]['token']})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(debug=True, host= '0.0.0.0')
