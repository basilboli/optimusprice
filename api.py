from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse, abort

app = Flask(__name__)
api = Api(app)

products = [
    {
        "id": 1,
        "brand": "Nike",
        "name": "Nike Roshe Nm Flyknit Se",
        "price": "130",
        "image": "http://cdn1.sarenza.net/static/_img/productsV4/0000130240/MD_0000130240_245917_09.jpg"
    },
    {
        "id": 2,
        "brand": "Reebok",
        "name": "Cl Lthr",
        "price": "89.99",
        "image": "http://cdn1.sarenza.net/static/_img/productsV4/0000104973/MD_0000104973_194128_09.jpg"
    }
]

users = [
    {
        "id": 1,
        "name": "luc",
        "like": {1, 2}
    }
]

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

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    app.run(debug=True, host= '0.0.0.0')