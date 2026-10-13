
import numpy as np
import matplotlib.pyplot as plt


def processar_laplaciano(
    src,
    limiar=30.0,
    banda_azul=1,
    banda_verde=2,
    banda_vermelha=3,
):
    """
    Aplica o filtro passa-alta Laplaciano sobre uma composição RGB.

    Etapas:
    1. Valida as bandas de entrada.
    2. Identifica pixels válidos no GeoTIFF.
    3. Converte as bandas para uma imagem RGB uint8.
    4. Calcula o Laplaciano manualmente com NumPy.
    5. Gera uma máscara dos pixels cuja resposta supera o limiar.
    6. Retorna a imagem e as máscaras para processamento posterior.

    O limiar é aplicado à magnitude absoluta do Laplaciano.
    """

    # 1. Validar as bandas de entrada
    bandas = [banda_azul, banda_verde, banda_vermelha]

    if min(bandas) < 1 or max(bandas) > src.count:
        raise ValueError(
            f"As bandas solicitadas devem estar entre 1 e {src.count}."
        )

    if limiar < 0:
        raise ValueError("O limiar não pode ser negativo.")

    # 2. Ler as bandas originais
    azul = src.read(banda_azul).astype(np.float32)
    verde = src.read(banda_verde).astype(np.float32)
    vermelho = src.read(banda_vermelha).astype(np.float32)

    # Combinar as máscaras de validade das três bandas
    mascara_valida = (
        (src.read_masks(banda_azul) > 0)
        & (src.read_masks(banda_verde) > 0)
        & (src.read_masks(banda_vermelha) > 0)
        & np.isfinite(azul)
        & np.isfinite(verde)
        & np.isfinite(vermelho)
    )

    pixels_validos = np.count_nonzero(mascara_valida)

    if pixels_validos == 0:
        raise ValueError(
            "O GeoTIFF não possui pixels válidos nas bandas selecionadas."
        )

    # 3. Converter as bandas para RGB de 8 bits.
    # A normalização usa os percentis 2 e 98, desconsiderando
    # os pixels inválidos.
    def normalizar_banda(banda):
        valores = banda[mascara_valida]

        minimo, maximo = np.percentile(valores, [2, 98])

        normalizada = np.zeros(banda.shape, dtype=np.uint8)

        if maximo > minimo:
            escala = (
                (banda[mascara_valida] - minimo)
                / (maximo - minimo)
            )

            normalizada[mascara_valida] = np.clip(
                escala * 255,
                0,
                255
            ).astype(np.uint8)

        return normalizada

    azul_rgb = normalizar_banda(azul)
    verde_rgb = normalizar_banda(verde)
    vermelho_rgb = normalizar_banda(vermelho)

    imagem_rgb = np.stack(
        [vermelho_rgb, verde_rgb, azul_rgb],
        axis=2
    )

    # 4. Obter o canal V do modelo HSV.
    # V equivale ao maior valor entre os canais RGB.
    canal_v = np.max(imagem_rgb, axis=2).astype(np.float32)

    # 5. Aplicar manualmente o Laplaciano 3x3:
    #
    # -1  -1  -1
    # -1   8  -1
    # -1  -1  -1
    #
    # O preenchimento replica os valores das bordas.
    imagem_padded = np.pad(
        canal_v,
        pad_width=1,
        mode="edge"
    )

    centro = imagem_padded[1:-1, 1:-1]

    vizinhos = (
        imagem_padded[:-2, :-2]
        + imagem_padded[:-2, 1:-1]
        + imagem_padded[:-2, 2:]
        + imagem_padded[1:-1, :-2]
        + imagem_padded[1:-1, 2:]
        + imagem_padded[2:, :-2]
        + imagem_padded[2:, 1:-1]
        + imagem_padded[2:, 2:]
    )

    resposta = (8 * centro) - vizinhos

    # Considerar a magnitude da resposta, independentemente do sinal
    magnitude = np.abs(resposta)

    # 6. Classificar pixels, excluindo pixels inválidos
    mascara_laplaciano = (
        mascara_valida
        & (magnitude >= limiar)
    )

    # 7. Gerar a imagem visual do filtro
    magnitude_visual = np.ma.masked_where(
        ~mascara_valida,
        magnitude
    )

    valores_magnitude = magnitude[mascara_valida]
    maximo_visual = max(
        float(np.percentile(valores_magnitude, 99)),
        1.0
    )

    fig, ax = plt.subplots(figsize=(10, 7))

    imagem_plot = ax.imshow(
        magnitude_visual,
        cmap="inferno",
        vmin=0,
        vmax=maximo_visual
    )

    fig.colorbar(
        imagem_plot,
        ax=ax,
        label="Magnitude do Laplaciano"
    )

    ax.set_title("Filtro passa-alta Laplaciano")
    ax.axis("off")
    fig.tight_layout()

    fig.canvas.draw()

    imagem_saida = np.asarray(
        fig.canvas.buffer_rgba()
    )[:, :, :3].copy()

    plt.close(fig)

    # 8. Retornar os resultados
    return {
        "imagem": imagem_saida,
        "imagem_rgb": imagem_rgb,
        "resposta": magnitude,
        "mascara_valida": mascara_valida,
        "mascara_laplaciano": mascara_laplaciano,
        "pixels_validos": pixels_validos,
        "limiar": limiar,
    }
