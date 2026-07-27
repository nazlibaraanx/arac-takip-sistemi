def kararli_sinifi_guncelle(sinif_oylari, takip_id, sinif, guven):
    """Karelik sınıf sıçramalarını güven ağırlıklı çoğunlukla süzer."""

    sinif_oylari[takip_id][sinif] += max(0.01, float(guven))
    return max(
        sinif_oylari[takip_id],
        key=sinif_oylari[takip_id].get
    )


def otomobil_boyutunda_mi(
    kutu,
    kare_sekli,
    min_alt_y_orani,
    min_genislik_orani,
    maks_genislik_orani,
    maks_boy_en_orani,
):
    """Kutunun önden görünen otomobil gövde oranında olup olmadığını döndürür."""

    if kutu is None or len(kutu) != 4 or len(kare_sekli) < 2:
        return False
    x1, y1, x2, y2 = map(float, kutu)
    kare_yuksekligi = float(kare_sekli[0])
    kare_genisligi = float(kare_sekli[1])
    genislik = x2 - x1
    yukseklik = y2 - y1
    if min(kare_yuksekligi, kare_genisligi, genislik, yukseklik) <= 0:
        return False

    return (
        y2 / kare_yuksekligi >= min_alt_y_orani
        and min_genislik_orani
        <= genislik / kare_genisligi
        <= maks_genislik_orani
        and yukseklik / genislik <= maks_boy_en_orani
    )


def genis_toplu_tasima_govdesi_mi(
    kutu,
    kare_sekli,
    min_alt_y_orani,
    min_genislik_orani,
    maks_boy_en_orani,
):
    """Yakındaki geniş minibüs/servis gövdesini otomobilden ayırır."""

    if kutu is None or len(kutu) != 4 or len(kare_sekli) < 2:
        return False
    x1, y1, x2, y2 = map(float, kutu)
    kare_yuksekligi = float(kare_sekli[0])
    kare_genisligi = float(kare_sekli[1])
    genislik = x2 - x1
    yukseklik = y2 - y1
    if min(kare_yuksekligi, kare_genisligi, genislik, yukseklik) <= 0:
        return False
    return (
        y2 / kare_yuksekligi >= min_alt_y_orani
        and genislik / kare_genisligi >= min_genislik_orani
        and yukseklik / genislik <= maks_boy_en_orani
    )


def servis_gibi_mi(
    kutu,
    kare_sekli,
    min_alt_y_orani,
    maks_genislik_orani,
    min_boy_en_orani
):
    """Tespit kutusunun servis/minibüs görünümüne uyup uymadığını döndürür."""

    if kutu is None or len(kutu) != 4 or len(kare_sekli) < 2:
        return False

    x1, y1, x2, y2 = map(float, kutu)
    kare_yuksekligi = float(kare_sekli[0])
    kare_genisligi = float(kare_sekli[1])
    kutu_genisligi = x2 - x1
    kutu_yuksekligi = y2 - y1

    if (
        kare_yuksekligi <= 0
        or kare_genisligi <= 0
        or kutu_genisligi <= 0
        or kutu_yuksekligi <= 0
    ):
        return False

    alt_y_orani = y2 / kare_yuksekligi
    genislik_orani = kutu_genisligi / kare_genisligi
    boy_en_orani = kutu_yuksekligi / kutu_genisligi

    return (
        alt_y_orani >= min_alt_y_orani
        and genislik_orani <= maks_genislik_orani
        and boy_en_orani >= min_boy_en_orani
    )


def toplu_tasima_duzeltmesi_gerekli_mi(
    model_sinifi,
    kutu,
    kare_sekli,
    min_alt_y_orani,
    maks_genislik_orani,
    min_boy_en_orani,
    otomobil_maks_genislik_orani
):
    """COCO'nun car/truck dediği servis-minibüs kutularını ayırır."""

    model_sinifi = str(model_sinifi).lower()
    if model_sinifi not in {"car", "truck"}:
        return False

    # Önden görünen sıradan otomobiller de yüksek görünebilir. `car` sonucu için
    # daha dar bir sınır kullanmak bu yanlış düzeltmeleri azaltır.
    secilen_maks_genislik = maks_genislik_orani
    if model_sinifi == "car":
        secilen_maks_genislik = min(
            maks_genislik_orani,
            otomobil_maks_genislik_orani
        )

    return servis_gibi_mi(
        kutu,
        kare_sekli,
        min_alt_y_orani,
        secilen_maks_genislik,
        min_boy_en_orani
    )
