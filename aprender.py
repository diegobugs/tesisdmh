import MachineLearning as ML
import final_v2_cantidad_poli as v4

if __name__ == '__main__':

    SVM = ML.ML_SVM(False)

    # Parametros para buscar descargas
    diaAnalizarIni = '2015-04-12 05:00'
    diaAnalizarFin = '2015-04-12 10:00'
    # coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    coordenadaAnalizar = '-57.58762493212727,-25.362657878768985'  # Asuncion2
    # coordenadaAnalizar = '-54.842809,-25.459519' # Ciudad del Este Aeropuerto Guarani
    # coordenadaAnalizar = '-55.873211,-27.336775' # Encarnacion - Playa San Jose
    tiempoIntervalo = 10  # minutos
    diametroAnalizar = '45000'  # en metros

    svmv4 = v4.SVM(diaAnalizarIni,diaAnalizarFin,coordenadaAnalizar)

    # svmv4.svm(diaAnalizarIni,diaAnalizarFin,coordenadaAnalizar)
    # SVM.RecorrerYGenerar(diaAnalizarIni,diaAnalizarFin,coordenadaAnalizar,tiempoIntervalo,diametroAnalizar)