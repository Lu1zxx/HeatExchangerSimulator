"""
Home — Simulador de Trocadores de Calor Casco-e-Tubo
Página inicial do projeto. O simulador está em pages/.
"""
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Simulador — Casco-e-Tubo",
    page_icon="assets/icone.png",   # ← troca o ⚙️ pelo logo
    layout="wide",
)
from PIL import Image
from pathlib import Path

# Logo IFMG na barra lateral
_logo_path = Path(__file__).parent / "assets" / "logo.png"
if not _logo_path.exists():
    _logo_path = Path(__file__).parent.parent / "assets" / "logo.png"

if _logo_path.exists():
    with st.sidebar:
        st.image(str(_logo_path), width=200)
    

# ── CSS para alinhar com o tema escuro ────────────────────────────
st.markdown("""
<style>
.block-container{padding-top:2rem}
.hero{
    background:linear-gradient(135deg,#0B1520 0%,#1E3048 100%);
    padding:48px 32px;border-radius:12px;
    border:1px solid #1F4068;margin-bottom:24px}
.hero h1{color:#DFF0FF;font-family:'Courier New',monospace;font-size:42px;
    margin:0 0 8px 0}
.hero p{color:#6A90B0;font-family:'Courier New',monospace;
    font-size:16px;margin:0}
.card{
    background:#172435;border-left:4px solid #00C2FF;
    border-radius:8px;padding:20px 24px;margin:12px 0;
    font-family:'Courier New',monospace;color:#DFF0FF}
.card h3{color:#00C2FF;margin-top:0}
.card.warn{border-left-color:#FFD166}
.card.warn h3{color:#FFD166}
.card.ok{border-left-color:#00E5A0}
.card.ok h3{color:#00E5A0}
a{color:#00C2FF;text-decoration:none}
a:hover{text-decoration:underline}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>⚙️ Simulador Casco-e-Tubo</h1>
    <p>Kern &amp; Bell-Delaware  ·  v5  ·  com Mudança de Fase, Fouling e CoolProp</p>
</div>
""", unsafe_allow_html=True)

# ── Como usar ─────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
<div class="card">
    <h3>🚀 Começar</h3>
    Use a <b>barra lateral esquerda</b> para navegar até
    <b>⚙️ Simulador</b> e comece a dimensionar seu trocador de calor.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="card">
    <h3>📚 O que você pode fazer</h3>
    <ul>
        <li>Dimensionar trocadores pelos métodos <b>Kern</b> e <b>Bell-Delaware</b></li>
        <li>Consultar propriedades de <b>+40 fluidos</b> via CoolProp (água, ar, refrigerantes, hidrocarbonetos)</li>
        <li>Calcular com <b>mudança de fase</b> (condensação/vaporização)</li>
        <li>Configurar <b>fouling</b> com presets TEMA</li>
        <li>Acompanhar <b>memorial de cálculo</b> passo a passo</li>
    </ul>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="card ok">
    <h3>✅ Resultados confiáveis</h3>
    Correlações validadas por:
    Kern (1950) · Bell &amp; Mueller (2001) · Kakaç &amp; Liu (2002) ·
    Thulukkanam (2013) · Incropera et al. (2007) · TEMA
</div>
""", unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="card warn">
    <h3>💻 Versão desktop</h3>
    Prefere rodar localmente? Baixe o executável:
</div>
""", unsafe_allow_html=True)

    exe = Path("assets/SimuladorCascoTubo.exe")
    if exe.exists():
        with open(exe, "rb") as f:
            st.download_button(
                "⬇️ Baixar .exe (Windows)",
                data=f,
                file_name="SimuladorCascoTubo.exe",
                mime="application/octet-stream",
                use_container_width=True,
            )
    else:
        st.info("📦 Em breve — versão desktop em preparação.")

    st.markdown("---")

    st.markdown("""
<div class="card">
    <h3>📖 Documentação</h3>
    Manual completo com:<br>
    • Guia de instalação<br>
    • Passo a passo das 4 páginas de entrada<br>
    • Interpretação dos resultados<br>
    • Exemplo numérico resolvido
</div>
""", unsafe_allow_html=True)

# ── Rodapé ────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Desenvolvido como parte de Trabalho de Conclusão de Curso  ·  "
    "Kern (1950) · Bell & Mueller (2001) · TEMA Standards"
)
