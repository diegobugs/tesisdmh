import numpy as np
import matplotlib.pyplot as plt
from sklearn import svm
from matplotlib import style
style.use("ggplot")

X = [0,4,10.2,9,8.6,0,12]
y = [2,3,12.5,2,5.5,1,14]

# plt.scatter(x,y)
# plt.show()

# X = np.array([[0,240000],
# 			 [4,350000],
# 			 [10.2,1200000],
# 			 [9,1000000],
# 			 [8.6,990000],
# 			 [0,100000],
# 			 [12,3400000]])
#
# y = [0,0,1,0,0,0,1]

clf = svm.SVC(kernel='linear', C=1.0)
X = np.reshape(X,(1, -1)) # converting to matrix of n X 1
clf.fit(X,y)

Z = [1100000]
# Z = np.reshape(Z,(1,-1))
print(clf.predict(Z))
w = clf.coef_[0]
print("Coef:" + str(w))
a = -w[0] / w[1]

xx = np.linspace(0,4500000)
yy = a * xx - clf.intercept_[0] / w[1]

h0 = plt.plot(xx,yy,'k-', label="Non wighted div")

plt.scatter(X[:,0],X[:,1], c=y)
plt.legend()
plt.show()