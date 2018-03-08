import csv
import numpy as np
import os.path
import pandas as pd

X,y = [],[]

newX, newY = [],[]

with open('dataset\clf_data.csv', 'rt') as clf_data:
    spamreader = csv.reader(clf_data, delimiter=';')
    for row in spamreader:
        X.append([float(row[0]), float(row[1])])
with open('dataset\clf_know.csv', 'rt') as clf_know:
    spamreader = csv.reader(clf_know, delimiter=';')
    for row in spamreader:
        y.append(float(row[0]))


idx=0
for i in X:
    # print(i[1],y[idx])
    if i[1]<5 and y[idx]==0 and not (i[1]==0 and y[idx]==0):
        newX.append([i[0], i[1]])
        newY.append([y[idx]])

    if i[1]<9.9 and i[1]>=5 and y[idx]==5:
        newX.append([i[0], i[1]])
        newY.append([y[idx]])

    if i[1]>9.9 and y[idx]==10:
        newX.append([i[0],i[1]])
        newY.append([y[idx]])
    idx+=1

# # Ordenar X
# matrix = np.matrix(np.column_stack((newX, newY)))
# matrix = matrix[np.argsort(matrix.A[:, 1])]
#
# newX = (np.delete(matrix, np.s_[2], axis=1)).tolist()
# y = ((np.delete(matrix, np.s_[0:2], axis=1)).ravel()).tolist()
# newY = y[0]

os.remove('dataset\clf_data.csv')
os.remove('dataset\clf_know.csv')

if not os.path.exists('dataset\clf_data.csv'):
    pd.DataFrame(data=newX).to_csv('dataset\clf_data.csv', sep=";", mode='w', index=False, header=False)
if not os.path.exists('dataset\clf_know.csv'):
    pd.DataFrame(data=newY).to_csv('dataset\clf_know.csv', sep=";", mode='w', index=False, header=False)


for i in newX:
    print(i)