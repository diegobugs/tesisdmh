import numpy as np
from sklearn.externals import joblib
from sklearn import svm
import csv

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
# #
X, y = [], []
with open('dataset\clf_data.csv', 'rt') as clf_data:
    spamreader = csv.reader(clf_data, delimiter=';')
    for row in spamreader:
        X.append([float(row[0]), float(row[1])])
with open('dataset\clf_know.csv', 'rt') as clf_know:
    spamreader = csv.reader(clf_know, delimiter=';')
    for row in spamreader:
        y.append(float(row[0]))

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

clf = joblib.load('modelo.sav')

# clf.fit(X, y)


# [[0,20], [0,2], [0,70],[0,100],[0,6]]
Z = [0, 11]
Z = np.reshape(Z, (1, -1))


prediccion = clf.predict(Z)



X = [[0,9], [0,12], [0,6.5],[0,18.5],[0,6],[0,0],[0,0.4], [0,20],[0,11], [0,10], [0,0.1], [0,1]]
y = [5,  10, 5, 10, 0, 0, 0, 10, 10, 10, 0, 0]

print(clf.score(X,y))

print(prediccion)
