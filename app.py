import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import itertools
import random
import google.generativeai as genai

# ==========================================
# GEMINI API AYARI
# ==========================================
API_KEY = "AIzaSyDUNxlbI32_-9rQPwl6_hDjHKHXlX30EcA"

# ==========================================
# API YAPILANDIRMA KONTROLÜ
# ==========================================
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.warning("Gemini API Key henüz tanımlanmadı. AI Degerlendirme modu calismayacaktir.")

# Sayfa ayarlari
st.set_page_config(page_title="LogiMind - Rota Optimizasyonu", layout="wide")

st.title("LogiMind: Rota ve Yuk Optimizasyon Sistemi")
st.write("Lojistik operasyonlar icin karar destek uygulamasi - BTK Akademi Hackathon 2026")

# Sidebar - Parametreler
st.sidebar.header("Parametreler")
arac_sayisi = st.sidebar.slider("Arac Sayisi", 1, 5, 2)
arac_kapasitesi = st.sidebar.slider("Arac Kapasitesi", 5, 50, 15)
trafik = st.sidebar.slider("Trafik Katsayisi", 1.0, 2.0, 1.0)

# Sabit Musteri Verileri
tum_musteriler = {
    "A": (5, 10, 3), "B": (-3, 8, 5), "C": (12, 2, 4),
    "D": (8, -4, 2), "E": (-6, -5, 6), "F": (2, 15, 3),
    "G": (14, -1, 5), "H": (-2, -9, 2), "I": (7, 7, 4)
}

# Mesafe Hesaplama Fonksiyonu
def mesafe(p1, p2):
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1]) * trafik

# Kiyaslama icin Rastgele Rota Hesaplama Fonksiyonu
def random_mesafe(df_input):
    noktalar = df_input.iloc[1:].to_dict('records')
    random.shuffle(noktalar)
    yol = [(0,0)] + [(n["x"], n["y"]) for n in noktalar] + [(0,0)]
    return sum(mesafe(yol[i], yol[i+1]) for i in range(len(yol)-1))

# Gemini Yapay Zeka Raporlama Fonksiyonu
def gemini_yorumla(arac_sayisi, toplam_mesafe, tasarruf, trafik):
    import requests
    import json
    try:
        prompt = f"""
        Sen bir lojistik ve rota optimizasyon uzmanısın. 
        Asagidaki verileri analiz et ve jüriyi etkileyecek profesyonel bir yonetici ozeti cikar:

        Aktif Arac Sayisi: {arac_sayisi}
        Optimize Edilmis Toplam Mesafe: {toplam_mesafe:.2f} km
        Rastgele Rotaya Gore Elde Edilen Tasarruf: %{tasarruf:.1f}
        Mevcut Trafik Yogunluk Katsayisi: {trafik}

        Lutfen cok kisa, profesyonel ve net 3 madde halinde sunlari yaz:
        - Sistemin sagladigi genel verimlilik duzeyi (LogiMind platformunun basarisi)
        - Saha operasyonlari ve suruculer icin 1 adet pratik lojistik oneri
        - Bu optimizasyonun karbon salinimi (yesil lojistik) ve sirket maliyetlerine etkisi
        """
        
        # Doğrudan kararlı v1 API endpoint'ine istek atıyoruz
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AI Degerlendirmesi su an olusturulamadi. Hata: {e}"

# Musteri Secim Ekrani
st.subheader("Musteri Secimi ve Dagitim Talepleri")

secili = st.multiselect(
    "Teslimat yapilacak musterileri secin:",
    list(tum_musteriler.keys()),
    default=["A","B","C","D","E"]
)

if len(secili) == 0:
    st.warning("Lutfen rota olusturabilmek icin en az bir musteri secin.")
    st.stop()

# Tablo Verisi Hazirlama
data = [{"name": "Depo", "x": 0, "y": 0, "demand": 0}]
for m in secili:
    x, y, d = tum_musteriler[m]
    data.append({"name": m, "x": x, "y": y, "demand": d})

df = pd.DataFrame(data)
st.dataframe(df)

# Optimizasyon Butonu ve Ana Algoritma
if st.button("Rota ve Yuk Dagitimini Optimize Et"):

    toplam_talep = df["demand"].sum()
    toplam_kapasite = arac_sayisi * arac_kapasitesi

    if toplam_talep > toplam_kapasite:
        st.error(f"Hata: Toplam musteri talebi ({toplam_talep}), mevcut araclarin toplam kapasitesini ({toplam_kapasite}) asiyor! Lutfen arac sayisini ellerinizle veya kapasitesini artirin.")
        st.stop()

    musteri_listesi = data[1:]
    arac_rotalari = {i: [] for i in range(arac_sayisi)}
    arac_yukleri = {i: 0 for i in range(arac_sayisi)}

    # Akilli Yuk Dagitimi
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

    # Atanan Musteriler Icin En Kisa Yol Siralamasi
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
            name=f"Arac {a+1} (Yuk: {arac_yukleri[a]}/{arac_kapasitesi})",
            line=dict(color=renkler[a % len(renkler)], width=3),
            marker=dict(size=10),
            text=isimler,
            hoverinfo="text+name"
        ))

    # Depo Noktasini Haritada Belirginlestirme
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers", name="Merkez Depo",
        marker=dict(color="black", size=15, symbol="square"), text=["ANA DEPO"]
    ))

    fig.update_layout(
        title="Arac Dagitim ve Rota Haritasi",
        xaxis_title="X Koordinati", yaxis_title="Y Koordinati", hovermode="closest"
    )

    # Performans Metrikleri
    r_mesafe = random_mesafe(df)
    tasarruf = ((r_mesafe - toplam_mesafe) / r_mesafe) * 100 if r_mesafe > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Geleneksel (Rastgele Rota)", f"{r_mesafe:.2f} km")
    col2.metric("LogiMind (Optimize Rota)", f"{toplam_mesafe:.2f} km")
    col3.metric("Saglanan Karbon/Yol Tasarrufu", f"%{tasarruf:.1f}")

    # Haritayi Goster
    st.plotly_chart(fig, use_container_width=True)

    # AI Yorum Alani
    st.subheader("LogiMind Yapay Zeka Degerlendirmesi")
    with st.spinner("Gemini rapor hazirliyor..."):
        ai_raporu = gemini_yorumla(arac_sayisi, toplam_mesafe, tasarruf, trafik)
        st.info(ai_raporu)
