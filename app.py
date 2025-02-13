import os
import streamlit as st
import google.generativeai as genai
import PyPDF2
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Cargar la API key desde el archivo .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("No se encontró la GOOGLE_API_KEY en el archivo .env")
    st.stop()

genai.configure(api_key=api_key)

# Crear la carpeta Output si no existe
output_dir = os.path.join(os.getcwd(), "Output")
os.makedirs(output_dir, exist_ok=True)

# Función para extraer texto del PDF


def extraer_texto_de_pdf(archivo_pdf):
    texto = ""
    try:
        lector_pdf = PyPDF2.PdfReader(archivo_pdf)
        for pagina in lector_pdf.pages:
            texto += pagina.extract_text()
    except Exception as e:
        st.error(f"Error al procesar el PDF: {e}")
    return texto


# Función para extraer datos de ventas del PDF usando GenAI


def extraer_datos_ventas(texto_pdf):
    modelo = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
    prompt = f"""
Extrae los datos de ventas para cada artículo del documento PDF proporcionado.  Ignora las filas que contengan totales (como "Total Client" o "Total Vendes") y cualquier texto que no sea parte de la tabla principal de artículos (fechas, encabezados de página, etc.).  Concéntrate en extraer datos de las siguientes columnas:

- **Article:**  El código o número de identificación del artículo.
- **Descripció:** La descripción completa del artículo.  Asegúrate de capturar toda la descripción, incluso si ocupa varias palabras.
- **Quantitat:**  La cantidad vendida del artículo.  Asegúrate de que este valor sea tratado como un número (entero). Incluye la unidad "U" al final.
- **Import:**  El importe total de venta para esa cantidad de artículo.  Asegúrate de que este valor sea tratado como un número (con decimales). Separa los decimales con coma (,).
- **Cost:** El coste del artículo.  Asegúrate de que este valor sea tratado como un número (con decimales). Separa los decimales con coma (,).
- **% Marge:** El porcentaje de margen de beneficio del artículo.  Asegúrate de que este valor sea tratado como un número (con decimales). Separa los decimales con coma (,).

Para cada fila de la tabla que represente un artículo individual (no un total), extrae los datos de estas columnas y proporciona la información en el siguiente formato, estrictamente, y solo el output, nada mas.

    Presenta los datos como una lista de diccionarios en Python, donde cada diccionario representa un artículo.
    No incluyas marcadores de código (```) en tu respuesta.

    Contenido del PDF:
    {texto_pdf}
    """

    with st.spinner("Extrayendo datos de ventas..."):
        respuesta = modelo.generate_content(
            prompt, generation_config=genai.types.GenerationConfig(temperature=0)
        )

    texto_limpio = (
        respuesta.text.strip().replace("```python", "").replace("```", "").strip()
    )

    try:
        datos = eval(texto_limpio)
        if isinstance(datos, list) and all(isinstance(item, dict) for item in datos):
            return datos
        else:
            raise ValueError(
                "La respuesta no tiene el formato esperado de una lista de diccionarios."
            )
    except Exception as e:
        st.error(f"Error al procesar la respuesta: {e}")
        st.text("Respuesta recibida:")
        st.code(texto_limpio)
        return []


# Función para generar tabla resumen


def generar_tabla_resumen(datos_ventas):
    if not datos_ventas:
        return None

    df = pd.DataFrame(datos_ventas)

    # Crear categorías para la clasificación
    def categorizar_venta(descripcion):
        if "VISITA" in descripcion.upper():
            return "Visitas"
        elif "APADRINAMENT" in descripcion.upper():
            return "Apadrinamiento"
        elif "DONACIÓ" in descripcion.upper():
            return "Donación"
        else:
            return f"Merchandising ({df['% Marge'][df['Descripció'] == descripcion].values[0]}% Marge"

    df["Tipo de venta"] = df["Descripció"].apply(categorizar_venta)

    # Convertir columnas numéricas a float
    for col in ["Base", "Import IVA", "PVP"]:
        df[col] = df[col].str.replace(",", ".").astype(float)

    # Agrupar los datos por Tipo de venta
    resumen = (
        df.groupby("Tipo de venta")
        .agg(Base=("Base", "sum"), IVA=("Import IVA", "sum"), PVP=("PVP", "sum"))
        .reset_index()
    )

    # Redondear los valores a 2 decimales
    resumen = resumen.round(2)

    # Calcular el total
    total = resumen.sum().round(2)
    total["Tipo de venta"] = "Total"

    # Añadir el total al resumen usando concat
    resumen = pd.concat([resumen, pd.DataFrame([total])], ignore_index=True)

    return resumen


# Función actualizada para mostrar resultados en tablas y ofrecer descarga


def mostrar_resultados(datos_ventas):
    if datos_ventas:
        # Mostrar tabla de todos los artículos
        st.header("Tabla de Todos los Artículos")
        df_articulos = pd.DataFrame(datos_ventas)
        st.dataframe(df_articulos, use_container_width=True)

        # Guardar CSV de artículos en la carpeta Output
        csv_filename = f"articulos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.join(output_dir, csv_filename)
        df_articulos.to_csv(csv_path, index=False)

        # Botón de descarga para la tabla de artículos
        csv_articulos = df_articulos.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Descargar CSV de artículos",
            data=csv_articulos,
            file_name=csv_filename,
            mime="text/csv",
        )

        # Mostrar tabla resumen de ventas
        resumen = generar_tabla_resumen(datos_ventas)
        if resumen is not None:
            st.header("Tabla Resumen de Ventas")
            st.dataframe(resumen, use_container_width=True)

            # Guardar CSV de resumen en la carpeta Output
            resumen_filename = (
                f"resumen_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            resumen_path = os.path.join(output_dir, resumen_filename)
            resumen.to_csv(resumen_path, index=False)

            # Botón de descarga para la tabla resumen
            csv_resumen = resumen.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Descargar CSV de resumen",
                data=csv_resumen,
                file_name=resumen_filename,
                mime="text/csv",
            )
        else:
            st.warning("No se pudieron generar los datos del resumen.")
    else:
        st.warning("No se encontraron datos de ventas para mostrar.")


# Función principal de la aplicación


def main():
    st.set_page_config(page_title="Extractor de Datos de Ventas PDF", layout="wide")

    st.title("📊 Extractor de Datos de Ventas PDF")

    st.markdown("""
    Esta aplicación te permite extraer datos de ventas de archivos PDF y visualizarlos de forma interactiva.
    
    ### Cómo usar:
    1. Sube tu archivo PDF
    2. Espera mientras procesamos y extraemos los datos
    3. Explora los resultados en las tablas de artículos y resumen
    4. Usa los botones de descarga para obtener los archivos CSV
    5. Los archivos CSV también se guardan automáticamente en la carpeta 'Output'
    """)

    archivo_pdf = st.file_uploader("Selecciona tu archivo PDF", type="pdf")

    if archivo_pdf is not None:
        texto_pdf = extraer_texto_de_pdf(archivo_pdf)

        if texto_pdf:
            datos_ventas = extraer_datos_ventas(texto_pdf)

            if datos_ventas:
                st.success("¡Datos extraídos con éxito!")

                st.header("Resultados")
                mostrar_resultados(datos_ventas)
            else:
                st.error("No se pudieron extraer datos de ventas del PDF.")
        else:
            st.error(
                "No se pudo extraer texto del PDF. Por favor, verifica que el archivo sea legible."
            )


if __name__ == "__main__":
    main()
