import numpy as np
import matplotlib.pyplot as plt


# X e Y serán el primer conjunto del cuarteto de Anscombe
# (https://en.wikipedia.org/wiki/Anscombe%27s_quartet)

points = ([-25.0,-50.0],[-24.0,51.0],[-26.0,50.0],[-24.0,-54.0])


X = [point[0] for point in points]
X = np.array(X)
Y = [point[1] for point in points]
Y = np.array(Y)

# X = np.array([10.0, 8.0, 13.0, 9.0, 11.0, 14.0, 6.0, 4.0, 12.0, 7.0, 5.0])
# Y = np.array([8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68])

# Calculamos los coeficientes del ajuste (a X + b)
a, b = np.polyfit(X, Y, 1)
# Calculamos el coeficiente de correlación
r = np.corrcoef(X, Y)

# Dibujamos los datos para poder visualizarlos y ver si sería lógico
# considerar el ajuste usando un modelo lineal
plt.plot(X, Y, 'o')
plt.xlim(np.min(X) - 1, np.max(X) + 1)
plt.ylim(np.min(Y) - 1, np.max(Y) + 1)
plt.plot(X, a * X + b)
plt.text(4, 10, 'r = {0:2.3f}'.format(r[0, 1]))
plt.text(4, 9, 'Y = {0:2.3f} X + {1:2.3f}'.format(a, b))
plt.show()