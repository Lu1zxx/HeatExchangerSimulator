"""
Simulador de Trocadores de Calor Casco-e-Tubo
Métodos: Kern e Bell-Delaware
Streamlit App — roda no navegador (desktop, tablet, celular)
"""

import math
import streamlit as st

# ─────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Simulador Casco-e-Tubo",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; font-weight: 600; }
    .result-box {
        background: #0e1117; border: 1px solid #21262d;
        border-radius: 8px; padding: 16px;
        font-family: 'Courier New', monospace; font-size: 13px;
        white-space: pre-wrap; line-height: 1.6;
        color: #58d68d;
    }
    .warn-box  { background:#1a1200; border:1px solid #f39c12; border-radius:6px; padding:10px; }
    .error-box { background:#1a0000; border:1px solid #e74c3c; border-radius:6px; padding:10px; }
    .ok-box    { background:#001a0a; border:1px solid #27ae60; border-radius:6px; padding:10px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
#  DADOS DE REFERÊNCIA
# ─────────────────────────────────────────────────────────────────
MATERIAIS_TUBO = {
    "Aço Carbono": 50.0, "Aço Inoxidável 304": 16.2, "Aço Inoxidável 316": 13.4,
    "Cobre": 385.0, "Latão (70/30)": 111.0, "Inconel 625": 10.1,
    "Monel 400": 21.8, "Níquel": 90.9, "Titanium Gr.2": 21.9, "Alumínio 6061": 167.0,
}
LIMITES_DP = {
    "Personalizado":                    (0.0,   0.0,  "—"),
    "Líquido — serviço geral":          (35.0,  70.0, "Kern (1983) / TEMA"),
    "Líquido — bomba de baixa pressão": (20.0,  35.0, "Thulukkanam (2013)"),
    "Líquido viscoso (μ > 5 cP)":       (50.0, 100.0, "Kakaç & Liu (2002)"),
    "Vapor / Gás — baixa pressão":      (7.0,   14.0, "Perry's 8ª ed. §11"),
    "Vapor — condensação":              (14.0,  35.0, "Thulukkanam (2013)"),
    "Gás — alta pressão (> 5 bar)":     (35.0,  70.0, "Kakaç & Liu (2002)"),
    "Gás — compressor (crítico)":       (3.5,   7.0,  "Perry's 8ª ed. §11"),
    "Água de resfriamento":             (50.0,  70.0, "TEMA RGP-T-2.4"),
    "Serviço criogênico":               (14.0,  35.0, "Perry's 8ª ed. §11"),
}
TAB10 = {
    30: [(1e5,0.321,-0.388,1.450,0.519),(1e4,0.321,-0.388,None,None),
         (1e3,0.593,-0.477,None,None),(1e2,1.360,-0.657,None,None),(10,1.400,-0.667,None,None)],
    45: [(1e5,0.370,-0.396,1.930,0.500),(1e4,0.370,-0.396,None,None),
         (1e3,0.730,-0.500,None,None),(1e2,0.498,-0.656,None,None),(10,1.550,-0.667,None,None)],
    90: [(1e5,0.370,-0.395,1.187,0.370),(1e4,0.107,-0.266,None,None),
         (1e3,0.408,-0.460,None,None),(1e2,0.900,-0.631,None,None),(10,0.970,-0.667,None,None)],
}
TAB11 = {
    30: [(1e5,0.372,-0.123,7.00,0.500),(1e4,0.486,-0.152,None,None),
         (1e3,4.570,-0.476,None,None),(1e2,45.100,-0.973,None,None),(10,48.000,-1.000,None,None)],
    45: [(1e5,0.303,-0.126,6.59,0.520),(1e4,0.333,-0.136,None,None),
         (1e3,3.500,-0.476,None,None),(1e2,26.200,-0.913,None,None),(10,32.000,-1.000,None,None)],
    90: [(1e5,0.391,-0.148,6.30,0.378),(1e4,0.0815,+0.022,None,None),
         (1e3,6.090,-0.602,None,None),(1e2,32.100,-0.963,None,None),(10,35.000,-1.000,None,None)],
}
K1N_TABLE = {
    (1,30):(0.319,2.142),(1,45):(0.319,2.142),(1,60):(0.319,2.142),(1,90):(0.215,2.207),
    (2,30):(0.249,2.207),(2,45):(0.249,2.207),(2,60):(0.249,2.207),(2,90):(0.156,2.291),
    (4,30):(0.175,2.285),(4,45):(0.175,2.285),(4,60):(0.175,2.285),(4,90):(0.158,2.263),
    (6,30):(0.0743,2.499),(6,45):(0.0743,2.499),(6,60):(0.0743,2.499),(6,90):(0.0402,2.617),
    (8,30):(0.0365,2.675),(8,45):(0.0365,2.675),(8,60):(0.0365,2.675),(8,90):(0.0331,2.643),
}

# ─────────────────────────────────────────────────────────────────
#  FUNÇÕES DE CÁLCULO
# ─────────────────────────────────────────────────────────────────
def _lookup(tabela, theta, Re):
    entradas = tabela[theta]
    for (Re_max, a1, a2, a3, a4) in reversed(entradas):
        if Re <= Re_max:
            return a1, a2, a3, a4
    return entradas[0][1], entradas[0][2], entradas[0][3], entradas[0][4]

def folgas_tema(Ds_mm):
    if Ds_mm <= 300:  Lbb = 9.5
    elif Ds_mm <= 500: Lbb = 11.0
    elif Ds_mm <= 700: Lbb = 12.7
    else:              Lbb = 15.9
    return {"Lbb_mm": Lbb, "Lsb_mm": round(3.1 + 0.004*Ds_mm, 2), "Ltb_mm": 0.8}

def bundle_diameter(Nt, do, Np, theta):
    key = (Np, theta) if (Np, theta) in K1N_TABLE else (Np, 90)
    K1, n1 = K1N_TABLE[key]
    Db = do * (Nt / K1) ** (1.0 / n1)
    Lbb = folgas_tema(Db * 1000)["Lbb_mm"] / 1000.0
    return {"Db": Db, "Ds_estimado": Db + Lbb, "K1": K1, "n1": n1}

def mu_parede(mu_bulk, T_bulk_C, T_w_C, fase="liquido"):
    T_bulk_K = T_bulk_C + 273.15
    T_w_K    = T_w_C    + 273.15
    if abs(T_bulk_K - T_w_K) < 0.5:
        return mu_bulk
    if fase.lower().startswith("g"):
        ratio = (T_w_K / T_bulk_K) ** 0.7
    else:
        B = -math.log(mu_bulk) * T_bulk_K if mu_bulk < 1.0 else 5000.0
        expo = max(-4.6, min(4.6, B * (1.0/T_w_K - 1.0/T_bulk_K)))
        ratio = max(0.01, min(100.0, math.exp(expo)))
    return mu_bulk * ratio

def calcular_mu_parede_iterativo(Tq_bulk, Tf_bulk, R_parede,
                                  obter_viscosidade_q, obter_viscosidade_f,
                                  calcular_h_casco, calcular_h_tubo, tol=0.1, max_iter=50):
    Tw_q = Tw_f = (Tq_bulk + Tf_bulk) / 2.0
    convergiu = False
    mu_w_q = obter_viscosidade_q(Tw_q)
    mu_w_f = obter_viscosidade_f(Tw_f)
    iteracao = 1
    for iteracao in range(1, max_iter + 1):
        mu_w_q = obter_viscosidade_q(Tw_q)
        mu_w_f = obter_viscosidade_f(Tw_f)
        try:
            h_q = max(1e-6, calcular_h_casco(mu_w_q))
            h_f = max(1e-6, calcular_h_tubo(mu_w_f))
        except:
            break
        Rq = 1.0/h_q; Rf = 1.0/h_f
        R_total = Rq + R_parede + Rf
        Q_fluxo = (Tq_bulk - Tf_bulk) / R_total if R_total > 0 else 0.0
        Tw_q_nova = Tq_bulk - Q_fluxo * Rq
        Tw_f_nova = Tw_q_nova - Q_fluxo * R_parede
        erro = max(abs(Tw_q_nova - Tw_q), abs(Tw_f_nova - Tw_f))
        Tw_q, Tw_f = Tw_q_nova, Tw_f_nova
        if erro < tol:
            convergiu = True
            break
    mu_bulk_q = obter_viscosidade_q(Tq_bulk)
    mu_bulk_f = obter_viscosidade_f(Tf_bulk)
    phi_q = (mu_bulk_q / mu_w_q) ** 0.14 if mu_w_q > 0 else 1.0
    phi_f = (mu_bulk_f / mu_w_f) ** 0.14 if mu_w_f > 0 else 1.0
    return {"Tw_q": Tw_q, "Tw_f": Tw_f, "mu_w_q": mu_w_q, "mu_w_f": mu_w_f,
            "h_casco": h_q, "h_tubo": h_f, "phi_q": phi_q, "phi_f": phi_f,
            "iteracoes": iteracao, "convergiu": convergiu}

def lmtd(Thi, Tho, Tci, Tco):
    dT1, dT2 = Thi-Tco, Tho-Tci
    if dT1 <= 0 or dT2 <= 0:
        raise ValueError("ΔT ≤ 0: verifique as temperaturas.")
    return dT1 if abs(dT1-dT2) < 1e-6 else (dT1-dT2)/math.log(dT1/dT2)

def fator_F(Thi, Tho, Tci, Tco, Np):
    if Np == 1: return 1.0
    R = (Thi-Tho)/(Tco-Tci) if (Tco-Tci) != 0 else 1.0
    P = (Tco-Tci)/(Thi-Tci) if (Thi-Tci) != 0 else 0.5
    if abs(R-1.0) < 1e-4:
        if P >= 1.0: return 0.5
        val = P/(1-P)
        if val <= 0: return 1.0
        try:
            F = math.sqrt(2)*val / math.log((1-P)/(1-P*(1+1/val)))
        except: F = 1.0
    else:
        S = math.sqrt(R**2+1)/(R-1)
        arg = (2/P-1-R+math.sqrt(R**2+1))/(2/P-1-R-math.sqrt(R**2+1))
        if arg <= 0: return 0.75
        try: F = S*math.log((1-P)/(1-P*R))/math.log(arg)
        except: F = 0.85
    return max(0.5, min(1.0, F))

def coef_global(hs, ht, d, di, kpar, Q_W, dTlm, Rf_ext=0.0, Rf_int=0.0, F=1.0):
    R_ext  = 1/hs
    R_cond = d*math.log(d/di)/(2*kpar)
    R_int  = (d/di)*(1/ht)
    R_foul = Rf_ext + (d/di)*Rf_int
    U = 1/(R_ext+R_cond+R_int+R_foul)
    A = Q_W/(U*dTlm*F) if (dTlm > 0 and F > 0) else 0
    return {"U":U,"A":A,"R_ext":R_ext,"R_cond":R_cond,"R_int":R_int,"R_foul":R_foul}

def resolver_temp(objetivo, Thi, Tci, T_saida, ms, cp_s, mt, cp_t):
    if objetivo == "Th,o → calcula Tc,o":
        Tho = T_saida
        Q = ms*cp_s*(Thi-Tho)
        if Q <= 0: raise ValueError("Q ≤ 0: Th,o deve ser menor que Th,i")
        Tco = Tci + Q/(mt*cp_t)
    else:
        Tco = T_saida
        Q = mt*cp_t*(Tco-Tci)
        if Q <= 0: raise ValueError("Q ≤ 0: Tc,o deve ser maior que Tc,i")
        Tho = Thi - Q/(ms*cp_s)
    return Tho, Tco

# ── Kern ──────────────────────────────────────────────────────────
def kern_geometria(d, di, Lta, Ltp, theta, Ds, Lbc, Np):
    if theta in (45,90):
        Dhs = 4*(Ltp**2 - math.pi*d**2/4)/(math.pi*d)
    else:
        Dhs = 4*(0.866*Ltp**2/2 - math.pi*d**2/8)/(math.pi*d/2)
    return {"Dhs":Dhs, "C":Ltp-d, "Atc":Ds*(Ltp-d)*Lbc/Ltp}

def kern_casco(ms, mu_s, cp_s, k_s, geo):
    Gs  = ms/geo["Atc"]
    Res = geo["Dhs"]*Gs/mu_s
    Prs = mu_s*cp_s/k_s
    hs  = (0.36*k_s/geo["Dhs"])*Res**0.55*Prs**(1/3)
    return {"Gs":Gs,"Res":Res,"Prs":Prs,"hs":hs}

def kern_pressao_casco(Gs, Res, rho_s, Ds, Dhs, mu_s, mu_ws, Nb):
    phi_s = (mu_s/mu_ws)**0.14
    Rc = max(Res, 400.0)
    fs  = math.exp(0.576 - 0.19*math.log(Rc))
    dPs = fs*Gs**2*(Nb+1)*Ds/(2*rho_s*Dhs*phi_s)
    return {"fs":fs,"dPs":dPs,"phi_s":phi_s,"fora_range":Res<400}

def kern_tubos(mt, rho_t, mu_t, cp_t, k_t, mu_wt, d, di, Lta, Nt, Np):
    At  = math.pi/4*di**2*Nt
    Gt  = mt/(At/Np)
    Ret = di*Gt/mu_t
    Prt = mu_t*cp_t/k_t
    if Ret < 2300:
        arg = max(Ret*Prt*di/Lta, 1e-6)
        Nut = max(3.66, 1.86*arg**(1/3)*(mu_t/mu_wt)**0.14)
        regime = "Laminar (Sieder-Tate)"
    elif Ret > 10000:
        Nut = 0.027*Ret**0.8*Prt**(1/3)*(mu_t/mu_wt)**0.14
        regime = "Turbulento (Sieder-Tate)"
    else:
        f_pet = (0.790*math.log(Ret)-1.64)**(-2)
        denom = 1.0+12.7*math.sqrt(f_pet/8.0)*(Prt**(2/3)-1.0)
        Nut_g = (f_pet/8.0)*(Ret-1000.0)*Prt/denom if denom > 0 else 10.0
        Nut   = max(3.66, Nut_g*(mu_t/mu_wt)**0.14)
        regime = "Transição (Gnielinski)"
    ht  = Nut*k_t/di
    ft  = 64.0/Ret if Ret < 2300 else 0.3164/Ret**0.25
    phi_t = (mu_t/mu_wt)**0.14 if Ret >= 2300 else (mu_t/mu_wt)**0.25
    dPt_fric = ft*(Lta/di)*(Gt**2/(2*rho_t))*(1/phi_t)*Np
    dPt_ret  = 4.0*max(Np-1,0)*(Gt**2/(2.0*rho_t))
    return {"Gt":Gt,"vt":Gt/rho_t,"Ret":Ret,"Prt":Prt,"Nut":Nut,"ht":ht,
            "ft":ft,"dPt":dPt_fric+dPt_ret,"dPt_fric":dPt_fric,
            "dPt_ret":dPt_ret,"regime":regime}

# ── Bell-Delaware ─────────────────────────────────────────────────
def bd_geometria(d, Lta, Ltp, theta, Ds, Bc, Lbc, Lbi, Lbo, Nt, Nss, Lbb_m=None, Ltb_m=0.8e-3):
    Lbb = Lbb_m if Lbb_m else (12.0+0.005*(Ds*1000))/1000
    Dotl = Ds-Lbb; Dctl = Dotl-d
    Nb   = max(1, int(Lta/Lbc)-1)
    arg_ds  = max(-1.0, min(1.0, 1-2*Bc/100))
    theta_ds  = 2*math.acos(arg_ds)
    arg_ctl = max(-1.0, min(1.0, (Ds/Dctl)*(1-2*Bc/100)))
    theta_ctl = 2*math.acos(arg_ctl)
    Ltp_eff = 0.707*Ltp if theta == 45 else Ltp
    Sm  = Lbc*(Lbb + Dctl/Ltp_eff*(Ltp-d))
    Swg = (math.pi/4)*Ds**2*(theta_ds/(2*math.pi)-math.sin(theta_ds)/(2*math.pi))
    Fw  = theta_ctl/(2*math.pi)-math.sin(theta_ctl)/(2*math.pi)
    Fc  = 1-2*Fw; Nwt = Nt*Fw; Swt = Nwt*math.pi/4*d**2; Sw = Swg-Swt
    denom_Dw = math.pi*d*Nwt+math.pi*Ds*theta_ds/(2*math.pi)
    Dw = 4*Sw/denom_Dw if denom_Dw > 0 else 1e-3
    Lpp = {30:Ltp*0.866,45:Ltp*0.707,60:Ltp*0.866,90:Ltp}.get(theta,Ltp)
    Ntcc = abs(Ds/Lpp*(1-2*Bc/100))
    Ntcw = max(0, 0.8/Lpp*(Ds*Bc/100-(Ds-Dctl)/2))
    Sb = Lbc*(Ds-Dotl); Fsbp = Sb/Sm
    Lsb = (3.1+0.004*(Ds*1000))/1000
    Ssb = math.pi*Ds*(Lsb/2)*(2*math.pi-theta_ds)/(2*math.pi)
    Stb = math.pi*d*Ltb_m*Nt*(1-Fw)
    return {"Lbb":Lbb,"Dotl":Dotl,"Dctl":Dctl,"Nb":Nb,"theta_ds":theta_ds,
            "theta_ctl":theta_ctl,"Sm":Sm,"Ltp_eff":Ltp_eff,"Swg":Swg,"Fw":Fw,
            "Fc":Fc,"Nwt":Nwt,"Swt":Swt,"Sw":Sw,"Dw":Dw,"Lpp":Lpp,
            "Ntcc":Ntcc,"Ntcw":Ntcw,"Sb":Sb,"Fsbp":Fsbp,"Ssb":Ssb,"Stb":Stb,"Lbc":Lbc}

def bd_fatores(geo, Res, Nb, Lbi, Lbo, Lbc, Nss):
    Fc=geo["Fc"]; Ssb=geo["Ssb"]; Stb=geo["Stb"]
    Sm=geo["Sm"]; Fsbp=geo["Fsbp"]; Ntcc=geo["Ntcc"]; Ntcw=geo["Ntcw"]
    Jc = 0.55+0.72*Fc
    rs  = Ssb/(Ssb+Stb); rlm = (Ssb+Stb)/Sm
    x   = -0.15*(1+rs)+0.8
    Jl  = 0.44*(1-rs)+(1-0.44*(1-rs))*math.exp(-2.2*rlm)
    Rl  = math.exp(-1.33*(1+rs)*rlm**x)
    rss = min(Nss/Ntcc if Ntcc > 0 else 0, 0.5)
    Cbh = 1.35 if Res > 100 else 1.25
    Cbp = 3.70 if Res > 100 else 4.50
    if rss >= 0.5:
        Jb=Rb=1.0
    else:
        f_Jb = (2*rss)**(1/3) if rss > 0 else 0
        f_Rb = rss**(1/3)     if rss > 0 else 0
        Jb = math.exp(-Cbh*Fsbp*(1-f_Jb))
        Rb = math.exp(-Cbp*Fsbp*(1-f_Rb))
    Nc = (Ntcc+Ntcw)*(Nb+1)
    if Res > 100: Jr = 1.0
    elif Res <= 20: Jr = max(0.4, 1.51/Nc**0.18)
    else:
        Jr_low = 1.51/Nc**0.18
        Jr = max(0.4, Jr_low+(20-Res)/80*(Jr_low-1))
    Li_star = Lbi/Lbc; Lo_star = Lbo/Lbc
    n_Js = 0.6 if Res > 100 else 1.0
    Js_num = (Nb-1)+Li_star**(1-n_Js)+Lo_star**(1-n_Js)
    Js_den = (Nb-1)+Li_star+Lo_star if Nb > 1 else (Li_star+Lo_star)
    Js = Js_num/Js_den if Js_den != 0 else 1.0
    n_Rs = 0.2 if Res > 100 else 1.0
    Rs = 0.5*(Li_star**(n_Rs-2)+Lo_star**(n_Rs-2))
    return {"Jc":Jc,"Jl":Jl,"Jb":Jb,"Js":Js,"Jr":Jr,
            "Rl":Rl,"Rb":Rb,"Rs":Rs,"rs":rs,"rlm":rlm,"rss":rss,"Nc":Nc}

def bd_casco(ms, mu_s, cp_s, k_s, mu_ws, d, Ltp, theta, geo, fat):
    Gs  = ms/geo["Sm"]
    Res = d*Gs/mu_s; Prs = mu_s*cp_s/k_s
    theta_key = min([30,45,90], key=lambda t: abs(t-theta))
    a1,a2,a3,a4 = _lookup(TAB10, theta_key, Res)
    a = a3/(1+0.14*Res**a4) if a3 is not None else 0.0
    ji  = a1*(1.33/(Ltp/d))**a*Res**a2
    phi_s = (mu_s/mu_ws)**0.14
    hi  = ji*cp_s*Gs*phi_s/Prs**(2/3)
    hs  = hi*fat["Jc"]*fat["Jl"]*fat["Jb"]*fat["Js"]*fat["Jr"]
    return {"Gs":Gs,"Res":Res,"Prs":Prs,"ji":ji,"phi_s":phi_s,"hi":hi,"hs":hs}

def bd_pressao_casco(ms, rho_s, mu_s, mu_ws, d, Ltp, theta, geo, fat):
    Sm=geo["Sm"]; Sw=geo["Sw"]; Dw=geo["Dw"]
    Ntcc=geo["Ntcc"]; Ntcw=geo["Ntcw"]; Nb=geo["Nb"]; Lbc=geo["Lbc"]
    Gs = ms/Sm; Res = d*Gs/mu_s
    theta_key = min([30,45,90], key=lambda t: abs(t-theta))
    b1,b2,b3,b4 = _lookup(TAB11, theta_key, Res)
    b = b3/(1+0.14*Res**b4) if b3 is not None else 0.0
    fs   = b1*(1.33/(Ltp/d))**b*Res**b2
    phi_inv = (mu_s/mu_ws)**(-0.14)
    dPbi = 2*fs*Ntcc*Gs**2/rho_s*phi_inv
    dPc  = (Nb-1)*dPbi*fat["Rb"]*fat["Rl"] if Nb > 1 else 0
    ratio = Ntcw/Ntcc if Ntcc > 0 else 0
    dPe  = 2*dPbi*(1+ratio)*fat["Rb"]*fat["Rs"]
    Gw   = ms/math.sqrt(Sm*Sw) if Sw > 0 else 1e-6
    dPwi = (2+0.6*Ntcw)*Gw**2/(2*rho_s) if Res >= 100 else \
           (26*Gw*mu_s/rho_s*(Ntcw/(Ltp-d)+Lbc/Dw)+2*Gw**2/rho_s)
    dPw  = dPwi*Nb*fat["Rl"] if Nb > 0 else 0
    return {"fs":fs,"dPbi":dPbi,"dPc":dPc,"dPw":dPw,"dPe":dPe,
            "dPs":dPc+dPw+dPe,"Gw":Gw,"Res":Res}

# ─────────────────────────────────────────────────────────────────
#  HELPER — bloco de entrada numérica
# ─────────────────────────────────────────────────────────────────
def num_input(label, key, value=0.0, fmt="%.5f", help=None):
    return st.number_input(label, value=float(value), format=fmt, key=key, help=help)

# ─────────────────────────────────────────────────────────────────
#  CABEÇALHO
# ─────────────────────────────────────────────────────────────────
st.title("⚙️ Simulador de Trocadores Casco-e-Tubo")
st.caption("Métodos: **Kern** e **Bell-Delaware**  |  v4  |  Ref: Kern (1950) · Kakaç & Liu (2002) · Thulukkanam (2013) · TEMA")
st.divider()

tab_kern, tab_bd = st.tabs(["🔵  KERN", "🟠  BELL-DELAWARE"])

# ═════════════════════════════════════════════════════════════════
#  ABA KERN
# ═════════════════════════════════════════════════════════════════
with tab_kern:
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        # ── Temperaturas ─────────────────────────────────────────
        st.subheader("🌡️ Temperaturas")
        c1, c2 = st.columns(2)
        k_Thi = c1.number_input("Th,i — entrada quente (°C)", value=100.0, key="k_Thi")
        k_Tci = c2.number_input("Tc,i — entrada frio (°C)",   value=20.0,  key="k_Tci")
        k_obj = st.radio("Objetivo:", ["Th,o → calcula Tc,o", "Tc,o → calcula Th,o"],
                         horizontal=True, key="k_obj")
        k_T_saida = st.number_input(
            "Th,o (°C)" if "Th,o" in k_obj else "Tc,o (°C)",
            value=60.0 if "Th,o" in k_obj else 45.0, key="k_T_saida")

        st.divider()

        # ── Limites ΔP ───────────────────────────────────────────
        st.subheader("⚡ Limites de ΔP")
        k_preset = st.selectbox("Preset por serviço:", list(LIMITES_DP.keys()), key="k_preset")
        ds_pre, dt_pre, ref_pre = LIMITES_DP[k_preset]
        if ds_pre > 0:
            st.caption(f"Ref: {ref_pre}  |  ΔP casco: {ds_pre} kPa  |  ΔP tubos: {dt_pre} kPa")
        c1, c2 = st.columns(2)
        k_dPs_max = c1.number_input("ΔPmax casco (kPa)", value=ds_pre if ds_pre > 0 else 70.0, key="k_dPs_max")
        k_dPt_max = c2.number_input("ΔPmax tubos (kPa)", value=dt_pre if dt_pre > 0 else 100.0, key="k_dPt_max")

        st.divider()

        # ── Fluido casco ─────────────────────────────────────────
        st.subheader("🔵 Fluido — Casco (quente)")
        c1, c2 = st.columns(2)
        k_rho_s = c1.number_input("ρₛ (kg/m³)",   value=983.0,    key="k_rho_s")
        k_mu_s  = c2.number_input("μₛ (Pa·s)",     value=4.6e-4,   format="%.2e", key="k_mu_s")
        k_cp_s  = c1.number_input("cp,s (J/kg·K)", value=4190.0,   key="k_cp_s")
        k_k_s   = c2.number_input("kₛ (W/m·K)",    value=0.659,    key="k_k_s")
        k_ms    = st.number_input("ṁₛ (kg/s)",     value=4.3,      key="k_ms")

        st.divider()

        # ── Fluido tubos ─────────────────────────────────────────
        st.subheader("🔵 Fluido — Tubos (frio)")
        c1, c2 = st.columns(2)
        k_rho_t = c1.number_input("ρₜ (kg/m³)",   value=998.0,    key="k_rho_t")
        k_mu_t  = c2.number_input("μₜ (Pa·s)",     value=8.9e-4,   format="%.2e", key="k_mu_t")
        k_cp_t  = c1.number_input("cp,t (J/kg·K)", value=4182.0,   key="k_cp_t")
        k_k_t   = c2.number_input("kₜ (W/m·K)",    value=0.600,    key="k_k_t")
        k_mt    = st.number_input("ṁₜ (kg/s)",     value=5.7,      key="k_mt")

        st.divider()

        # ── Geometria tubo ───────────────────────────────────────
        st.subheader("📐 Geometria — Tubo")
        c1, c2 = st.columns(2)
        k_d  = c1.number_input("do externo (m)", value=0.01905, format="%.5f", key="k_d")
        k_ep = c2.number_input("Espessura e (m)", value=0.00165, format="%.5f", key="k_ep")
        k_di = k_d - 2*k_ep
        st.caption(f"→ di calculado = **{k_di*1000:.3f} mm**")
        k_mat = st.selectbox("Material do tubo:", list(MATERIAIS_TUBO.keys()), key="k_mat")
        k_kpar = MATERIAIS_TUBO[k_mat]
        st.caption(f"→ k_parede = **{k_kpar} W/m·K**")

        st.divider()

        # ── Casco e chicanas ─────────────────────────────────────
        st.subheader("🏗️ Casco e Chicanas")
        c1, c2 = st.columns(2)
        k_Ds  = c1.number_input("Ds (m)",  value=0.387,  format="%.4f", key="k_Ds")
        k_Lta = c2.number_input("Lta (m)", value=4.877,  format="%.4f", key="k_Lta")
        k_Ltp = c1.number_input("Ltp (m)", value=0.025,  format="%.5f", key="k_Ltp")
        k_Lbc = c2.number_input("Lbc (m)", value=0.200,  format="%.4f", key="k_Lbc")
        k_Nt  = c1.number_input("Nt",      value=158,    step=1,        key="k_Nt")
        k_Nb  = max(1, int(k_Lta/k_Lbc)-1) if k_Lbc > 0 else 1
        st.caption(f"→ Nb calculado = **{k_Nb}** chicanas  (= floor({k_Lta:.3f}/{k_Lbc:.3f}) − 1)")

        k_theta = st.selectbox("Ângulo θ:", [30, 45, 60, 90], key="k_theta")
        k_Np    = st.selectbox("Passes Np:", [1, 2, 4, 6, 8], key="k_Np")

        # ── Estimativa Db/Ds ─────────────────────────────────────
        with st.expander("📐 Estimar Db → Ds (Coulson & Richardson)"):
            if st.button("Calcular Db e Ds estimado", key="k_btn_db"):
                res_db = bundle_diameter(int(k_Nt), k_d, k_Np, k_theta)
                st.success(f"Db = {res_db['Db']*1000:.1f} mm  |  Ds estimado = {res_db['Ds_estimado']*1000:.1f} mm")
                st.caption(f"K₁ = {res_db['K1']}   n = {res_db['n1']}")

        st.divider()

        # ── Fouling ──────────────────────────────────────────────
        st.subheader("🔧 Fouling (TEMA)")
        PRESETS_FOULING = {
            "Personalizado": (0.0002, 0.0002),
            "Água tratada":  (0.000176, 0.000176),
            "Água não tratada": (0.000352, 0.000352),
            "Vapor d'água":  (0.0000882, 0.0000882),
            "Hidrocarbonetos leves": (0.000176, 0.000176),
        }
        k_f_preset = st.selectbox("Preset fouling:", list(PRESETS_FOULING.keys()), key="k_f_preset")
        f_ext_def, f_int_def = PRESETS_FOULING[k_f_preset]
        c1, c2 = st.columns(2)
        k_Rf_ext = c1.number_input("Rf externo (m²·K/W)", value=f_ext_def, format="%.7f", key="k_Rf_ext")
        k_Rf_int = c2.number_input("Rf interno (m²·K/W)", value=f_int_def, format="%.7f", key="k_Rf_int")

        st.divider()
        calcular_k = st.button("▶ CALCULAR — KERN", type="primary", use_container_width=True, key="btn_kern")

    # ── RESULTADO KERN ───────────────────────────────────────────
    with col_out:
        st.subheader("📊 Resultados — Kern")
        if calcular_k:
            try:
                Tho, Tco = resolver_temp(k_obj, k_Thi, k_Tci, k_T_saida, k_ms, k_cp_s, k_mt, k_cp_t)
                Q_W = k_ms*k_cp_s*(k_Thi-Tho)
                dTlm = lmtd(k_Thi, Tho, k_Tci, Tco)
                F    = fator_F(k_Thi, Tho, k_Tci, Tco, k_Np)

                T_bulk_s = (k_Thi+Tho)/2; T_bulk_t = (k_Tci+Tco)/2
                R_par = k_d*math.log(k_d/k_di)/(2*k_kpar) if k_di > 0 else 0

                geo_pre = kern_geometria(k_d, k_di, k_Lta, k_Ltp, k_theta, k_Ds, k_Lbc, k_Np)

                def _h_casco_k(muw_s):
                    c = kern_casco(k_ms, k_mu_s, k_cp_s, k_k_s, geo_pre)
                    return c["hs"]
                def _h_tubo_k(muw_t):
                    t = kern_tubos(k_mt, k_rho_t, k_mu_t, k_cp_t, k_k_t, muw_t,
                                   k_d, k_di, k_Lta, int(k_Nt), k_Np)
                    return t["ht"]

                res_muw = calcular_mu_parede_iterativo(
                    T_bulk_s, T_bulk_t, R_par,
                    lambda T: mu_parede(k_mu_s, T_bulk_s, T),
                    lambda T: mu_parede(k_mu_t, T_bulk_t, T),
                    _h_casco_k, _h_tubo_k)
                mu_ws = res_muw["mu_w_q"]; mu_wt = res_muw["mu_w_f"]

                geo   = kern_geometria(k_d, k_di, k_Lta, k_Ltp, k_theta, k_Ds, k_Lbc, k_Np)
                casco = kern_casco(k_ms, k_mu_s, k_cp_s, k_k_s, geo)
                press = kern_pressao_casco(casco["Gs"], casco["Res"], k_rho_s,
                                           k_Ds, geo["Dhs"], k_mu_s, mu_ws, k_Nb)
                tubos = kern_tubos(k_mt, k_rho_t, k_mu_t, k_cp_t, k_k_t, mu_wt,
                                   k_d, k_di, k_Lta, int(k_Nt), k_Np)
                glob  = coef_global(casco["hs"], tubos["ht"], k_d, k_di, k_kpar,
                                    Q_W, dTlm, k_Rf_ext, k_Rf_int, F)
                A_inst  = int(k_Nt)*math.pi*k_d*k_Lta
                excesso = (A_inst/glob["A"]-1)*100 if glob["A"] > 0 else 0

                # Métricas principais
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("U  (W/m²·K)", f"{glob['U']:.1f}")
                mc2.metric("Área calc. (m²)", f"{glob['A']:.3f}")
                mc3.metric("Área inst. (m²)", f"{A_inst:.3f}")
                mc4.metric("Excesso (%)", f"{excesso:.1f}",
                           delta=None,
                           delta_color="normal" if 10 <= excesso <= 25 else "inverse")

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Q (kW)", f"{Q_W/1000:.2f}")
                mc2.metric("LMTD (°C)", f"{dTlm:.2f}")
                mc3.metric("Fator F", f"{F:.4f}")
                mc4.metric("ΔPs (kPa)", f"{press['dPs']/1000:.2f}")

                # Aviso F
                if F < 0.75:
                    st.warning("⚠️ F < 0,75 — considere aumentar Np ou usar 2 cascos em série")

                # Verificação ΔP
                st.subheader("Verificação de Pressão")
                c1, c2 = st.columns(2)
                dPs_kPa = press["dPs"]/1000; dPt_kPa = tubos["dPt"]/1000
                ok_s = dPs_kPa <= k_dPs_max
                ok_t = dPt_kPa <= k_dPt_max
                c1.metric("ΔPs calculado (kPa)", f"{dPs_kPa:.3f}",
                          f"Máx: {k_dPs_max:.1f} kPa — {'✓ OK' if ok_s else '⚠ EXCEDE'}")
                c2.metric("ΔPt calculado (kPa)", f"{dPt_kPa:.3f}",
                          f"Máx: {k_dPt_max:.1f} kPa — {'✓ OK' if ok_t else '⚠ EXCEDE'}")
                if not ok_s: st.error("❌ ΔP casco excede o limite!")
                if not ok_t: st.error("❌ ΔP tubos excede o limite!")

                # Diagnóstico excesso
                st.subheader("Diagnóstico de Área")
                if excesso < 0:
                    st.error("❌ Área INSUFICIENTE — trocador não atinge a transferência requerida.")
                elif excesso < 10:
                    st.warning("⚠️ Margem muito estreita (< 10%) — risco com fouling e variações.")
                elif excesso <= 25:
                    st.success("✅ Projeto ADEQUADO — excesso entre 10 e 25%.")
                elif excesso <= 35:
                    st.warning("⚠️ Leve superdimensionamento (25–35%) — considere reduzir Nt ou Lta.")
                else:
                    st.error("❌ Superdimensionamento excessivo (> 35%) — redimensione.")

                # Resultado detalhado
                txt = f"""
╔══════════════════════════════════════════════╗
║       RESULTADO — MÉTODO DE KERN             ║
╚══════════════════════════════════════════════╝

─── TEMPERATURAS ────────────────────────────────
  Quente : {k_Thi:.2f} °C  →  {Tho:.2f} °C
  Frio   : {k_Tci:.2f} °C  →  {Tco:.2f} °C

─── BALANÇO ENERGÉTICO ──────────────────────────
  Q               = {Q_W/1000:.4f} kW
  LMTD            = {dTlm:.4f} °C
  Fator F         = {F:.4f}  (Np = {k_Np} passes)

─── VISCOSIDADE NA PAREDE (iterativo) ───────────
  Tw casco = {res_muw['Tw_q']:.2f} °C   μw,s = {mu_ws:.4e} Pa·s   φs = {res_muw['phi_q']:.4f}
  Tw tubo  = {res_muw['Tw_f']:.2f} °C   μw,t = {mu_wt:.4e} Pa·s   φt = {res_muw['phi_f']:.4f}
  Convergência: {res_muw['iteracoes']} iterações  {'✓' if res_muw['convergiu'] else '⚠ não convergiu'}

─── GEOMETRIA (Kern) ────────────────────────────
  Nb  = {k_Nb}   Dhs = {geo['Dhs']*1000:.2f} mm   Atc = {geo['Atc']*1e4:.4f} cm²

─── LADO DO CASCO ───────────────────────────────
  Gs  = {casco['Gs']:.4f} kg/m²·s
  Res = {casco['Res']:.1f}
  Prs = {casco['Prs']:.4f}
  hs  = {casco['hs']:.2f} W/m²·K
  ΔPs = {press['dPs']:.2f} Pa  ({press['dPs']/1000:.4f} kPa){'  ⚠ Re<400: extrapolado' if press['fora_range'] else ''}

─── LADO DOS TUBOS ──────────────────────────────
  Ret   = {tubos['Ret']:.1f}   [{tubos['regime']}]
  Nut   = {tubos['Nut']:.4f}
  ht    = {tubos['ht']:.2f} W/m²·K
  vt    = {tubos['vt']:.3f} m/s
  ΔPt fricc  = {tubos['dPt_fric']:.2f} Pa
  ΔPt retorno= {tubos['dPt_ret']:.2f} Pa  ({k_Np-1} curvas)
  ΔPt total  = {tubos['dPt']:.2f} Pa  ({tubos['dPt']/1000:.4f} kPa)

─── COEFICIENTE GLOBAL ──────────────────────────
  R_ext  = {glob['R_ext']:.6f} m²·K/W
  R_cond = {glob['R_cond']:.6f} m²·K/W
  R_int  = {glob['R_int']:.6f} m²·K/W
  R_foul = {glob['R_foul']:.6f} m²·K/W
  U      = {glob['U']:.2f} W/m²·K

─── DIMENSIONAMENTO ─────────────────────────────
  Área necessária  = {glob['A']:.4f} m²
  Área instalada   = {A_inst:.4f} m²
  Excesso          = {excesso:.1f} %

─── FOULING ─────────────────────────────────────
  Rf ext = {k_Rf_ext:.7f} m²·K/W
  Rf int = {k_Rf_int:.7f} m²·K/W

Ref: Kern (1950) · Sieder-Tate (1936/1958)
     Gnielinski (1976) · TEMA · Kakaç & Liu (2002)
"""
                st.markdown(f'<div class="result-box">{txt}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erro: {e}")

# ═════════════════════════════════════════════════════════════════
#  ABA BELL-DELAWARE
# ═════════════════════════════════════════════════════════════════
with tab_bd:
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.subheader("🌡️ Temperaturas")
        c1, c2 = st.columns(2)
        b_Thi = c1.number_input("Th,i — entrada quente (°C)", value=100.0, key="b_Thi")
        b_Tci = c2.number_input("Tc,i — entrada frio (°C)",   value=20.0,  key="b_Tci")
        b_obj = st.radio("Objetivo:", ["Th,o → calcula Tc,o", "Tc,o → calcula Th,o"],
                         horizontal=True, key="b_obj")
        b_T_saida = st.number_input(
            "Th,o (°C)" if "Th,o" in b_obj else "Tc,o (°C)",
            value=60.0 if "Th,o" in b_obj else 45.0, key="b_T_saida")

        st.divider()
        st.subheader("⚡ Limites de ΔP")
        b_preset = st.selectbox("Preset por serviço:", list(LIMITES_DP.keys()), key="b_preset")
        ds_pre2, dt_pre2, ref_pre2 = LIMITES_DP[b_preset]
        if ds_pre2 > 0:
            st.caption(f"Ref: {ref_pre2}  |  ΔP casco: {ds_pre2} kPa  |  ΔP tubos: {dt_pre2} kPa")
        c1, c2 = st.columns(2)
        b_dPs_max = c1.number_input("ΔPmax casco (kPa)", value=ds_pre2 if ds_pre2>0 else 70.0, key="b_dPs_max")
        b_dPt_max = c2.number_input("ΔPmax tubos (kPa)", value=dt_pre2 if dt_pre2>0 else 100.0, key="b_dPt_max")

        st.divider()
        st.subheader("🟠 Fluido — Casco (quente)")
        c1, c2 = st.columns(2)
        b_rho_s = c1.number_input("ρₛ (kg/m³)",   value=983.0,   key="b_rho_s")
        b_mu_s  = c2.number_input("μₛ (Pa·s)",     value=4.6e-4,  format="%.2e", key="b_mu_s")
        b_cp_s  = c1.number_input("cp,s (J/kg·K)", value=4190.0,  key="b_cp_s")
        b_k_s   = c2.number_input("kₛ (W/m·K)",    value=0.659,   key="b_k_s")
        b_ms    = st.number_input("ṁₛ (kg/s)",     value=4.3,     key="b_ms")

        st.divider()
        st.subheader("🟠 Fluido — Tubos (frio)")
        c1, c2 = st.columns(2)
        b_rho_t = c1.number_input("ρₜ (kg/m³)",   value=998.0,   key="b_rho_t")
        b_mu_t  = c2.number_input("μₜ (Pa·s)",     value=8.9e-4,  format="%.2e", key="b_mu_t")
        b_cp_t  = c1.number_input("cp,t (J/kg·K)", value=4182.0,  key="b_cp_t")
        b_k_t   = c2.number_input("kₜ (W/m·K)",    value=0.600,   key="b_k_t")
        b_mt    = st.number_input("ṁₜ (kg/s)",     value=5.7,     key="b_mt")

        st.divider()
        st.subheader("📐 Geometria — Tubo")
        c1, c2 = st.columns(2)
        b_d  = c1.number_input("do externo (m)", value=0.01905, format="%.5f", key="b_d")
        b_ep = c2.number_input("Espessura e (m)", value=0.00165, format="%.5f", key="b_ep")
        b_di = b_d - 2*b_ep
        st.caption(f"→ di calculado = **{b_di*1000:.3f} mm**")
        b_mat  = st.selectbox("Material do tubo:", list(MATERIAIS_TUBO.keys()), key="b_mat")
        b_kpar = MATERIAIS_TUBO[b_mat]
        st.caption(f"→ k_parede = **{b_kpar} W/m·K**")

        st.divider()
        st.subheader("🏗️ Casco e Chicanas")
        c1, c2 = st.columns(2)
        b_Ds  = c1.number_input("Ds (m)",    value=0.387,  format="%.4f", key="b_Ds")
        b_Lta = c2.number_input("Lta (m)",   value=4.877,  format="%.4f", key="b_Lta")
        b_Ltp = c1.number_input("Ltp (m)",   value=0.025,  format="%.5f", key="b_Ltp")
        b_Bc  = c2.number_input("Bc (%)",    value=25.0,   key="b_Bc")
        b_Lbc = c1.number_input("Lbc (m)",   value=0.200,  format="%.4f", key="b_Lbc")

        # Lbi e Lbo com botão de cópia
        c1, c2 = st.columns(2)
        b_Lbi = c1.number_input("Lbi (m)",   value=0.200,  format="%.4f", key="b_Lbi")
        b_Lbo = c2.number_input("Lbo (m)",   value=0.200,  format="%.4f", key="b_Lbo")
        if b_Lbi != b_Lbc or b_Lbo != b_Lbc:
            st.info("ℹ️ Lbi ≠ Lbc ou Lbo ≠ Lbc → fator Js < 1 penaliza h (Bell-Delaware)")

        c1, c2 = st.columns(2)
        b_Nss = c1.number_input("Nss (tiras vedação)", value=1.0,   key="b_Nss")
        b_Nt  = c2.number_input("Nt (nº tubos)",       value=158,   step=1, key="b_Nt")

        b_Nb_calc = max(1, int(b_Lta/b_Lbc)-1) if b_Lbc > 0 else 1
        st.caption(f"→ Nb calculado = **{b_Nb_calc}** chicanas")

        b_theta = st.selectbox("Ângulo θ:", [30, 45, 90], key="b_theta")
        b_Np    = st.selectbox("Passes Np:", [1, 2, 4, 6, 8], key="b_Np")

        with st.expander("📐 Estimar Db → Ds (Coulson & Richardson)"):
            if st.button("Calcular Db e Ds estimado", key="b_btn_db"):
                res_db = bundle_diameter(int(b_Nt), b_d, b_Np, b_theta)
                st.success(f"Db = {res_db['Db']*1000:.1f} mm  |  Ds estimado = {res_db['Ds_estimado']*1000:.1f} mm")
                st.caption(f"K₁ = {res_db['K1']}   n = {res_db['n1']}")

        st.divider()
        st.subheader("📏 Folgas TEMA")
        c1, c2, c3 = st.columns(3)
        b_Lbb = c1.number_input("Lbb (mm)", value=folgas_tema(b_Ds*1000)["Lbb_mm"], format="%.2f", key="b_Lbb")
        b_Ltb = c2.number_input("Ltb (mm)", value=0.80, format="%.2f", key="b_Ltb")
        if st.button("↻ Recalcular folgas TEMA", key="b_tema"):
            f = folgas_tema(b_Ds*1000)
            st.info(f"Lbb = {f['Lbb_mm']} mm  |  Lsb = {f['Lsb_mm']} mm  |  Ltb = {f['Ltb_mm']} mm")

        st.divider()
        st.subheader("🔧 Fouling (TEMA)")
        b_f_preset = st.selectbox("Preset fouling:", list(PRESETS_FOULING.keys()), key="b_f_preset")
        f_ext_def2, f_int_def2 = PRESETS_FOULING[b_f_preset]
        c1, c2 = st.columns(2)
        b_Rf_ext = c1.number_input("Rf externo (m²·K/W)", value=f_ext_def2, format="%.7f", key="b_Rf_ext")
        b_Rf_int = c2.number_input("Rf interno (m²·K/W)", value=f_int_def2, format="%.7f", key="b_Rf_int")

        st.divider()
        calcular_b = st.button("▶ CALCULAR — BELL-DELAWARE", type="primary",
                               use_container_width=True, key="btn_bd")

    # ── RESULTADO BELL-DELAWARE ──────────────────────────────────
    with col_out:
        st.subheader("📊 Resultados — Bell-Delaware")
        if calcular_b:
            try:
                Tho, Tco = resolver_temp(b_obj, b_Thi, b_Tci, b_T_saida, b_ms, b_cp_s, b_mt, b_cp_t)
                Q_W  = b_ms*b_cp_s*(b_Thi-Tho)
                dTlm = lmtd(b_Thi, Tho, b_Tci, Tco)
                F    = fator_F(b_Thi, Tho, b_Tci, Tco, b_Np)

                T_bulk_s = (b_Thi+Tho)/2; T_bulk_t = (b_Tci+Tco)/2
                R_par    = b_d*math.log(b_d/b_di)/(2*b_kpar) if b_di > 0 else 0
                Lbb_m    = b_Lbb/1000; Ltb_m = b_Ltb/1000

                geo_pre = bd_geometria(b_d, b_Lta, b_Ltp, b_theta, b_Ds, b_Bc,
                                       b_Lbc, b_Lbi, b_Lbo, int(b_Nt), b_Nss, Lbb_m, Ltb_m)
                Gs_pre  = b_ms/geo_pre["Sm"]
                Res_pre = b_d*Gs_pre/b_mu_s
                fat_pre = bd_fatores(geo_pre, Res_pre, geo_pre["Nb"], b_Lbi, b_Lbo, b_Lbc, b_Nss)

                def _h_casco_bd(muw_s):
                    c = bd_casco(b_ms, b_mu_s, b_cp_s, b_k_s, muw_s, b_d, b_Ltp,
                                 b_theta, geo_pre, fat_pre)
                    return c["hi"]
                def _h_tubo_bd(muw_t):
                    t = kern_tubos(b_mt, b_rho_t, b_mu_t, b_cp_t, b_k_t, muw_t,
                                   b_d, b_di, b_Lta, int(b_Nt), b_Np)
                    return t["ht"]

                res_muw = calcular_mu_parede_iterativo(
                    T_bulk_s, T_bulk_t, R_par,
                    lambda T: mu_parede(b_mu_s, T_bulk_s, T),
                    lambda T: mu_parede(b_mu_t, T_bulk_t, T),
                    _h_casco_bd, _h_tubo_bd)
                mu_ws = res_muw["mu_w_q"]; mu_wt = res_muw["mu_w_f"]

                geo   = bd_geometria(b_d, b_Lta, b_Ltp, b_theta, b_Ds, b_Bc,
                                     b_Lbc, b_Lbi, b_Lbo, int(b_Nt), b_Nss, Lbb_m, Ltb_m)
                Nb    = geo["Nb"]
                Gs_e  = b_ms/geo["Sm"]; Res_e = b_d*Gs_e/b_mu_s
                fat   = bd_fatores(geo, Res_e, Nb, b_Lbi, b_Lbo, b_Lbc, b_Nss)
                casco = bd_casco(b_ms, b_mu_s, b_cp_s, b_k_s, mu_ws, b_d, b_Ltp,
                                 b_theta, geo, fat)
                press = bd_pressao_casco(b_ms, b_rho_t, b_mu_s, mu_ws, b_d, b_Ltp,
                                         b_theta, geo, fat)
                tubos = kern_tubos(b_mt, b_rho_t, b_mu_t, b_cp_t, b_k_t, mu_wt,
                                   b_d, b_di, b_Lta, int(b_Nt), b_Np)
                glob  = coef_global(casco["hs"], tubos["ht"], b_d, b_di, b_kpar,
                                    Q_W, dTlm, b_Rf_ext, b_Rf_int, F)
                A_inst  = int(b_Nt)*math.pi*b_d*b_Lta
                excesso = (A_inst/glob["A"]-1)*100 if glob["A"] > 0 else 0
                ProdJ = fat["Jc"]*fat["Jl"]*fat["Jb"]*fat["Js"]*fat["Jr"]

                # Métricas
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("U (W/m²·K)",    f"{glob['U']:.1f}")
                mc2.metric("Área calc. (m²)", f"{glob['A']:.3f}")
                mc3.metric("Área inst. (m²)", f"{A_inst:.3f}")
                mc4.metric("Excesso (%)", f"{excesso:.1f}")

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Q (kW)",   f"{Q_W/1000:.2f}")
                mc2.metric("LMTD (°C)", f"{dTlm:.2f}")
                mc3.metric("Fator F",   f"{F:.4f}")
                mc4.metric("∏J",        f"{ProdJ:.4f}")

                if F < 0.75:
                    st.warning("⚠️ F < 0,75 — considere aumentar Np ou usar 2 cascos em série")
                if ProdJ < 0.6:
                    st.warning(f"⚠️ ∏J = {ProdJ:.3f} — eficiência muito baixa. Revise geometria.")

                # Fatores J como tabela
                st.subheader("Fatores de Correção J")
                jdf = {
                    "Fator": ["Jc","Jl","Jb","Js","Jr","∏J"],
                    "Valor": [f"{fat['Jc']:.4f}",f"{fat['Jl']:.4f}",f"{fat['Jb']:.4f}",
                              f"{fat['Js']:.4f}",f"{fat['Jr']:.4f}",f"{ProdJ:.4f}"],
                    "Status": [
                        "✅" if fat['Jc'] >= 0.9 else "⚠️",
                        "✅" if fat['Jl'] >= 0.75 else ("❌" if fat['Jl'] < 0.6 else "⚠️"),
                        "✅" if fat['Jb'] >= 0.85 else ("❌" if fat['Jb'] < 0.7 else "⚠️"),
                        "✅" if fat['Js'] >= 0.9 else "⚠️",
                        "✅" if fat['Jr'] >= 1.0 else "⚠️",
                        "✅" if ProdJ >= 0.7 else ("❌" if ProdJ < 0.6 else "⚠️"),
                    ]
                }
                st.table(jdf)

                # ΔP e diagnóstico
                st.subheader("Verificação de Pressão")
                c1, c2 = st.columns(2)
                dPs_kPa = press["dPs"]/1000; dPt_kPa = tubos["dPt"]/1000
                ok_s = dPs_kPa <= b_dPs_max; ok_t = dPt_kPa <= b_dPt_max
                c1.metric("ΔPs (kPa)", f"{dPs_kPa:.3f}",
                          f"Máx: {b_dPs_max:.1f} — {'✓ OK' if ok_s else '⚠ EXCEDE'}")
                c2.metric("ΔPt (kPa)", f"{dPt_kPa:.3f}",
                          f"Máx: {b_dPt_max:.1f} — {'✓ OK' if ok_t else '⚠ EXCEDE'}")

                st.subheader("Diagnóstico de Área")
                if excesso < 0:
                    st.error("❌ Área INSUFICIENTE — trocador não atende a transferência requerida.")
                elif excesso < 10:
                    st.warning("⚠️ Margem muito estreita (< 10%)")
                elif excesso <= 25:
                    st.success("✅ Projeto ADEQUADO — excesso entre 10 e 25%.")
                elif excesso <= 35:
                    st.warning("⚠️ Leve superdimensionamento (25–35%)")
                else:
                    st.error("❌ Superdimensionamento excessivo (> 35%)")

                # Resultado detalhado
                txt = f"""
╔══════════════════════════════════════════════╗
║       RESULTADO — BELL-DELAWARE              ║
╚══════════════════════════════════════════════╝

─── TEMPERATURAS ────────────────────────────────
  Quente : {b_Thi:.2f} °C  →  {Tho:.2f} °C
  Frio   : {b_Tci:.2f} °C  →  {Tco:.2f} °C

─── BALANÇO ENERGÉTICO ──────────────────────────
  Q               = {Q_W/1000:.4f} kW
  LMTD            = {dTlm:.4f} °C
  Fator F         = {F:.4f}  (Np = {b_Np} passes)

─── VISCOSIDADE NA PAREDE (iterativo) ───────────
  Tw casco = {res_muw['Tw_q']:.2f} °C   μw,s = {mu_ws:.4e} Pa·s   φs = {res_muw['phi_q']:.4f}
  Tw tubo  = {res_muw['Tw_f']:.2f} °C   μw,t = {mu_wt:.4e} Pa·s   φt = {res_muw['phi_f']:.4f}
  Convergência: {res_muw['iteracoes']} iterações  {'✓' if res_muw['convergiu'] else '⚠ não convergiu'}

─── FOLGAS TEMA ─────────────────────────────────
  Lbb = {geo['Lbb']*1000:.2f} mm   Ltb = {Ltb_m*1000:.1f} mm

─── GEOMETRIA AUXILIAR ──────────────────────────
  Nb   = {Nb}   Sm = {geo['Sm']*1e4:.4f} cm²
  Sw   = {geo['Sw']*1e4:.4f} cm²   Fc = {geo['Fc']:.4f}
  Ntcc = {geo['Ntcc']:.2f}   Ntcw = {geo['Ntcw']:.2f}
  Fsbp = {geo['Fsbp']:.4f}

─── FATORES J ───────────────────────────────────
  Jc={fat['Jc']:.4f}  Jl={fat['Jl']:.4f}  Jb={fat['Jb']:.4f}
  Js={fat['Js']:.4f}  Jr={fat['Jr']:.4f}  ∏J={ProdJ:.4f}

─── LADO DO CASCO ───────────────────────────────
  Gs  = {casco['Gs']:.4f} kg/m²·s
  Res = {casco['Res']:.1f}   Prs = {casco['Prs']:.4f}
  hi  = {casco['hi']:.2f} W/m²·K  (ideal)
  hs  = {casco['hs']:.2f} W/m²·K  (REAL)
  ΔPs = {press['dPs']:.2f} Pa  ({press['dPs']/1000:.4f} kPa)
    ΔPc={press['dPc']:.2f}  ΔPw={press['dPw']:.2f}  ΔPe={press['dPe']:.2f} Pa

─── LADO DOS TUBOS ──────────────────────────────
  Ret  = {tubos['Ret']:.1f}  [{tubos['regime']}]
  Nut  = {tubos['Nut']:.4f}
  ht   = {tubos['ht']:.2f} W/m²·K
  vt   = {tubos['vt']:.3f} m/s
  ΔPt fricc   = {tubos['dPt_fric']:.2f} Pa
  ΔPt retorno = {tubos['dPt_ret']:.2f} Pa  ({b_Np-1} curvas)
  ΔPt total   = {tubos['dPt']:.2f} Pa  ({tubos['dPt']/1000:.4f} kPa)

─── COEFICIENTE GLOBAL ──────────────────────────
  R_ext  = {glob['R_ext']:.6f} m²·K/W
  R_cond = {glob['R_cond']:.6f} m²·K/W
  R_int  = {glob['R_int']:.6f} m²·K/W
  R_foul = {glob['R_foul']:.6f} m²·K/W
  U      = {glob['U']:.2f} W/m²·K

─── DIMENSIONAMENTO ─────────────────────────────
  Área necessária = {glob['A']:.4f} m²
  Área instalada  = {A_inst:.4f} m²
  Excesso         = {excesso:.1f} %

Ref: Bell & Mueller (2001) · Kakaç & Liu (2002)
     Thulukkanam (2013) · TEMA Standards
"""
                st.markdown(f'<div class="result-box">{txt}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erro: {e}")

# ─── Rodapé ──────────────────────────────────────────────────────
st.divider()
st.caption("Ref: Kern (1950) · Bell & Mueller (2001) · Kakaç & Liu (2002) · "
           "Thulukkanam (2013) · Gnielinski (1976) · TEMA Standards · "
           "Coulson & Richardson Vol.6")
