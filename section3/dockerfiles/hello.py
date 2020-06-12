from flask import Flask, request, escape

app = Flask(__name__)

@app.route("/")
def hello():
    name = request.args.get("name", "World")
    return f"Hello, {escape(name)}! Greetings from a Container"

