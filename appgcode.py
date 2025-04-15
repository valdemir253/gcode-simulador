# app.py - Simulador interativo de G-code para usinagem CNC (Streamlit)

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

st.set_page_config(page_title="Simulador de G-code CNC", layout="centered")
st.title("🛠️ Simulador de Trajetória CNC - G-code")

# Peças disponíveis
pecas = {
    "Peça 1": "Retângulo 320x180 mm com furo Ø95 mm",
    "Peça 2": "Círculo Ø420 mm com furo quadrado 120x120 mm",
    "Peça 3": "Retângulo 240x125 mm com furo 96x50 mm (cantos R10)",
}

peca = st.selectbox("1 - Selecione uma das peças para gerar o G-code:", list(pecas.keys()))
st.caption(f"🧩 {pecas[peca]}")

# Desenho da peça selecionada
fig, ax = plt.subplots(figsize=(5, 5))
ax.set_aspect('equal')
ax.grid(True)

if peca == "Peça 1":
    ax.add_patch(patches.Rectangle((-160, -90), 320, 180, fill=False, linewidth=2))
    ax.add_patch(patches.Circle((0, 0), 95/2, fill=False, linestyle='--', linewidth=2))
    ax.text(0, -100, "320 x 180 mm\nFuro Ø95 mm", ha='center')
    ax.set_xlim(-200, 200)
    ax.set_ylim(-120, 120)

elif peca == "Peça 2":
    ax.add_patch(patches.Circle((0, 0), 210, fill=False, linewidth=2))
    ax.add_patch(patches.Rectangle((-60, -60), 120, 120, fill=False, linestyle='--', linewidth=2))
    ax.text(0, -230, "Ø420 mm\nFuro 120 x 120 mm", ha='center')
    ax.set_xlim(-250, 250)
    ax.set_ylim(-250, 250)

elif peca == "Peça 3":
    ax.add_patch(patches.Rectangle((-120, -62.5), 240, 125, fill=False, linewidth=2))
    ax.add_patch(patches.FancyBboxPatch((-48, -25), 96, 50, boxstyle="Round,pad=0.02,rounding_size=10",
                                        fill=False, linestyle='--', linewidth=2))
    ax.text(0, -80, "240 x 125 mm\nFuro 96 x 50 mm R10", ha='center')
    ax.set_xlim(-150, 150)
    ax.set_ylim(-100, 100)

st.pyplot(fig)

# Entrada de G-code
gcode_input = st.text_area("2 - Digite o G-code da peça linha por linha:", height=200)

# Função de interpretação
@st.cache_data(show_spinner=False)
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
            angs = np.linspace(ang0, ang1, 30)
            raio = np.linalg.norm(v0)
            for a1, a2 in zip(angs[:-1], angs[1:]):
                p1 = centro + raio * np.array([np.cos(a1), np.sin(a1)])
                p2 = centro + raio * np.array([np.cos(a2), np.sin(a2)])
                posicoes.append((p1, p2, cmd))
            pos_atual = final
    return posicoes

# Executar trajetória
if st.button("Executar Simulação"):
    linhas = gcode_input.splitlines()
    trajetos = interpretar_gcode(linhas)

    fig2, ax2 = plt.subplots(figsize=(6, 6))
    ax2.set_aspect('equal')
    ax2.grid(True)
    ax2.set_title("Trajetória da Ferramenta")
    ax2.set_xlim(-50, 400)
    ax2.set_ylim(-50, 250)

    trajeto_x, trajeto_y = [], []
    for ini, fim, _ in trajetos:
        trajeto_x.extend([ini[0], fim[0], None])
        trajeto_y.extend([ini[1], fim[1], None])

    ax2.plot(trajeto_x, trajeto_y, 'r-', lw=2)
    ax2.plot(trajeto_x, trajeto_y, 'k--', lw=1, alpha=0.3)
    ax2.plot(trajeto_x[-2], trajeto_y[-2], 'ro', label="Ponto Final")

    st.pyplot(fig2)
