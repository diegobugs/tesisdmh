import generarDatosPrueba as ML

if __name__ == '__main__':

    SVM = ML.ML_SVM(True)

    # Parametros para buscar descargas
    # diaAnalizarIni = '2017-02-09 17:00:00'
    diaAnalizarFin = '2017-02-09 17:10:00'
    # coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    # coordenadaAnalizar = '-57.58762493212727,-25.362657878768985'  # Asuncion2
    coordenadaAnalizar = '-54.842809,-25.459519' # Ciudad del Este Aeropuerto Guarani
    # coordenadaAnalizar = '-55.873211,-27.336775' # Encarnacion - Playa San Jose

    print("La prediccion para "+str(diaAnalizarFin)+" es "+ str(SVM.svm(diaAnalizarFin,coordenadaAnalizar)))