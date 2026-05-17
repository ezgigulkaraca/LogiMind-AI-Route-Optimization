import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import itertools
import random
import google.generativeai as genai

# =========================
# GEMINI API SETUP
# =========================
API_KEY = "YOUR_API_KEY_HERE"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

# =========================
# STREAMLIT AYAR
# =========================
st.set_page_config(page_title="LogiMind", layout="wide")

st.title("🚚 LogiMind: Rota Optimizasyon Sistemi")
st.write("BTK Hackathon 2026 - AI destekli lojistik optimizasyon")

# =========================
# SIDEBAR PARAMETRELER
# =========================
st.sidebar.header("Parametreler")

arac_sayisi = st.sidebar.slider("Araç Sayısı", 1, 5, 2)
arac_kapasitesi = st.sidebar.slider("Araç Kapasitesi", 5, 50, 15)
trafik = st.sidebar.slider("Trafik Katsayısı", 1.0, 2.0, 1.0)

# =========================
# MÜŞTERİ VERİLERİ
# =========================
musteriler = {
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

# =========================
# MESAFE
# =========================
def mesafe(p1, p2):
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1]) * trafik

def random_mesafe(df):
    noktalar = df.iloc[1:].to_dict("records")
    random.shuffle(noktalar)
    yol = [(0,0)] + [(n["x"], n["y"]) for n in noktalar] + [(0,0)]
    return sum(mesafe(yol[i], yol[i+1]) for i in range(len(yol)-1))

# =========================
# GEMINI AI
# =========================
def gemini_yorum(arac, mesafe, tasarruf, trafik):
    try:
        prompt = f"""
Sen bir lojistik optimizasyon uzmanısın.

Araç sayısı: {arac}
Toplam mesafe: {mesafe:.2f}
Tasarruf: %{tasarruf:.1f}
Trafik: {trafik}

3 madde yaz:
- Verimlilik analizi
- Operasyon önerisi
- Karbon + maliyet etkisi
"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"AI Hatası: {e}"

# =========================
# MÜŞTERİ SEÇİMİ
# =========================
st.subheader("Müşteri Seçimi")

secili = st.multiselect(
    "Müşteriler:",
    list(musteriler.keys()),
    default=["A","B","C","D","E"]
)

if len(secili) == 0:
    st.warning("En az 1 müşteri seçmelisin")
    st.stop()

# =========================
# DATAFRAME
# =========================
data = [{"name": "Depo", "x": 0, "y": 0, "demand": 0}]

for m in secili:
    x, y, d = musteriler[m]
    data.append({"name": m, "x": x, "y": y, "demand": d})

df = pd.DataFrame(data)
st.dataframe(df)

# =========================
# OPTİMİZASYON
# =========================
if st.button("Optimize Et 🚀"):

    toplam_talep = df["demand"].sum()
    kapasite = arac_sayisi * arac_kapasitesi

    if toplam_talep > kapasite:
        st.error("Kapasite yetersiz!")
        st.stop()

    rotalar = {i: [] for i in range(arac_sayisi)}
    yuk = {i: 0 for i in range(arac_sayisi)}

    for m in data[1:]:
        best = None

        for a in range(arac_sayisi):
            if yuk[a] + m["demand"] <= arac_kapasitesi:
                if len(rotalar[a]) == 0:
                    last = (0,0)
                else:
                    last = (rotalar[a][-1]["x"], rotalar[a][-1]["y"])

                d = mesafe(last, (m["x"], m["y"]))
                if best is None or d < best[0]:
                    best = (d, a)

        if best:
            a = best[1]
        else:
            a = min(yuk, key=yuk.get)

        rotalar[a].append(m)
        yuk[a] += m["demand"]

    # =========================
    # ROUTE + PLOT
    # =========================
    fig = go.Figure()
    renk = ["red","blue","green","purple","orange"]

    toplam_mesafe = 0

    for a in range(arac_sayisi):

        if not rotalar[a]:
            continue

        best_route = None
        best_cost = float("inf")

        for perm in itertools.permutations(rotalar[a]):
            path = [(0,0)] + [(p["x"], p["y"]) for p in perm] + [(0,0)]
            cost = sum(mesafe(path[i], path[i+1]) for i in range(len(path)-1))

            if cost < best_cost:
                best_cost = cost
                best_route = perm

        toplam_mesafe += best_cost

        x = [0] + [p["x"] for p in best_route] + [0]
        y = [0] + [p["y"] for p in best_route] + [0]

        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            name=f"Araç {a+1}",
            line=dict(color=renk[a % len(renk)], width=3)
        ))

    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode="markers",
        name="Depo",
        marker=dict(size=12, color="black", symbol="square")
    ))

    fig.update_layout(title="Rota Haritası")

    # =========================
    # METRİKLER
    # =========================
    r = random_mesafe(df)
    tasarruf = ((r - toplam_mesafe) / r) * 100 if r else 0

    st.metric("Rastgele", f"{r:.2f}")
    st.metric("Optimize", f"{toplam_mesafe:.2f}")
    st.metric("Tasarruf", f"%{tasarruf:.1f}")

    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # GEMINI OUTPUT
    # =========================
    st.subheader("AI Rapor")

    with st.spinner("Gemini çalışıyor..."):
        result = gemini_yorum(arac_sayisi, toplam_mesafe, tasarruf, trafik)
        st.success(result)
