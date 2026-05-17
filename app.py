import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import itertools

# Sayfa Yapilandirmasi
st.set_page_config(page_title="LogiMind - Lojistik Optimizasyon Sistemi", layout="wide")

st.title("LogiMind: Akilli Rota ve Yuk Optimizasyon Platformu")
st.write("Musteri bazli secim ve dinamik yuk/kapasite kontrol paneli.")

# Kontrol Paneli (Sidebar)
st.sidebar.header("Sistem Parametreleri")
arac_sayisi = st.sidebar.slider("Aktif Arac Sayisi", min_value=0, max_value=5, value=2)
arac_kapasitesi = st.sidebar.slider("Arac Kapasitesi (KG)", min_value=5, max_value=100, value=15)

# Sabit Veri Havuzu
tüm_musteriler = {
    "Musteri A": {"X": 5, "Y": 10, "Talep": 3},
    "Musteri B": {"X": -3, "Y": 8, "Talep": 5},
    "Musteri C": {"X": 12, "Y": 2, "Talep": 4},
    "Musteri D": {"X": 8, "Y": -4, "Talep": 2},
    "Musteri E": {"X": -6, "Y": -5, "Talep": 6},
    "Musteri F": {"X": 2, "Y": 15, "Talep": 3},
    "Musteri G": {"X": 14, "Y": -1, "Talep": 5},
    "Musteri H": {"X": -2, "Y": -9, "Talep": 2},
    "Musteri I": {"X": 7, "Y": 7, "Talep": 4}
}

# 1. Kural: Arac Sayisi 0 ise direkt engelle
if arac_sayisi == 0:
    st.error("Hata: Aktif arac sayisi 0 oldugunda tasima yapilamaz, rota olusturulamadi. Lutfen en az 1 arac seciniz.")
else:
    # Dinamik Musteri Secim Kutusu
    st.subheader("Siparis Veren Musterileri Seciniz")
    secilen_isimler = st.multiselect(
        "Bugun teslimat yapilacak musterileri listeden isaretleyin:",
        options=list(tüm_musteriler.keys()),
        default=["Musteri A", "Musteri G", "Musteri D", "Musteri C", "Musteri E"]
    )

    # Secilen verilerden dinamik tablo olusturma
    tablo_verisi = []
    tablo_verisi.append({"Musteri_Adi": "Depo (Merkez)", "X_Koordinati": 0, "Y_Koordinati": 0, "Talep_KG": 0})
    
    for m in secilen_isimler:
        tablo_verisi.append({
            "Musteri_Adi": m,
            "X_Koordinati": tüm_musteriler[m]["X"],
            "Y_Koordinati": tüm_musteriler[m]["Y"],
            "Talep_KG": tüm_musteriler[m]["Talep"]
        })
        
    df = pd.DataFrame(tablo_verisi)
    
    st.subheader("Mevcut Siparis ve Dagitim Verileri")
    st.dataframe(df, use_container_width=True)

    # Optimizasyon Butonu
    if st.button("Rotalari Optimize Et", type="primary"):
        if len(secilen_isimler) == 0:
            st.warning("Lutfen rota olusturabilmek icin en az bir musteri seciniz.")
        else:
            toplam_talep = df["Talep_KG"].sum()
            toplam_kapasite = arac_sayisi * arac_kapasitesi
            
            # 2. Kural: Kapasite kontrolu
            if toplam_talep > toplam_kapasite:
                st.error(f"Hata: Yetersiz Kapasite. Secilen musterilerin toplam talebi {toplam_talep} KG, fakat {arac_sayisi} aracinizin toplam tasima kapasitesi {toplam_kapasite} KG. Lutfen parametreleri guncelleyin.")
            else:
                with st.spinner("Dengeli ve en kisa optimum rotalar hesaplaniyor..."):
                    
                    # Matematiksel Mesafe Hesaplama Fonksiyonu
                    def mesafe_bul(p1, p2):
                        return np.hypot(p1[0] - p2[0], p1[1] - p2[1])

                    # Musteri listesini kopyala
                    musteri_listesi = tablo_verisi[1:].copy()
                    
                    # Bos arac rotalari hazırlığı
                    arac_rotalari = {i: [] for i in range(arac_sayisi)}
                    arac_yukleri = {i: 0 for i in range(arac_sayisi)}
                    
                    # YUKLERI ARACLAR ARASINDA DENGELI PAYLASTIRMA ALGORITMASI
                    # Musterileri yakınlıklarına ve arac kapasitelerine gore sirayla boler
                    for m_verisi in musteri_listesi:
                        uygun_araclar = []
                        for a_id in range(arac_sayisi):
                            if arac_yukleri[a_id] + m_verisi["Talep_KG"] <= arac_kapasitesi:
                                # Aracin son konumuna olan mesafesini olc
                                if len(arac_rotalari[a_id]) == 0:
                                    son_konum = (0, 0)
                                else:
                                    son_konum = (arac_rotalari[a_id][-1]["X_Koordinati"], arac_rotalari[a_id][-1]["Y_Koordinati"])
                                
                                m_konum = (m_verisi["X_Koordinati"], m_verisi["Y_Koordinati"])
                                d = mesafe_bul(son_konum, m_konum)
                                uygun_araclar.append((a_id, d))
                        
                        if
