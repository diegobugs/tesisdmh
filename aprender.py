from util import MachineLearning as ML

if __name__ == '__main__':

    SVM = ML.ML_SVM(True)

    # Parametros para buscar descargas
    diaAnalizarIni = '2015-01-01 00:00:00'
    diaAnalizarFin = '2015-06-01 00:00:00'
    coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    tiempoIntervalo = 10  # minutos
    diametroAnalizar = '40000'  # en metros

    SVM.RecorrerYGenerar(diaAnalizarIni,diaAnalizarFin,coordenadaAnalizar,tiempoIntervalo,diametroAnalizar)