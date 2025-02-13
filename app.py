import os
import streamlit as st
import google.generativeai as genai
import PyPDF2
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import io
import xlsxwriter

# Cargar la API key desde el archivo .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("No se encontró la GOOGLE_API_KEY en el archivo .env")
    st.stop()

genai.configure(api_key=api_key)


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


def main():
    st.set_page_config(
        page_title="Asistente de Ventas - Arantxa",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Personalización del header
    st.title("👋 ¡Hola Arantxa!")
    st.markdown("""
    Esta aplicación está diseñada especialmente para ayudarte a procesar los datos de ventas de manera más eficiente.
    Simplemente sube tu PDF y podrás visualizar y descargar los datos en formato Excel.
    """)

    # Sidebar con instrucciones
    with st.sidebar:
        st.header("📝 Instrucciones")
        st.markdown("""
        1. Sube tu archivo PDF de ventas
        2. Revisa los datos extraídos en la tabla
        3. Si todo está correcto, descarga el archivo Excel
        """)
        st.markdown("---")
        st.markdown(
            "💡 **Tip**: Puedes ordenar la tabla haciendo clic en los encabezados"
        )

    archivo_pdf = st.file_uploader("📄 Selecciona tu archivo PDF de ventas", type="pdf")

    if archivo_pdf is not None:
        texto_pdf = extraer_texto_de_pdf(archivo_pdf)
        if texto_pdf:
            datos_ventas = extraer_datos_ventas(texto_pdf)
            if datos_ventas:
                st.success("✨ ¡Datos extraídos correctamente!")

                # Crear DataFrame y mostrar previsualización
                df_articulos = pd.DataFrame(datos_ventas)

                # Mostrar la tabla con estilo
                st.subheader("📊 Tabla de Artículos")
                st.dataframe(df_articulos, use_container_width=True, hide_index=True)

                # Botón de descarga Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_articulos.to_excel(writer, sheet_name="Artículos", index=False)

                excel_data = output.getvalue()
                st.download_button(
                    label="📥 Descargar datos en Excel",
                    data=excel_data,
                    file_name=f"ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            else:
                st.error("❌ No se pudieron extraer datos de ventas.")
        else:
            st.error("❌ No se pudo extraer texto del PDF.")


if __name__ == "__main__":
    main()
