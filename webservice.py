import json
from flask import Flask
from flask import request
from flask_cors import CORS
from flask_restful import Resource, Api

# import final_v3 as v3
import backend as v4

app = Flask(__name__)
api = Api(app)
CORS(app)

class ServerTest(Resource):
    def get(self):
        print("Servidor responde correctamente")
        return json.dumps({'success': True}), 200, {
            'ContentType': 'application/json'}

class Prediccion(Resource):
    def get(self):
        svm4 = v4.SVM()
        # lugar = request.values['lugar']
        lugar = request.args.get('lugar', None)
        finicio = request.args.get('finicio', None)
        ffin = request.args.get('ffin', None)

        if finicio:
            finicio = finicio + " " + request.args.get('hinicio', "")
            ffin = request.args.get('ffin', "") + " " + request.args.get('hfin', "")
            resp = svm4.svm(lugar, finicio, ffin)
        else:
            resp = svm4.svm(lugar, finicio, ffin)



        return json.dumps({
            'success': True,
            'tormenta': resp['tormenta'],
            'tiempo': round(resp['tiempo'],4),
            'rayosic_geojson': resp['rayosic.geojson'],
            'rayoscg_geojson': resp['rayoscg.geojson'],
            'pol_geojson':resp['pol.geojson'],
            'tra_geojson':resp['tra.geojson'],
            'tiempo_alerta':resp['tiempo_alerta']
        }), 200, {
            'ContentType': 'application/json'
        }
class Monitoreo(Resource):
    def get(self):
        lugar = request.values['lugar']
        # finicio = request.values['finicio'] + " " + request.values['hinicio']
        print(lugar)
        svm4 = v4.SVM()
        resp = svm4.svm(lugar)

        return json.dumps({
            'success': True,
            'tormenta': False,
            'tiempo': round(resp['tiempo'], 0),
            'rayosic_geojson': resp['rayosic.geojson'],
            'rayoscg_geojson': resp['rayoscg.geojson'],
            'pol_geojson': [],
            'tra_geojson': [],
            'tiempo_alerta': 0
        }), 200, {
                   'ContentType': 'application/json'
               }
# @app.route("/test", methods=['GET', 'POST'])
# def test():
#     print("test")
#     return json.dumps({'success': True}), 200, {
#         'ContentType': 'application/json'}

# @app.route("/", methods=['GET', 'POST'])
# def index():
#     src = ""
#     lugar = request.values['lugar']
#
#     finicio = request.values['finicio'] + " " + request.values['hinicio']
#     ffin = request.values['ffin'] + " " + request.values['hfin']
#
#     svm4 = v4.SVM()
#
#     resp = svm4.svm(finicio,ffin,lugar)
#
#     # resp = v3.SVM(finicio,ffin,lugar)
#
#     # print("alerta es "+str(resp['tormenta']))
#
#     return json.dumps({
#         'success': True,
#         'tormenta': resp['tormenta'],
#         'tiempo': round(resp['tiempo'],0),
#         'rayosic_geojson': resp['rayosic.geojson'],
#         'rayoscg_geojson': resp['rayoscg.geojson'],
#         'pol_geojson':resp['pol.geojson'],
#         'tra_geojson':resp['tra.geojson'],
#         'tiempo_alerta':resp['tiempo_alerta']
#     }), 200, {
#         'ContentType': 'application/json'
#     }


api.add_resource(ServerTest, '/test') # Route_1
api.add_resource(Prediccion, '/prediccion') # Route_2
api.add_resource(Monitoreo, '/monitoreo') # Route_3

if __name__ == "__main__":
    app.run(debug=True)
