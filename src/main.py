import rasterio as rs
import streamlit as st
from rasterio.io import MemoryFile

import fileHandler as fH
import ndviCalc
import passa_alta
import rgb


st.set_page_config(
    page_title="Deforestation Index Calculator",
    page_icon="🌎",
    layout="wide",
)

st.title("🌎 Deforestation Index Calculator")
st.write("Faça upload de um arquivo GeoTIFF para analisar a cobertura da imagem.")

arquivo = st.file_uploader(
    "Selecione um arquivo",
    type=["tif", "tiff"],
)


def mostrar_metricas(resultados, rotulo_pixels, descricao):
    col_pixels, col_area, col_percentual = st.columns(3)
    with col_pixels:
        st.metric(rotulo_pixels, f"{resultados['pixels_classificados']:,}")
    with col_area:
        st.metric("Área classificada", f"{resultados['area_classificada_m2']:,.2f} m²")
        st.caption(f"{resultados['area_classificada_km2']:.6f} km²")
    with col_percentual:
        st.metric("Percentual da área total", f"{resultados['percentual_area_total']:.2f}%")
    st.caption(
        f"{descricao} Percentual sobre os pixels válidos: "
        f"{resultados['percentual_area_valida']:.2f}%."
    )


if arquivo is not None:
    limiar_col1, limiar_col2 = st.columns(2)
    with limiar_col1:
        limiar_ndvi = st.number_input(
            "Limiar do NDVI",
            value=0.2,
            step=0.05,
            format="%.2f",
            help="Pixels com NDVI abaixo deste valor entram na máscara.",
        )
    with limiar_col2:
        limiar_laplaciano = st.number_input(
            "Limiar do Laplaciano",
            min_value=0.0,
            value=30.0,
            step=1.0,
            format="%.1f",
            help="Pixels com magnitude igual ou acima deste valor entram na máscara.",
        )

    try:
        with MemoryFile(arquivo.getvalue()) as memfile:
            with memfile.open() as src:
                info = fH.validar_geotiff(src)
                imagem_rgb, mascara_rgb = rgb.generate_composicao(src)
                ndvi = ndviCalc.processar_ndvi(src, limiar=limiar_ndvi)
                laplaciano = passa_alta.processar_laplaciano(
                    src,
                    limiar=limiar_laplaciano,
                    imagem_rgb=imagem_rgb,
                    mascara_valida=mascara_rgb,
                )
    except (ValueError, rs.errors.RasterioError) as erro:
        st.error(f"Erro ao processar a imagem: {erro}")
        st.stop()

    area_pixel = abs(info["res"][0] * info["res"][1])

    with st.expander("Informações do arquivo", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Visualização RGB")
            st.image(imagem_rgb, caption="Composição RGB do GeoTIFF", use_container_width=True)

        with col2:
            st.subheader("Propriedades do GeoTIFF")
            st.write(f"CRS: {info['crs']}")
            st.write(f"Resolução espacial: {info['res']}")
            st.write(f"Área por pixel: {area_pixel:.2f} m²")
            st.write(f"Bandas: {info['bands']}")
            st.subheader("Pixels da imagem")

            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                st.metric("Dimensão", f"{info['width']} × {info['height']}")
                st.metric("Pixels totais", f"{info['total_pixels']:,}")
            with sub_col2:
                st.metric("Pixels válidos", f"{info['valid_pixels']:,}")
                st.metric("Pixels inválidos", f"{info['invalid_pixels']:,}")
            with sub_col3:
                st.metric("Percentual válido", f"{info['valid_percentual']:.2f}%")
                st.metric("Percentual inválido", f"{info['invalid_percentual']:.2f}%")

    st.divider()
    st.header("Resultados dos processamentos")

    pro_col1, pro_col2 = st.columns(2)

    with pro_col1:
        st.subheader("NDVI")
        st.image(ndvi["imagem"], caption="Composição do índice NDVI", use_container_width=True)
        mostrar_metricas(
            ndvi,
            f"Pixels com NDVI < {ndvi['limiar']}",
            "A área é uma estimativa de pixels potencialmente sem vegetação pelo limiar NDVI.",
        )

    with pro_col2:
        st.subheader("Magnitude do Laplaciano")
        st.image(
            laplaciano["imagem"],
            caption="Magnitude do filtro passa-alta Laplaciano",
            use_container_width=True,
        )
        mostrar_metricas(
            laplaciano,
            f"Pixels com magnitude ≥ {laplaciano['limiar']:g}",
            "Área estimada a partir da máscara de pixels acima do limiar do Laplaciano.",
        )
