"""
dicc = {
    'a':5,
    'b':1,
    1: 10
}
dicc['nuevo'] = "valor nuevo"
dicc[1] = 33443444433

valor = dicc[1]
valor = dicc.get('a',False)

del dicc['b']
key = dicc.keys()
print(valor)
print(key)
"""

a = None
if a:
    print("Es True")
else:
    print("Es False")
