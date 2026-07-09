import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# Configuración de la página
st.set_page_config(
    page_title="Visor de Barrido Espectrofotométrico",
    page_icon="📈",
    layout="wide"
)

# Estilo personalizado simple para dar apariencia limpia
st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📈 Análisis de Barrido Espectrofotométrico</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Carga archivos de espectrofotometría, visualiza y personaliza las curvas de absorbancia, y descarga reportes en Excel e imágenes de alta resolución.</div>', unsafe_allow_html=True)

# Barra lateral para carga de archivo y parámetros
with st.sidebar:
    st.header("1. Cargar Datos")
    uploaded_file = st.file_uploader(
        "Sube tu archivo CSV o TXT del espectrofotómetro",
        type=["csv", "txt"],
        help="Soporta archivos exportados delimitados por tabuladores (UTF-16 o UTF-8)."
    )

    st.divider()
    st.header("2. Personalizar Líneas de Interés")
    w1 = st.number_input("Longitud de onda 1 (nm)", min_value=190, max_value=1100, value=417, step=1)
    w2 = st.number_input("Longitud de onda 2 (nm)", min_value=190, max_value=1100, value=873, step=1)

    st.divider()
    st.header("3. Parámetros de la Gráfica")
    chart_title = st.text_input("Título de la gráfica", value="Barrido de Espectrofotometría")
    x_min, x_max = st.slider("Rango de Longitud de Onda (X)", 190, 1100, (190, 1100))
    y_max = st.slider("Máximo Absorbancia (Y)", 1.0, 10.0, 5.5, 0.5)

@st.cache_data
def load_data(file_bytes):
    # Intentar decodificar y leer con pandas (primero utf-16le como en el equipo, luego utf-8)
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), sep='\t', decimal=',', encoding='utf-16le')
    except Exception:
        df = pd.read_csv(io.BytesIO(file_bytes), sep='\t', decimal=',', encoding='utf-8')
    
    df.columns = df.columns.str.strip()
    return df

def generate_excel(resumen_df, full_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        resumen_df.to_excel(writer, sheet_name='Resumen_ABS', index=False)
        full_df.to_excel(writer, sheet_name='Datos_Completos', index=False)
    return output.getvalue()

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    try:
        df = load_data(file_bytes)
        
        # Identificar columna de longitud de onda
        col_x = [c for c in df.columns if 'wavelength' in c.lower() or 'longitud' in c.lower() or 'nm' in c.lower()]
        if not col_x:
            col_x = df.columns[0]
        else:
            col_x = col_x[0]

        # Columnas de absorbancia
        cols_abs = [c for c in df.columns if c != col_x]

        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader("Gráfica de Espectro")
            
            fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
            
            # Paleta de colores atractiva
            colors = ['#d62728', '#1f77b4', '#2ca02c', '#bcbd22', '#e377c2', '#17becf', '#8c564b', '#7f7f7f']
            
            for i, col in enumerate(cols_abs):
                color = colors[i % len(colors)]
                label_clean = col.replace('(Abs)', '').strip()
                ax.plot(df[col_x], df[col], label=label_clean, color=color, linewidth=1.8)

            # Líneas verticales
            ax.axvline(x=w1, color='#1E3A8A', linestyle='--', label=f'{w1} nm', linewidth=1.5)
            ax.text(w1 + 4, y_max * 0.9, str(w1), rotation=90, verticalalignment='top', color='#1E3A8A', fontweight='bold')

            ax.axvline(x=w2, color='#047857', linestyle='--', label=f'{w2} nm', linewidth=1.5)
            ax.text(w2 + 4, y_max * 0.9, str(w2), rotation=90, verticalalignment='top', color='#047857', fontweight='bold')

            ax.set_xlabel("Longitud de onda (nm)", fontweight='bold')
            ax.set_ylabel("Absorbancia (ABS)", fontweight='bold')
            ax.set_title(chart_title, fontweight='bold', pad=12)
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(0, y_max)
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
            plt.tight_layout()

            st.pyplot(fig)

            # Guardar gráfica en buffer para descarga
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)

            st.download_button(
                label="🖼️ Descargar Gráfica en Alta Calidad (PNG)",
                data=img_buffer,
                file_name="grafica_espectrofotometria.png",
                mime="image/png",
                use_container_width=True
            )

        with col2:
            st.subheader("Tabla Resumen de Picos")
            st.write(f"Valores de absorbancia medidos en **{w1} nm** y **{w2} nm**:")

            row_w1 = df.iloc[(df[col_x] - w1).abs().argsort()[:1]]
            row_w2 = df.iloc[(df[col_x] - w2).abs().argsort()[:1]]

            resumen_df = pd.DataFrame({
                'Ejemplo': [c.replace('(Abs)', '').strip() for c in cols_abs],
                f'ABS({w1})': [row_w1[c].values[0] for c in cols_abs],
                f'ABS({w2})': [row_w2[c].values[0] for c in cols_abs]
            })

            st.dataframe(resumen_df, use_container_width=True, hide_index=True)

            # Botón de descarga Excel
            excel_bytes = generate_excel(resumen_df, df)
            st.download_button(
                label="📊 Descargar Tabla y Datos en Excel (.xlsx)",
                data=excel_bytes,
                file_name="reporte_espectrofotometria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            st.divider()
            with st.expander("🔍 Ver todos los datos originales"):
                st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo. Verifica el formato del CSV. Detalle: {e}")

else:
    st.info("👈 Sube un archivo CSV desde la barra lateral izquierda para comenzar.")
