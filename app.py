import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import itertools
import random
import google.generativeai as genai

# -----------------------------
# API KEY (Streamlit Secrets)
# -----------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# -----------------------------
# SAYFA AYARLARI
# -----------------------------
st.set_page_config(page_title="LogiMind - Rota Optimizasyonu", layout="wide")

st.title("LogiMind: Rota ve Yük Optimizasyon Sistemi")
st.write("Lojistik operasyonlar için karar destek uygulaması")

# -----------------------------
# SIDEBAR PARAMETRELER
# -----------------------------
st.sidebar.header("Parametreler")

arac_sayisi = st.sidebar.slider("Araç Sayısı", 1, 5, 2)
arac_kapasitesi = st.sidebar.slider("Araç Kapasitesi", 5, 50, 15)
trafik = st.sidebar.slider("Trafik Katsayısı", 1.0, 2.0, 1.0)

# -----------------------------
# MÜŞTERİ VERİSİ
# -----------------------------
tum_musteriler = {
    "A": (5, 10, 3),
    "B": (-3, 8, 5),
    "C": (12, 2, 4),
    "D": (8, -4, 2),
    "E": (-6, -5, 6),
    "F": (2, 15, 3),
    "G": (14, -1, 5),
    "H": (-2, -9, 2),
    "I": (7, 7, 4)
}

# -----------------------------
# MESAFE FONKSİYONU
# -----------------------------
def mesafe(p1, p2):
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1]) * trafik

# -----------------------------
# RANDOM ROTA
# -----------------------------
def random_mesafe(df):
    noktalar = df.iloc[1:].to_dict('records')
    random.shuffle(noktalar)
    yol = [(0,0)] + [(n["x"], n["y"]) for n in noktalar] + [(0,0)]
    return sum(mesafe(yol[i], yol[i+1]) for i in range(len(yol)-1))

# -----------------------------
# GEMINI YORUM FONKSİYONU
# -----------------------------
def gemini_yorumla(arac_sayisi, toplam_mesafe, tasarruf, trafik):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        Sen bir lojistik uzmanısın.

        Aşağıdaki dağıtım planını değerlendir:

        Araç sayısı: {arac_sayisi}
        Toplam mesafe: {toplam_mesafe:.2f}
        Tasarruf: %{tasarruf:.1f}
        Trafik katsayısı: {trafik}

        3 kısa madde yaz:
        - verimlilik analizi
        - iyileştirme önerisi
        - işletmeye etkisi
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"AI yorum oluşturulamadı: {e}"

# -----------------------------
# MÜŞTERİ SEÇİMİ
# -----------------------------
st.subheader("Müşteri Seçimi")

secili = st.multiselect(
    "Teslimat yapılacak müşterileri seçiniz:",
    list(tum_musteriler.keys()),
    default=["A","B","C","D","E"]
)

if len(secili) == 0:
    st.warning("En az bir müşteri seçilmelidir.")
    st.stop()

# -----------------------------
# DATAFRAME
# -----------------------------
data = [{"name":"Depo","x":0,"y":0,"demand":0}]

for m in secili:
    x,y,d = tum_musteriler[m]
    data.append({"name":m,"x":x,"y":y,"demand":d})

df = pd.DataFrame(data)

st.dataframe(df)

# -----------------------------
# OPTİMİZASYON
# -----------------------------
if st.button("Optimize Et"):

    toplam_talep = df["demand"].sum()
    toplam_kapasite = arac_sayisi * arac_kapasitesi

    if toplam_talep > toplam_kapasite:
        st.error("Toplam talep kapasiteyi aşmaktadır.")
        st.stop()

    musteri_listesi = data[1:]

    arac_rotalari = {i: [] for i in range(arac_sayisi)}
    arac_yukleri = {i: 0 for i in range(arac_sayisi)}

    # müşteri atama
    for m in musteri_listesi:
        uygun = []

        for a in range(arac_sayisi):
            if arac_yukleri[a] + m["demand"] <= arac_kapasitesi:
                if len(arac_rotalari[a]) == 0:
                    son = (0,0)
                else:
                    son = (arac_rotalari[a][-1]["x"], arac_rotalari[a][-1]["y"])

                d = mesafe(son, (m["x"], m["y"]))
                uygun.append((a,d))

        if uygun:
            uygun.sort(key=lambda x: x[1])
            secilen = uygun[0][0]
        else:
            secilen = min(arac_yukleri, key=arac_yukleri.get)

        arac_rotalari[secilen].append(m)
        arac_yukleri[secilen] += m["demand"]

    # rota optimizasyonu
    toplam_mesafe = 0
    fig = go.Figure()
    renkler = ["red","blue","green","purple","orange"]

    for a in range(arac_sayisi):
        duraklar = arac_rotalari[a]

        if not duraklar:
            continue

        en_iyi = None
        en_kisa = float("inf")

        for perm in itertools.permutations(duraklar):
            yol = [(0,0)] + [(d["x"], d["y"]) for d in perm] + [(0,0)]
            m = sum(mesafe(yol[i], yol[i+1]) for i in range(len(yol)-1))

            if m < en_kisa:
                en_kisa = m
                en_iyi = perm

        toplam_mesafe += en_kisa

        x = [0] + [d["x"] for d in en_iyi] + [0]
        y = [0] + [d["y"] for d in en_iyi] + [0]

        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            name=f"Arac {a+1}",
            line=dict(color=renkler[a])
        ))

    # karşılaştırma
    r_mesafe = random_mesafe(df)
    tasarruf = ((r_mesafe - toplam_mesafe) / r_mesafe) * 100

    # sonuçlar
    st.subheader("Sonuçlar")

    col1, col2, col3 = st.columns(3)

    col1.metric("Rastgele Mesafe", f"{r_mesafe:.2f}")
    col2.metric("Optimize Mesafe", f"{toplam_mesafe:.2f}")
    col3.metric("Tasarruf (%)", f"{tasarruf:.1f}")

    # grafik
    fig.add_trace(go.Scatter(
        x=df["x"][1:],
        y=df["y"][1:],
        mode="markers+text",
        text=df["name"][1:],
        name="Musteriler"
    ))

    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode="markers+text",
        text=["Depo"],
        name="Depo"
    ))

    st.plotly_chart(fig, use_container_width=True)

    # GEMINI AI YORUM
    st.subheader("AI Destekli Değerlendirme")

    yorum = gemini_yorumla(arac_sayisi, toplam_mesafe, tasarruf, trafik)
    st.write(yorum)

    st.write("Bu sistem lojistik operasyonlar için karar destek amacıyla geliştirilmiştir.")
