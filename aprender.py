import MachineLearning as ML
import final_v3 as v3

if __name__ == '__main__':

    SVM = ML.ML_SVM(False)

    # Parametros para buscar descargas
    diaAnalizarIni = '2016-10-24 18:00:00'
    diaAnalizarFin = '2016-10-25 05:00:00'
    coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    # coordenadaAnalizar = '-54.842809,-25.459519' # Ciudad del Este Aeropuerto Guarani
    # coordenadaAnalizar = '-55.873211,-27.336775' # Encarnacion - Playa San Jose
    tiempoIntervalo = 10  # minutos
    diametroAnalizar = '45000'  # en metros

    v3.SVM(diaAnalizarIni,diaAnalizarFin,coordenadaAnalizar)
    # SVM.RecorrerYGenerar(diaAnalizarIni,diaAnalizarFin,coordenadaAnalizar,tiempoIntervalo,diametroAnalizar)