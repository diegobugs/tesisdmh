from numpy import *
import matplotlib.pyplot as plt
#cantidad de puntos
n=20
random.seed(n)
x=linspace(0.0,1.0,n)
# un poco de ruido
ruido=random.normal(0,0.25,n)
# pendiente y offset
me=-2.0
be=3.0
# puntos: (x,ye)
ye=me*x+be + ruido
# grafico los puntos
plt.plot(x,ye,'o')
# Armo la matriz de Vandermonde
A=array([x,zeros(n)+1])
A=A.transpose();
# numpy hace el laburo pesado
result=linalg.lstsq(A,ye)
#pendiente y desplazamiento
#de recta de aproximacion
m,b=result[0]
# le chanto arriba la recta aproximada
plt.plot(x,m*x+b)
plt.show()