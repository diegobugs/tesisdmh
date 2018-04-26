import json

# pykryge
# open lyer
# open map

from flask import Flask
from flask import request
from flask_cors import CORS

import final_v3 as v3

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
    tiempoIntervalo = 10 # minutos
    diametroAnalizar = '45000' # metros


    resp = v3.SVM(finicio,ffin,lugar)

    print("alerta es "+str(resp['tormenta']))

    return json.dumps({
        'success': True,
        'tormenta': resp['tormenta'],
        'src': resp['src'],
        'tiempo':round(resp['tiempo'],0),
        'rayos_geojson':resp['rayos.geojson'],
        'pol_geojson':resp['pol.geojson'],
        'tra_geojson':resp['tra.geojson']
    }), 200, {
        'ContentType': 'application/json'
    }

if __name__ == "__main__":
    app.run(debug=True)
