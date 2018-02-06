from flask import Flask
from flask import request
import json
app = Flask(__name__)

@app.route("/", methods=['GET'])

def hello():
    lugar = request.form['lugar'];
    finicio = request.form['finicio'];
    ffin = request.form['ffin'];
    hinicio = request.form['hinicio'];
    hfin = request.form['hfin'];

    return json.dumps({'status': '200', 'tormenta':False});

if __name__ == "__main__":
    app.run()