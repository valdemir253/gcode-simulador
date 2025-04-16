# app.py - Simulador interativo de G-code com orientação e animação da trajetória (Streamlit)

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import time
from io import BytesIO

st.set_page_config(page_title="Simulador de G-code CNC", layout="centered")
st.title("🛠️ Simulador de Trajetória CNC - G-code")

# Peças disponíveis
pecas = {
    "Peça 1": "Retângulo 320x180 mm com furo Ø90 mm (centro em x=160, y=90)",
    "Peça 2": "Círculo Ø420 mm com furo quadrado 120x120 mm",
    "Peça 3": "Retângulo 240x125 mm com furo quadrado 96x50 mm",
}

peca = st.selectbox("1 - Selecione uma das peças para gerar o G-code:", list(pecas.keys()))
st.caption(f"🧩 {pecas[peca]}")

# Desenho da peça selecionada
fig, ax = plt.subplots(figsize=(5, 5))
ax.set_aspect('equal')
ax.grid(True)

if peca == "Peça 1":
    ax.add_patch(patches.Rectangle((0, 0), 320, 180, fill=False, linewidth=2))
    ax.add_patch(patches.Circle((160, 90), 90/2, fill=False, linestyle='--', linewidth=2))
    ax.text(160, 200, "320 x 180 mm\nFuro Ø90 mm", ha='center')
    ax.set_xlim(-50, 400)
    ax.set_ylim(-50, 250)

elif peca == "Peça 2":
    ax.add_patch(patches.Circle((0, 0), 210, fill=False, linewidth=2))
    ax.add_patch(patches.Rectangle((-60, -60), 120, 120, fill=False, linestyle='--', linewidth=2))
    ax.text(0, 100, "Ø420 mm\nFuro 120 x 120 mm", ha='center')
    ax.set_xlim(-250, 250)
    ax.set_ylim(-250, 250)

elif peca == "Peça 3":
    ax.add_patch(patches.Rectangle((-120, -62.5), 240, 125, fill=False, linewidth=2))
    ax.add_patch(patches.Rectangle((-72, -37.5), 96, 50, fill=False, linestyle='--', linewidth=2))
    ax.text(0, 35, "240 x 125 mm\nFuro 96 x 50 mm", ha='center')
    ax.set_xlim(-150, 150)
    ax.set_ylim(-100, 100)

st.pyplot(fig)

# Etapas com instruções e validação por peça
etapas_por_peca = {
    "Peça 1": [
        ("Você deve digitar um nome para esse programa.", lambda entrada: len(entrada.strip()) > 0),
        ("Digite o código de movimento rápido para X0 Y0 (comando G0).", lambda entrada: entrada.strip().upper() == "G0 X0 Y0"),
        ("Digite o código de avanço linear para X320 Y0 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X320 Y0"),
        ("Digite o código de avanço linear para X320 Y180 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X320 Y180"),
        ("Digite o código de avanço linear para X0 Y180 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X0 Y180"),
        ("Digite o código de avanço linear para X0 Y0 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X0 Y0"),
        ("Digite o código de avanço linear para X160 Y45 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X160 Y45"),
        ("Digite o código de interpolação circular horário até X160 Y45 com centro I0 J45 (comando G2).", lambda entrada: entrada.strip().upper() == "G2 X160 Y45 I0 J45"),
        ("Digite o código de finalização do programa (comando M30).", lambda entrada: entrada.strip().upper() == "M30")
    ],
    "Peça 2": [
        ("Nome do programa.", lambda entrada: len(entrada.strip()) > 0),
        ("Movimento rápido para X0 Y-210 (comando G0).", lambda entrada: entrada.strip().upper() == "G0 X0 Y-210"),
        ("Interpolação circular anti-horária até X0 Y210 I0 J210 (comando G3).", lambda entrada: entrada.strip().upper() == "G3 X0 Y210 I0 J210"),
        ("Interpolação circular anti-horária até X0 Y-210 I0 J-210 (comando G3).", lambda entrada: entrada.strip().upper() == "G3 X0 Y-210 I0 J-210"),
        ("Movimento rápido para X-60 Y-60 (comando G0).", lambda entrada: entrada.strip().upper() == "G0 X-60 Y-60"),
        ("Avanço linear até X60 Y-60 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X60 Y-60"),
        ("Avanço linear até X60 Y60 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X60 Y60"),
        ("Avanço linear até X-60 Y60 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X-60 Y60"),
        ("Avanço linear até X-60 Y-60 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X-60 Y-60"),
        ("Final do programa (comando M30).", lambda entrada: entrada.strip().upper() == "M30")
    ],
    "Peça 3": [
        ("Nome do programa.", lambda entrada: len(entrada.strip()) > 0),
        ("Movimento rápido para X-120 Y-62.5 (comando G0).", lambda entrada: entrada.strip().upper() == "G0 X-120 Y-62.5"),
        ("Avanço linear até X120 Y-62.5 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X120 Y-62.5"),
        ("Avanço linear até X120 Y62.5 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X120 Y62.5"),
        ("Avanço linear até X-120 Y62.5 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X-120 Y62.5"),
        ("Avanço linear até X-120 Y-62.5 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X-120 Y-62.5"),
        ("Movimento rápido para X-48 Y0 (comando G0).", lambda entrada: entrada.strip().upper() == "G0 X-48 Y0"),
        ("Avanço linear até X48 Y0 (comando G1).", lambda entrada: entrada.strip().upper() == "G1 X48 Y0"),
        ("Final do programa (comando M30).", lambda entrada: entrada.strip().upper() == "M30")
    ]
}

etapas = etapas_por_peca[peca]

st.markdown("---")
st.subheader("2 - Digite o G-code passo a passo:")

entradas = []
validos = []
executar = False

for i, (instrucao, validador) in enumerate(etapas):
    entrada = st.text_input(f"Linha {i+1}", key=f"linha_{i}_{peca}", label_visibility="collapsed")
    st.caption(f"ℹ️ {instrucao}")
    if entrada:
        if validador(entrada):
            entradas.append(entrada)
            validos.append(True)
        else:
            st.error("❌ Entrada incorreta. Verifique a instrução acima.")
            break
    else:
        break

if len(validos) == len(etapas):
    if st.button("✅ Executar Simulação da Trajetória"):

        def interpretar_gcode(linhas):
            posicoes = []
            pos_atual = np.array([0.0, 0.0])
            for linha in linhas:
                linha = linha.split(';')[0].strip()
                if not linha:
                    continue
                tokens = linha.split()
                cmd = tokens[0].upper()
                args = {t[0]: float(t[1:]) for t in tokens[1:] if t[0] in 'XYZIJ'}
                if cmd in ('G0', 'G1'):
                    nova_pos = np.array([
                        args.get('X', pos_atual[0]),
                        args.get('Y', pos_atual[1])
                    ])
                    posicoes.append((pos_atual.copy(), nova_pos.copy(), cmd))
                    pos_atual = nova_pos
                elif cmd in ('G2', 'G3'):
                    sentido = -1 if cmd == 'G2' else 1
                    centro = pos_atual + np.array([args['I'], args['J']])
                    final = np.array([args['X'], args['Y']])
                    v0 = pos_atual - centro
                    v1 = final - centro
                    ang0 = np.arctan2(v0[1], v0[0])
                    ang1 = np.arctan2(v1[1], v1[0])
                    if sentido == 1 and ang1 <= ang0:
                        ang1 += 2 * np.pi
                    elif sentido == -1 and ang1 >= ang0:
                        ang1 -= 2 * np.pi
                    angs = np.linspace(ang0, ang1, 40)
                    raio = np.linalg.norm(v0)
                    for a1, a2 in zip(angs[:-1], angs[1:]):
                        p1 = centro + raio * np.array([np.cos(a1), np.sin(a1)])
                        p2 = centro + raio * np.array([np.cos(a2), np.sin(a2)])
                        posicoes.append((p1, p2, cmd))
                    pos_atual = final
            return posicoes

        trajetos = interpretar_gcode(entradas)

        fig2, ax2 = plt.subplots(figsize=(6, 6))
        ax2.set_aspect('equal')
        ax2.grid(True)
        ax2.set_xlim(-250, 400)
        ax2.set_ylim(-250, 250)
        ax2.set_title("Trajetória da Ferramenta")

        xdata, ydata = [], []
        img_spot = st.empty()

        n_frames = len(trajetos)
        for i in range(n_frames):
            ini, fim, _ = trajetos[i]
            xdata.extend([ini[0], fim[0]])
            ydata.extend([ini[1], fim[1]])

            ax2.clear()
            ax2.set_aspect('equal')
            ax2.grid(True)
            ax2.set_xlim(-250, 400)
            ax2.set_ylim(-250, 250)
            ax2.set_title(f"Trajetória da Ferramenta (Frame {i+1}/{n_frames})")
            ax2.plot(xdata, ydata, 'r-', lw=2)
            ax2.plot(fim[0], fim[1], 'ro')

            buf = BytesIO()
            fig2.savefig(buf, format="png")
            buf.seek(0)
            img_spot.image(buf)
            time.sleep(0.5)

        st.success("✅ Trajetória executada com sucesso!")
