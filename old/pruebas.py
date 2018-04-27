import numpy as np
# from mpl_toolkits.basemap import Basemap
# import matplotlib.pyplot as plt
# from sklearn.externals import joblib
from sklearn import linear_model
import matplotlib.pyplot as plt

x=np.array([-55,-56,-56.5,-57,-55.5])
y=np.array([-27,-27,-27.6,-26.5,-27.2])

#
# plt.plot(-55,-27)
# plt.plot(-56,-27)
# plt.plot(-56.5,-27.6)
# plt.plot(-57,-26.5)
# plt.plot(-55.5,-27.2)

a, b = np.polyfit(x, y, 1)
y = (a * x + b)

# plt.plot(x,y)
# plt.show()

print([(np.min(x),np.min(y)),(np.max(x),np.max(y))])

j = (np.array((x,y)).T)
for i in j:
    # print(np.asarray(i))
    xx = i[0]
    yy = i[1]
    plt.plot(xx,yy)

# plt.plot(j)
plt.show()

#
# # Coordenadas de Encarnación
# lllon = -56.533893
# urlon = -55.134718
# lllat = -27.735085
# urlat = -26.688416
#
# # Calculo del punto central para la proyección
# centerlon = float(lllon + urlon) / 2.0
# centerlat = float(lllat + urlat) / 2.0
#
# m = Basemap(resolution='i', llcrnrlon=lllon, urcrnrlon=urlon, lon_0=centerlon,
#         llcrnrlat=lllat, urcrnrlat=urlat, lat_0=centerlat, projection='tmerc')
# # Lectura de los bordes departamentales en un archivo SHP
# shp_info = m.readshapefile('dataset/shp/PRY_adm1', 'states',
#                        drawbounds=True, color='black')
#
# # Dibujar coordenadas
# m.drawmeridians(np.arange(urlon,lllon,-.5),labels=[0,1,1,0])
# m.drawparallels(np.arange(urlat,lllat,-.5),labels=[1,0,0,1])
#
# # Mostrar gráfico
# plt.show()
#
# exit()

# historialDescargas = [None] * 9
#
# print("Longitud del array "+str(len(historialDescargas)))
# peak = [[27,57],[27,57]]
# for idx, item in enumerate(historialDescargas):
#     historialDescargas.insert(idx,peak)
#     historialDescargas.pop()
#     break
#
# peak = [[27,58],[27,58]]
# for idx, item in enumerate(historialDescargas):
#     historialDescargas.insert(idx,peak)
#     historialDescargas.pop()
#     break
#
# print("Longitud del array "+str(len(historialDescargas)))
#
# print(historialDescargas)

# historialDescargas = [1,2,3,4,5,6,7,8,9]
#
# print(historialDescargas)
#
# shift_left(historialDescargas)
#
#
# print(historialDescargas)


# X = [[0,10], [0,4.5], [0,7.5],[0,12.6],[0,7.8],[0,0],[0,0.4], [0,15], [0, 11],[0,8],[0,13] ,[0,26], [0,16.4], [0,9.6] ,[0,0.051], [0,0.91],[0,0.014]]
# y = [10,  0, 0, 10, 0, 0, 0, 10,10,0,10,10, 10, 10, 0, 0, 0]
# # #
# X, y = [], []
# with open('dataset\clf_data.csv', 'rt') as clf_data:
#     spamreader = csv.reader(clf_data, delimiter=';')
#     for row in spamreader:
#         X.append([float(row[0]), float(row[1])])
# with open('dataset\clf_know.csv', 'rt') as clf_know:
#     spamreader = csv.reader(clf_know, delimiter=';')
#     for row in spamreader:
#         y.append(float(row[0]))

# print(X)
# print(y)

# a = np.matrix(np.column_stack((X, y)))
#
#
# # print("ordenado")
# # print(a)
# # a = np.unique(a,axis=0)
# # print(a)
# # exit()
#
# a = a[np.argsort(a.A[:, 1])]


# print(a)

# print("separar en vector")

#
# X = (np.delete(a, np.s_[2], axis=1)).tolist()
#
# y = (np.delete(a, np.s_[0:2], axis=1)).ravel()
# y = y.tolist()
# y = y[0]

# Z = np.reshape(A1, (-1, 2))
#
# print(Z)

# clf = svm.SVC(kernel='rbf', C=0.5, cache_size=500) #,probability=True, class_weight='balanced')

# clf = joblib.load('modelo.sav')
#
# # clf.fit(X, y)
#
#
# # [[0,20], [0,2], [0,70],[0,100],[0,6]]
# Z = [0, 10]
# Z = np.reshape(Z, (1, -1))
#
#
# prediccion = clf.predict(Z)
#
#
#
# X = [[0,0], [0,1], [0,2],[0,3],[0,4],[0,5],[0,6], [0,7],[0,8], [0,9], [0,10],[0,11],[0,12],[0,13],[0,14],[0,15],[0,16],[0,17],[0,18],[0,19],[0,20],[0,21],[0,22],[0,22],[0,23],[0,24]]
# y = [0,0,0,0,0,5,5,5,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10]
#
# print(clf.score(X,y))
#
# print(prediccion)
