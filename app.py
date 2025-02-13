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
    modelo = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")  # O el modelo que uses
    prompt = f"""
Extrae los datos de ventas para cada artículo del documento PDF proporcionado.  Ignora las filas que contengan totales (como "Total Client" o "Total Vendes") y cualquier texto que no sea parte de la tabla principal de artículos (fechas, encabezados de página, etc.).  Concéntrate en extraer datos de las siguientes columnas:

- **Article:**  El código o número de identificación del artículo.
- **Descripció:** La descripción completa del artículo.
- **Quantitat:**  La cantidad vendida.  Entero. Incluye la unidad "U".
- **Import:**  El importe total de venta.  Número con decimales (coma).
- **Cost:** El coste del artículo. Número con decimales (coma).
- **% Marge:** El porcentaje de margen. Número con decimales (coma).

Formato de salida (lista de diccionarios en Python, sin marcadores de código):

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
            raise ValueError("La respuesta no tiene el formato esperado.")
    except Exception as e:
        st.error(f"Error al procesar la respuesta: {e}")
        st.text("Respuesta recibida:")
        st.code(texto_limpio)  # Mostrar respuesta para depuración
        return []


# Función para generar tabla resumen (MODIFICADA para guardar directamente)
def generar_y_guardar_tabla_resumen(datos_ventas, output_dir):
    if not datos_ventas:
        return

    df = pd.DataFrame(datos_ventas)

    # Categorización (adaptar según sea necesario)
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

    # Conversión de tipos (¡IMPORTANTE! Asegurarse de que los nombres de columna coinciden)
    for col in [
        "Import",
        "Cost",
    ]:  # Asegurate de que los nombres de las columnas son correctos
        if col in df.columns:  # Verificar si la columna existe
            df[col] = df[col].astype(str).str.replace(",", ".").astype(float)

    # Agrupación y resumen
    resumen = (
        df.groupby("Tipo de venta")
        .agg(
            Import=("Import", "sum"), Cost=("Cost", "sum")
        )  # Los campos a sumar en la agrupación
        .reset_index()
    )
    resumen = resumen.round(2)

    # Calcular el total
    total = resumen.sum(numeric_only=True).round(2)  # Suma solo las columnas numéricas
    total["Tipo de venta"] = "Total"
    resumen = pd.concat([resumen, pd.DataFrame([total])], ignore_index=True)

    # Guardar CSV de resumen
    resumen_filename = f"resumen_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    resumen_path = os.path.join(output_dir, resumen_filename)
    resumen.to_csv(resumen_path, index=False)
    return resumen_filename  # Devolver el nombre del archivo


# Función principal de la aplicación (SIMPLIFICADA)
def main():
    st.set_page_config(page_title="Extractor de Datos de Ventas PDF", layout="wide")
    st.title("Extractor de Datos de Ventas PDF")
    st.markdown("""
    Sube un PDF para extraer los datos de ventas y generar archivos CSV.
    Los archivos se guardarán en la carpeta 'Output'.
    """)

    archivo_pdf = st.file_uploader("Selecciona tu archivo PDF", type="pdf")

    if archivo_pdf is not None:
        texto_pdf = extraer_texto_de_pdf(archivo_pdf)
        if texto_pdf:
            datos_ventas = extraer_datos_ventas(texto_pdf)
            if datos_ventas:
                st.success("Datos extraídos. Generando archivos CSV...")

                # Guardar CSV de artículos
                articulos_filename = (
                    f"articulos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                articulos_path = os.path.join(output_dir, articulos_filename)
                df_articulos = pd.DataFrame(datos_ventas)
                df_articulos.to_csv(articulos_path, index=False)
                st.write(f"Archivo de artículos guardado: {articulos_filename}")

                # Generar y guardar tabla resumen
                nombre_archivo_resumen = generar_y_guardar_tabla_resumen(
                    datos_ventas, output_dir
                )
                if nombre_archivo_resumen:
                    st.write(f"Archivo de resumen guardado: {nombre_archivo_resumen}")

            else:
                st.error("No se pudieron extraer datos de ventas.")
        else:
            st.error("No se pudo extraer texto del PDF.")


if __name__ == "__main__":
    main()
