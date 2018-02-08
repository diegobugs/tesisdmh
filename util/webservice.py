from flask import Flask
from flask import request
from flask_cors import CORS
import analisis_V5 as av5

import json

app = Flask(__name__)
CORS(app)

@app.route("/test", methods=['GET', 'POST'])
def test():
    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

@app.route("/", methods=['GET', 'POST'])
def index():
    src = ""
    lugar = request.values['lugar']
    finicio = request.values['finicio']
    ffin = request.values['ffin']
    hinicio = request.values['hinicio']
    hfin = request.values['hfin']



    return json.dumps({'success': True, 'tormenta': False, 'src': src}), 200, {
        'ContentType': 'application/json'}


if __name__ == "__main__":
    app.run(debug=True)
