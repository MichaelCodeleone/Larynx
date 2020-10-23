from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#----------For Private key to Address----------
import codecs
import ecdsa
from Crypto.Hash import keccak


#----------Private key to Address----------
# Modified from https://www.freecodecamp.org/news/how-to-create-an-ethereum-wallet-address-from-a-private-key-ae72b0eee27b/
def private_to_address(private_key):
    private_key_bytes = codecs.decode(private_key, 'hex')
    # Get ECDSA public key
    key = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1).verifying_key
    key_bytes = key.to_string()
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(key_bytes)
    keccak_digest = keccak_hash.hexdigest()
    # Take the last 20 bytes
    wallet_len = 40
    wallet = '0x' + keccak_digest[-wallet_len:]
    return wallet

app = Flask(__name__)

#----------Flask-SQLAlchemy----------
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Larynx.db"
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)

#----------SQL Message Table----------
class Message(db.Model):

    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    userFrom = db.Column(db.Text)
    userTo = db.Column(db.Text)
    message = db.Column(db.Text)
    postDate = db.Column(db.DateTime, default= datetime.now)
     
    def __init__(self, userFrom, userTo, message):
        self.userFrom = private_to_address(userFrom).lower()
        #----------If blank then sends to self----------
        self.userTo = userTo.lower() if userTo != '' else self.userFrom.lower()
        self.message = message
        self.postDate = datetime.now()

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        rows = Message.query.order_by(Message.id.desc()).limit(10).all()
        return render_template("index.html",messages = rows)
    elif request.method == "POST":
        rows = Message.query.order_by(Message.id.desc()).limit(10).all()
        userFrom = request.form.get("userFrom")
        userTo = request.form.get("userTo")
        userMessage = request.form.get("message")

        #----------Ensure private key----------
        if len(userFrom) != 64:
            return render_template("index.html",messages = rows)

        #----------Ensure public address or blank----------
        if len(userTo) not in {0,42}:
            return render_template("index.html",messages = rows)

        if not (userFrom and userMessage):
            return render_template("index.html",messages = rows)

        message = Message(userFrom,userTo,userMessage)
        db.session.add(message)
        db.session.commit()
        rows = Message.query.order_by(Message.id.desc()).limit(10).all()
        return render_template("index.html",messages = rows)

@app.route('/inbox', methods=["GET", "POST"])
def inbox():
    if request.method == "GET":
        return render_template("inbox.html")
    elif request.method == "POST":
        receiver = request.form.get("receiver").lower()
        if receiver:
            rows = Message.query.filter_by(userTo = receiver).order_by(Message.id.desc())
            return render_template("inbox.html", messages = rows)
    return render_template("inbox.html")

@app.route('/sent', methods=["GET", "POST"])
def sent():
    if request.method == "GET":
        return render_template("sent.html")
    elif request.method == "POST":
        sender = request.form.get("sender").lower()
        if sender:
            rows = Message.query.filter_by(userFrom = sender).order_by(Message.id.desc())
            return render_template("sent.html", messages = rows)
    return render_template("sent.html")

@app.route('/searchByUser', methods=["GET", "POST"])
def searchByUser():
    if request.method == "GET":
        return render_template("searchByUser.html")
    elif request.method == "POST":
        sender = request.form.get("sender").lower()
        receiver = request.form.get("receiver").lower()
        if not (sender or receiver):
            return render_template("searchByUser.html")
        if sender and receiver:
            rows = Message.query.filter_by(userFrom = sender, userTo = receiver).order_by(Message.id.desc())
            return render_template("searchByUser.html", messages = rows)
        if sender:
            rows = Message.query.filter_by(userFrom = sender).order_by(Message.id.desc())
        if receiver:
            rows = Message.query.filter_by(userTo = receiver).order_by(Message.id.desc())
        return render_template("searchByUser.html", messages = rows)

@app.route('/searchByMessage', methods=["GET", "POST"])
def searchByMessage():
    if request.method == "GET":
        return render_template("searchByMessage.html")
    elif request.method == "POST":
        message = request.form.get("message")
        if not message:
            return render_template("searchByMessage.html")
        message = Message.query.filter(Message.message.contains(message)).order_by(Message.id.desc())
        return render_template("searchByMessage.html", messages = message)

if __name__ == "__main__":
    app.run()
