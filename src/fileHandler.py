import numpy as np


def calcular_metricas_area(src, mascara_valida, mascara_classificada):
    """Calcula contagens, áreas e percentuais para uma máscara classificada."""
    if src.crs is None or not src.crs.is_projected:
        raise ValueError(
            "É necessário um CRS projetado para calcular áreas em m²."
        )

    unidade = (src.crs.linear_units or "").lower()
    if unidade not in ("metre", "meter", "metres", "meters"):
        raise ValueError(
            "O cálculo de áreas em m² exige que o CRS use metros."
        )

    mascara_valida = np.asarray(mascara_valida, dtype=bool)
    mascara_classificada = np.asarray(mascara_classificada, dtype=bool)

    if mascara_valida.shape != mascara_classificada.shape:
        raise ValueError("As máscaras de validade e classificação devem ter o mesmo tamanho.")

    # Uma classificação só conta quando o pixel também é válido.
    mascara_classificada = mascara_classificada & mascara_valida

    pixels_totais = src.width * src.height
    pixels_validos = int(np.count_nonzero(mascara_valida))
    pixels_classificados = int(np.count_nonzero(mascara_classificada))
    area_pixel_m2 = abs(src.res[0] * src.res[1])
    area_total_m2 = pixels_totais * area_pixel_m2
    area_valida_m2 = pixels_validos * area_pixel_m2
    area_classificada_m2 = pixels_classificados * area_pixel_m2

    return {
        "pixels_totais": pixels_totais,
        "pixels_validos": pixels_validos,
        "pixels_invalidos": pixels_totais - pixels_validos,
        "pixels_classificados": pixels_classificados,
        "area_pixel_m2": area_pixel_m2,
        "area_total_m2": area_total_m2,
        "area_total_km2": area_total_m2 / 1_000_000,
        "area_valida_m2": area_valida_m2,
        "area_valida_km2": area_valida_m2 / 1_000_000,
        "area_classificada_m2": area_classificada_m2,
        "area_classificada_km2": area_classificada_m2 / 1_000_000,
        "percentual_area_total": (
            pixels_classificados / pixels_totais * 100 if pixels_totais else 0.0
        ),
        "percentual_area_valida": (
            pixels_classificados / pixels_validos * 100 if pixels_validos else 0.0
        ),
    }


def validar_geotiff(src):
    # Verifica se a imagem possui bandas
    if src.count == 0:
        raise ValueError("O arquivo não possui bandas.")

    # Combina as bandas uma a uma para evitar manter a pilha de máscaras
    # inteira na memória ao mesmo tempo.
    mascara_valida = np.ones((src.height, src.width), dtype=bool)
    for banda in range(1, src.count + 1):
        mascara_valida &= src.read_masks(banda) > 0

    # Quantidade total de pixels espaciais
    total_pixels = src.width * src.height

    # Contagem de pixels válidos e inválidos
    pixels_validos = np.count_nonzero(mascara_valida)
    pixels_invalidos = total_pixels - pixels_validos

    # Percentuais
    percentual_validos = pixels_validos / total_pixels * 100 if total_pixels else 0.0
    percentual_invalidos = pixels_invalidos / total_pixels * 100 if total_pixels else 0.0

    # Metadados
    informacoes = {
        "width": src.width,
        "height": src.height,
        "bands": src.count,
        "res": src.res,
        "crs": str(src.crs),
        "total_pixels": total_pixels,
        "valid_pixels": pixels_validos,
        "invalid_pixels": pixels_invalidos,
        "valid_percentual": percentual_validos,
        "invalid_percentual": percentual_invalidos,
    }

    if pixels_validos == 0:
        raise ValueError(
            "A imagem não possui pixels válidos."
        )

    return informacoes
