import hmac
import sqlite3
from smtplib import SMTPRecipientsRefused

from flask import *
from flask_jwt import *
from flask_cors import *
from flask_mail import Mail, Message
from datetime import timedelta


# creating a user object
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# initializing the database
class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect('shop.db')
        self.cursor = self.conn.cursor()

    # to commit multiple things
    def to_commit(self, query, values):
        self.cursor.execute(query, values)
        self.conn.commit()

    # one commit
    def single_commit(self, query):
        self.cursor.execute(query)

    # to fetch all
    def fetch_all(self):
        return self.cursor.fetchall()

    # to fetch one
    def fetch_one(self):
        return self.cursor.fetchone()


# create user table
def init_user_table():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    print("Opened database successfully")
    cursor.execute("CREATE TABLE IF NOT EXISTS users "
                   "(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                   "first_name TEXT NOT NULL,"
                   "last_name TEXT NOT NULL, "
                   "email_address TEXT NOT NULL, "
                   "username TEXT NOT NULL, "
                   "password TEXT NOT NULL)")
    print("Users table created successfully")
    conn.close()


# calling function to create users table
init_user_table()


# fetching users from the user table
def fetch_users():
    db = Database()
    query = "SELECT * FROM users"
    db.single_commit(query)
    registered_users = db.fetch_all()

    new_data = []

    for data in registered_users:
        new_data.append(User(data[0], data[4], data[5]))
    return new_data


# calling function to fetch all users
all_users = fetch_users()


username_table = {u.username: u for u in all_users}
userid_table = {u.id: u for u in all_users}


# function to get unique token upon registration
# def authenticate(username, password):
#     user = username_table.get(username, None)
#     if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
#         return user


# function to identify user
# def identity(payload):
#     user_id = payload['identity']
#     return userid_table.get(user_id, None)


# initializing app
app = Flask(__name__)
CORS(app)
app.debug = True
# app.config['SECRET_KEY'] = 'super-secret'
app.config["JWT_EXPIRATION_DELTA"] = timedelta(days=1)  # allows token to last a day
app.config['MAIL_SERVER'] = 'smtp.gmail.com'            # server for email to be sent on
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mikaylabeelders@gmail.com'
app.config['MAIL_PASSWORD'] = 'Ashleemiks12!*'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
# jwt = JWT(app, authenticate, identity)


@app.route('/protected')
# @jwt_required()
def protected():
    return '%s' % current_identity


# route to register user
@app.route('/register/', methods=["POST"])
@cross_origin()
def registration():
    response = {}
    db = Database()
    try:
        if request.method == "POST":

            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email_address']
            username = request.form['username']
            password = request.form['password']

            query = "INSERT INTO users(first_name, last_name, email_address,username, password) VALUES(?, ?, ?, ?, ?)"
            values = (first_name, last_name, email, username, password)
            db.to_commit(query, values)

            msg = Message('Welcome Email', sender='mikaylabeelders@gmail.com', recipients=[email])
            # message for the email
            msg.body = "Hello " + str(email) + \
                       "\n\nThank you for registering with us! \n\nWe look forward to doing business with you. " \
                       "\n\nRegards"
            mail.send(msg)

            response["message"] = "Successful Registration"
            response["status_code"] = 201
            return response
    except SMTPRecipientsRefused:
        response['message'] = "Please enter a valid email address."
        response['status_code'] = 400
        return response


@app.route('/login/', methods=["POST"])
def login():
    response = {}
    db = Database()
    username = request.form['username']
    password = request.form['password']
    query = 'SELECT * FROM users WHERE username =? and password=?', username, password
    # values = (username, password)
    # db.to_commit(query, values)
    results = db.fetch_all()
    if str(username) == results[0][3] and str(password) == results[0][4]:
        response["message"] = "Successful Registration"
        response["status_code"] = 201
        return response


# creating products object
class Products(object):
    def __init__(self, product_id, product_name, product_price, product_description):
        self.product_id = product_id
        self.product_name = product_name
        self.product_price = product_price
        self.product_description = product_description


# creating products table
def init_product_table():
    db = Database()
    query = ("CREATE TABLE IF NOT EXISTS products "
             "(product_id INTEGER PRIMARY KEY AUTOINCREMENT, "
             "product_name TEXT NOT NULL, "
             "product_price TEXT NOT NULL, "
             "product_quantity TEXT NOT NULL, "
             "product_description TEXT NOT NULL, "
             "total TEXT NOT NULL)")
    db.single_commit(query)
    print("Products table created successfully.")


# calling function to create products table
init_product_table()


# route to add a product
@app.route('/add-product/', methods=["POST"])
# @jwt_required()
def add_product():
    response = {}
    db = Database()
    if request.method == "POST":
        name = request.form['product_name']
        price = request.form['product_price']
        quantity = request.form['product_quantity']
        description = request.form['product_description']
        total = int(price) * int(quantity)
        if name == '' or price == '' or quantity == '' or description == '':
            return "Please fill in all entry fields"
        else:
            query = "INSERT INTO products( product_name, product_price, product_quantity, product_description, total)" \
                    "VALUES(?, ?, ?, ?, ?)"
            values = (name, price, quantity, description, total)
            db.to_commit(query, values)

            response["status_code"] = 201
            response['description_message'] = "Product added successfully"
            return response


# route to show all products
@app.route('/show-products/', methods=["GET"])
def show_products():
    response = {}
    db = Database()
    query = "SELECT * FROM products"
    db.single_commit(query)
    products = db.fetch_all()

    response['status_code'] = 200
    response['data'] = products
    return response


# calling function to show all products
all_products = show_products()


# route to delete single existing product using product ID
@app.route("/delete-product/<int:product_id>")
# @jwt_required()
def delete_product(product_id):
    response = {}
    db = Database()
    query = "DELETE FROM products WHERE product_id=" + str(product_id)
    db.single_commit(query)
    response['status_code'] = 200
    response['message'] = "Product deleted successfully."
    return response


# route to edit single existing product using product ID
@app.route('/edit-product/<int:product_id>/', methods=["PUT"])
# @jwt_required()
def edit_product(product_id):
    response = {}
    db = Database()

    if request.method == "PUT":
        with sqlite3.connect('shop.db'):
            data_received = dict(request.json)
            put_data = {}

            if data_received.get("product_name") is not None:
                put_data["product_name"] = data_received.get("product_name")
                query = "UPDATE products SET product_name =? WHERE product_id=?"
                values = (put_data["product_name"], product_id)
                db.to_commit(query, values)

                response['message'] = "Product update was successful."
                response['status_code'] = 200
            if data_received.get("product_price") is not None:
                put_data['product_price'] = data_received.get('product_price')
                query = "UPDATE products SET product_price =? WHERE product_id=?"
                values = (put_data["product_price"], str(product_id))
                db.to_commit(query, values)

                response["product_price"] = "Product price updated successfully"
                response["status_code"] = 200
            if data_received.get("product_quantity") is not None:
                put_data['product_quantity'] = data_received.get('product_quantity')
                query = "UPDATE products SET product_quantity =? WHERE product_id=?"
                values = (put_data["product_quantity"], str(product_id))
                db.to_commit(query, values)

                response["product_quantity"] = "Product quantity updated successfully"
                response["status_code"] = 200
            if data_received.get("product_description") is not None:
                put_data['product_description'] = data_received.get('product_description')
                query = "UPDATE products SET product_description =? WHERE product_id=?"
                values = (put_data["product_description"], str(product_id))
                db.to_commit(query, values)

                response["product_description"] = "Product description updated successfully"
                response["status_code"] = 200
            if data_received.get("total") is not None:
                put_data['total'] = data_received.get('total')
                query = "UPDATE products SET total =? WHERE product_id=?"
                values = (put_data["total"], str(product_id))
                db.to_commit(query, values)

                response["total"] = "The total updated successfully"
                response["status_code"] = 200
            return response


# route to view single existing product using product ID
@app.route('/view-product/<int:product_id>/', methods=["GET"])
def view_product(product_id):
    response = {}
    db = Database()
    query = ("SELECT * FROM products WHERE product_id=" + str(product_id))
    db.single_commit(query)
    response["status_code"] = 200
    response["message_description"] = "Product retrieved successfully"
    response["data"] = db.fetch_one()
    return response


if __name__ == "__main__":
    app.debug = True
    app.run()