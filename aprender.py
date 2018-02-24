from util import MachineLearning as ML

if __name__ == '__main__':
    SVM = ML.ML_SVM(False)

    # Parametros para buscar descargas
    diaAnalizarIni = '2015-12-04 00:00:00'
    diaAnalizarFin = '2015-12-05 00:00:00'
    coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    # tiempoIntervalo = 10  # minutos
    # diametroAnalizar = '40000'  # en metros

    SVM.RecorrerYGenerar(diaAnalizarIni,diaAnalizarFin,coordenadaAnalizar)