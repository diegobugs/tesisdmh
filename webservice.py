import json

# pykryge
# open lyer
# open map

from flask import Flask
from flask import request
from flask_cors import CORS

# import final_v3 as v3
import backend as v4

app = Flask(__name__)
CORS(app)

@app.route("/test", methods=['GET', 'POST'])
def test():
    print("test")
    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

@app.route("/", methods=['GET', 'POST'])
def index():
    src = ""
    lugar = request.values['lugar']

    finicio = request.values['finicio'] + " " + request.values['hinicio']
    ffin = request.values['ffin'] + " " + request.values['hfin']

    svm4 = v4.SVM()

    resp = svm4.svm(finicio,ffin,lugar)

    # resp = v3.SVM(finicio,ffin,lugar)

    # print("alerta es "+str(resp['tormenta']))

    return json.dumps({
        'success': True,
        'tormenta': resp['tormenta'],
        'tiempo': round(resp['tiempo'],0),
        'rayosic_geojson': resp['rayosic.geojson'],
        'rayoscg_geojson': resp['rayoscg.geojson'],
        'pol_geojson':resp['pol.geojson'],
        'tra_geojson':resp['tra.geojson'],
        'tiempo_alerta':resp['tiempo_alerta']
    }), 200, {
        'ContentType': 'application/json'
    }

if __name__ == "__main__":
    app.run(debug=True)
