import numpy as np

X = [[1,20], [1,2], [1,70],[1,100],[1,6]]
y = [4,  5, 6,4,5]

# print(X)
# print(y)

a = np.matrix(np.column_stack((X, y)))


# print("ordenado")
# print(a)
a = np.unique(a,axis=0)
# print(a)
# exit()

# a = a[np.argsort(a.A[:, 1])]


# print(a)

# print("separar en vector")


X = (np.delete(a, np.s_[2], axis=1)).tolist()

y = (np.delete(a, np.s_[0:2], axis=1)).ravel()
y = y.tolist()

print(X)
print(y)

# Z = np.reshape(A1, (-1, 2))
#
# print(Z)