# Extractor de Datos de Ventas desde PDF

Este script de Python extrae datos de ventas de archivos PDF utilizando el modelo de IA Gemini de Google.

## Requisitos

- Python 3.7+
- Bibliotecas listadas en `requirements.txt`

## Configuración

1. Clona este repositorio o descarga los archivos `sales_data_extractor.py` y `requirements.txt`.

2. Instala las dependencias necesarias:

   ```
   pip install -r requirements.txt
   ```

3. Obtén una clave API de Google Gemini y reemplaza 'YOUR_API_KEY_HERE' en `sales_data_extractor.py` con tu clave real.

## Uso

1. Ejecuta el script:

   ```
   python sales_data_extractor.py
   ```

2. Se abrirá una ventana para que selecciones el archivo PDF que contiene los datos de ventas.

3. El script procesará el PDF, extraerá los datos de ventas y los mostrará en formato de tabla.

4. Se te preguntará si deseas descargar los datos como un archivo CSV. Responde 's' para sí o 'n' para no.

## Notas

- Asegúrate de que tu PDF contenga datos de ventas estructurados para obtener los mejores resultados.
- El script está diseñado para funcionar en un entorno de Google Colab, pero puede adaptarse para uso local con algunas modificaciones.

## Solución de problemas

Si encuentras algún error, asegúrate de:

- Haber instalado todas las dependencias correctamente.
- Usar una clave API de Gemini válida.
- Tener permisos de lectura/escritura en el directorio donde se ejecuta el script.

Para cualquier otro problema, por favor, abre un issue en este repositorio.
