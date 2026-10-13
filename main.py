import streamlit as st, rasterio as rs, fileHandler as fH, rgb, ndviCalc, passa_alta
from rasterio.io import MemoryFile
from pathlib import Path

st.set_page_config(
    page_title="Deforestation Index Calculator",
    page_icon="🌎",
    layout="wide",
)

st.title("🌎 Deforestation Index Calculator")
st.write("Faça upload de um arquivo para iniciar o processamento.")

arquivo = st.file_uploader(
    "Selecione um arquivo",
    type=["tif"],
)

if arquivo is not None:
    try:
        with MemoryFile(arquivo.getvalue()) as memfile:
            with memfile.open() as src:
                info = fH.validar_geotiff(src)
                imagem_rgb = rgb.generate(src)
                ndvi = ndviCalc.processar_ndvi(src)
                laplaciano = passa_alta.processar_laplaciano(src)

    except (ValueError, rs.errors.RasterioError) as erro:
        st.error(f"Erro ao processar a imagem : {erro}")

    area_pixel = info["res"][0] * info["res"][1]

    with st.expander("Informações do Arquivo", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Visualização RGB")
            st.image(imagem_rgb, caption="Composição RGB do GeoTIFF", width=700)
        with col2:
            st.subheader("Propriedades do TIF")
            st.write(f"{info["crs"]}")
            st.write(f"Resolução Espacial: {info["res"]}")
            st.write(f"Área por Pixel: {area_pixel:.2f} m²")
            st.write(f"Bandas: {info["bands"]}")
            st.subheader("Análise dos Pixels")
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                st.metric("Dimensão", f"{info["width"]} x {info["height"]}")
                st.metric("Pixels Totais", f"{info["total_pixels"]:,}")
            with sub_col2:
                st.metric("Pixels Válidos", f"{info["valid_pixels"]:,}")
                st.metric("Pixels Inválidos", f"{info["invalid_pixels"]:,}")
            with sub_col3:
                st.metric("Percentual Válido", f"{info["valid_percentual"]:,}")
                st.metric("Percentual Inávlido", f"{info["invalid_percentual"]:,}")

    st.divider()

    st.header("Processamentos")

    pro_col1, pro_col2 = st.columns(2)

    with pro_col1:
        st.image(ndvi["imagem"], caption="Composição do Índice NDVI", width=800)

    with pro_col2:
        st.image(laplaciano["imagem"], caption="Composição da Magnitude do Laplaciano (Filtro Passa-Alta)", width=800)

#    with st.expander("NDVI", expanded=False):
#        st.image(ndvi["imagem"], caption="Composição do Índice NDVI", width=800)

#    with st.expander("Laplaciano", expanded=False):
#        st.image(laplaciano["imagem"], caption="Composição do Filtro Laplaciano", width=800)
