#MONICA FERNANDA ALFARO RANGEL

#2 Crear variable y saludar al estudiante
nombre_estudiante = input ("Escribe su nombre: ")
print ("Bienbenid@ " + nombre_estudiante + "!")

#3. crear un diccionario contenga tres elementos.
#  Cada clave deberá corresponder al nombre de una asignatura
#  y cada valor a la calificación obtenida.
calificaciones= {
    "Matematicas":9.0,
    "programacion": 9.5,
    "Redes": 8.5
}

#4.Agrega la asignatura BD con la calificación de 9
calificaciones.setdefault("BD", 9.0)

#5.Modifica la calificación anterior a 10 e imprime el resultado
calificaciones.update({"BD": 10})
print(calificaciones)
#6. Recorre el diccionario e imprime tanto la clave como el valor, 
# no olvides emplear una función de conversión
for calificacion in calificaciones.items():
   print (calificacion)

#7.Imprime cuantos elementos tiene el diccionario
print(f"canrtidad de elementos: {len(calificaciones)}")

#8.Elimina la primera asignatura
calificaciones.pop("Matematicas", 9.0)
print(calificaciones)
#9.Comprueba si la clave “BD” existe o no e imprime un mensaje


#10.Crea una copia del diccionario


#11.Imprime las claves del diccionario copia


#12.Imprime los valores del diccionario copia