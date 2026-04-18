# Usar imagen ligera de Python
FROM python:3.9-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias
RUN pip install flask

# Copiar archivos del proyecto
COPY app.py init_db.py ./

# Ejecutar el script de inicialización para crear DB y archivos
RUN python init_db.py

# Exponer el puerto
EXPOSE 5000

# Comando para arrancar la app
CMD ["python", "app.py"]
