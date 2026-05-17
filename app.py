import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import itertools
import random
import requests
import json

# ==========================================
# GEMINI API AYARI (Yeni Oluşturduğun Anahtar)
# ==========================================
API_KEY = "AIzaSyCAZMZqB5SIaSK4IK-a_dzAyVXQzYag5HU"

# Sayfa ayarları
st.set_page_config(page_title="LogiMind - Rota Optimizasyonu", layout="wide")

st.title("LogiMind: Rota ve Yük Optimizasyon Sistemi")
st.write("Lojistik operasyonlar için karar destek uygulaması - BTK Akademi Hackathon 2026")

# Sidebar - Parametreler
st.sidebar.header("Parametreler")
arac_sayisi = st.sidebar.slider("Araç Sayısı", 1, 5, 2)
arac_kapasitesi = st.sidebar.slider("Araç Kapasitesi", 5, 50, 15)
trafik = st.sidebar.slider("Trafik Katsayısı", 1.0, 2.0, 1.0)

# Sabit Müşteri Verileri
tum_musteriler = {
    "A": (5, 10, 3), "B": (-3, 8, 5), "C": (12, 2, 4),
    "D": (8, -4, 2), "E": (-6, -5, 6), "F": (2, 15, 3),
    "G": (14, -1, 5), "H": (-2, -9, 2), "I": (7, 7, 4)
}

# Mesafe Hesaplama Fonksiyonu
def mesafe(p1, p2):
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1]) * trafik

# Kıyaslama için Rastgele Rota Hesaplama Fonksiyonu
def random_mesafe(df_input):
    noktalar = df_input.iloc[1:].to_dict('records')
    random.shuffle(noktalar)
    yol = [(0,0)] + [(n["x"], n["y"]) for n in noktalar] + [(0,0)]
    return sum(mesafe(yol[i], yol[i+1]) for i in range(len(yol)-1))

# Kütüphanesiz Doğrudan HTTP İstekli Gemini Fonksiyonu
def gemini_yorumla(arac_sayisi, toplam_mesafe, tasarruf, trafik):
    try:
        prompt = f"""
        Sen bir lojistik ve rota optimizasyon uzmanısın. 
        Aşağıdaki verileri analiz et ve jüriyi etkileyecek profesyonel bir yönetici özeti çıkar:

        Aktif Araç Sayısı: {arac_sayisi}
        Optimize Edilmiş Toplam Mesafe: {toplam_mesafe:.2f} km
        Rastgele Rotaya Göre Elde Edilen Tasarruf: %{tasarruf:.1f}
        Mevcut Trafik Yoğunluk Katsayısı: {trafik}

        Lütfen çok kısa, profesyonel ve net 3 madde halinde şunları yaz:
        - Sistemin sağladığı genel verimlilik düzeyi (LogiMind platformunun başarısı)
        - Saha operasyonları ve sürücüler için 1 adet pratik lojistik öneri
        - Bu optimizasyonun karbon salınımı (yeşil lojistik) ve şirket maliyetlerine etkisi
        """
        
        # En kararlı saf v1 API sürümü ve direkt model adı
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        
        if 'error' in res_json:
            return f"Google API Hatası: {res_json['error']['message']}"
            
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AI Değerlendirmesi şu an oluşturulamadı. Detay: {e}"

# Müşteri Seçim Ekranı
st.subheader("Müşteri Seçimi ve Dağıtım Talepleri")

secili = st.multiselect(
    "Teslimat yapılacak müşterileri seçin:",
    list(tum_musteriler.keys()),
    default=["A","B","C","D","E"]
)

if len(secili) == 0:
    st.warning("Lütfen rota oluşturabilmek için en az bir müşteri seçin.")
    st.stop()

# Tablo Verisi Hazırlama
data = [{"name": "Depo", "x": 0, "y": 0, "demand": 0}]
for m in secili:
    x, y, d = tum_musteriler[m]
    data.append({"name": m, "x": x, "y": y, "demand": d})

df = pd.DataFrame(data)
st.dataframe(df)

# Optimizasyon Butonu ve Ana Algoritma
if st.button("Rota ve Yük Dağıtımını Optimize Et"):

    toplam_talep = df["demand"].sum()
    toplam_kapasite = arac_sayisi * arac_kapasitesi

    if toplam_talep > toplam_kapasite:
        st.error(f"Hata: Toplam müşteri talebi ({toplam_talep}), mevcut araçların toplam kapasitesini ({toplam_kapasite}) aşıyor! Lütfen araç sayısını veya kapasitesini artırın.")
        st.stop()

    musteri_listesi = data[1:]
    arac_rotalari = {i: [] for i in range(arac_sayisi)}
    arac_yukleri = {i: 0 for i in range(arac_sayisi)}

    # Akıllı Yük Dağıtımı
    for m in musteri_listesi:
        uygun_araclar = []
        for a in range(arac_sayisi):
            if arac_yukleri[a] + m["demand"] <= arac_kapasitesi:
                if len(arac_rotalari[a]) == 0:
                    son_konum = (0,0)
                else:
                    son_konum = (arac_rotalari[a][-1]["x"], arac_rotalari[a][-1]["y"])
                
                d = mesafe(son_konum, (m["x"], m["y"]))
                uygun_araclar.append((a, d))

        if uygun_araclar:
            uygun_araclar.sort(key=lambda x: x[1])
            secilen_arac = uygun_araclar[0][0]
        else:
            secilen_arac = min(arac_yukleri, key=arac_yukleri.get)

        arac_rotalari[secilen_arac].append(m)
        arac_yukleri[secilen_arac] += m["demand"]

    toplam_mesafe = 0
    fig = go.Figure()
    renkler = ["#FF4B4B", "#1C83E1", "#00D4B2", "#7D4BFF", "#FFB64B"]

    # Atanan Müşteriler İçin En Kısa Yol Sıralaması
    for a in range(arac_sayisi):
        duraklar = arac_rotalari[a]
        if not duraklar:
            continue

        en_iyi_yol_sirasi = None
        en_kisa_arac_mesafesi = float("inf")

        for perm in itertools.permutations(duraklar):
            yol = [(0,0)] + [(d["x"], d["y"]) for d in perm] + [(0,0)]
            m_skor = sum(mesafe(yol[i], yol[i+1]) for i in range(len(yol)-1))

            if m_skor < en_kisa_arac_mesafesi:
                en_kisa_arac_mesafesi = m_skor
                en_iyi_yol_sirasi = perm

        toplam_mesafe += en_kisa_arac_mesafesi

        x_koordinatlari = [0] + [d["x"] for d in en_iyi_yol_sirasi] + [0]
        y_koordinatlari = [0] + [d["y"] for d in en_iyi_yol_sirasi] + [0]
        isimler = ["Depo"] + [d["name"] for d in en_iyi_yol_sirasi] + ["Depo"]

        fig.add_trace(go.Scatter(
            x=x_koordinatlari,
            y=y_koordinatlari,
            mode="lines+markers",
            name=f"Araç {a+1} (Yük: {arac_yukleri[a]}/{arac_kapasitesi})",
            line=dict(color=renkler[a % len(renkler)], width=3),
            marker=dict(size=10),
            text=isimler,
            hoverinfo="text+name"
        ))

    # Depo Noktasını Haritada Belirginleştirme
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers", name="Merkez Depo",
        marker=dict(color="black", size=15, symbol="square"), text=["ANA DEPO"]
    ))

    fig.update_layout(
        title="Araç Dağıtım ve Rota Haritası",
        xaxis_title="X Koordinatı", yaxis_title="Y Koordinatı", hovermode="closest"
    )

    # Performans Metrikleri
    r_mesafe = random_mesafe(df)
    tasarruf = ((r_mesafe - toplam_mesafe) / r_mesafe) * 100 if r_mesafe > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Geleneksel (Rastgele Rota)", f"{r_mesafe:.2f} km")
    col2.metric("LogiMind (Optimize Rota)", f"{toplam_mesafe:.2f} km")
    col3.metric("Sağlanan Karbon/Yol Tasarrufu", f"%{tasarruf:.1f}")

    # Haritayı Göster
    st.plotly_chart(fig, use_container_width=True)

    # AI Yorum Alanı
    st.subheader("LogiMind Yapay Zeka Değerlendirmesi")
    with st.spinner("Gemini rapor hazırlıyor..."):
        ai_raporu = gemini_yorumla(arac_sayisi, toplam_mesafe, tasarruf, trafik)
        st.info(ai_raporu)
