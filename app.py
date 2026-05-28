"""
Simulador de Trocadores de Calor Casco-e-Tubo
Métodos: Kern e Bell-Delaware  |  v5  |  Streamlit Pro
"""
import math
import streamlit as st

st.set_page_config(
    page_title="Simulador Casco-e-Tubo",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização customizada em modo Dark Terminal
st.markdown("""
<style>
.block-container{padding-top:1rem}
.result-box{
    background:#0e1117;border:1px solid #21262d;border-radius:8px;
    padding:16px;font-family:'Courier New',monospace;font-size:13px;
    white-space:pre-wrap;line-height:1.6;color:#58d68d}
input[type=text]{font-size:15px!important}
</style>""", unsafe_allow_html=True)

# ─── DADOS DE REFERÊNCIA E CONSTANTES ────────────────────────────
MATERIAIS = {
    "Aço Carbono":50.0,"Aço Inoxidável 304":16.2,"Aço Inoxidável 316":13.4,
    "Cobre":385.0,"Latão (70/30)":111.0,"Inconel 625":10.1,
    "Monel 400":21.8,"Níquel":90.9,"Titanium Gr.2":21.9,"Alumínio 6061":167.0,
}
LIMITES_DP = {
    "Personalizado":                    (0.0,  0.0,  "—"),
    "Líquido — serviço geral":          (35.0, 70.0, "Kern (1983)/TEMA"),
    "Líquido — bomba baixa pressão":    (20.0, 35.0, "Thulukkanam (2013)"),
    "Líquido viscoso (μ>5 cP)":         (50.0,100.0, "Kakaç & Liu (2002)"),
    "Vapor / Gás — baixa pressão":      (7.0,  14.0, "Perry's §11"),
    "Vapor — condensação":              (14.0, 35.0, "Thulukkanam (2013)"),
    "Gás — alta pressão (>5 bar)":      (35.0, 70.0, "Kakaç & Liu (2002)"),
    "Gás — compressor (crítico)":       (3.5,  7.0,  "Perry's §11"),
    "Água de resfriamento":             (50.0, 70.0, "TEMA RGP-T-2.4"),
    "Serviço criogênico":               (14.0, 35.0, "Perry's §11"),
}
FOULING_PRESETS = {
    "Personalizado":               (0.0002,   0.0002),
    "Água tratada":                (0.000176, 0.000176),
    "Água não tratada":            (0.000352, 0.000352),
    "Vapor d'água":                (0.0000882,0.0000882),
    "Hidrocarbonetos leves":       (0.000176, 0.000176),
    "Hidrocarbonetos pesados":     (0.000528, 0.000528),
}
TAB10={
    30:[(1e5,0.321,-0.388,1.450,0.519),(1e4,0.321,-0.388,None,None),
        (1e3,0.593,-0.477,None,None),(1e2,1.360,-0.657,None,None),(10,1.400,-0.667,None,None)],
    45:[(1e5,0.370,-0.396,1.930,0.500),(1e4,0.370,-0.396,None,None),
        (1e3,0.730,-0.500,None,None),(1e2,0.498,-0.656,None,None),(10,1.550,-0.667,None,None)],
    90:[(1e5,0.370,-0.395,1.187,0.370),(1e4,0.107,-0.266,None,None),
        (1e3,0.408,-0.460,None,None),(1e2,0.900,-0.631,None,None),(10,0.970,-0.667,None,None)],
}
TAB11={
    30:[(1e5,0.372,-0.123,7.00,0.500),(1e4,0.486,-0.152,None,None),
        (1e3,4.570,-0.476,None,None),(1e2,45.100,-0.973,None,None),(10,48.000,-1.000,None,None)],
    45:[(1e5,0.303,-0.126,6.59,0.520),(1e4,0.333,-0.136,None,None),
        (1e3,3.500,-0.476,None,None),(1e2,26.200,-0.913,None,None),(10,32.000,-1.000,None,None)],
    90:[(1e5,0.391,-0.148,6.30,0.378),(1e4,0.0815,+0.022,None,None),
        (1e3,6.090,-0.602,None,None),(1e2,32.100,-0.963,None,None),(10,35.000,-1.000,None,None)],
}
K1N={
    (1,30):(0.319,2.142),(1,45):(0.319,2.142),(1,60):(0.319,2.142),(1,90):(0.215,2.207),
    (2,30):(0.249,2.207),(2,45):(0.249,2.207),(2,60):(0.249,2.207),(2,90):(0.156,2.291),
    (4,30):(0.175,2.285),(4,45):(0.175,2.285),(4,60):(0.175,2.285),(4,90):(0.158,2.263),
    (6,30):(0.0743,2.499),(6,45):(0.0743,2.499),(6,60):(0.0743,2.499),(6,90):(0.0402,2.617),
    (8,30):(0.0365,2.675),(8,45):(0.0365,2.675),(8,60):(0.0365,2.675),(8,90):(0.0331,2.643),
}

# Inicialização de estados padrões de sessão para evitar chaves nulas
for k, v in [
    ("k_Ds", "0.387"), ("k_Ltp", "0.025"), ("k_Nt", "158"), ("k_d", "0.01905"), ("k_ep", "0.00165"),
    ("b_Ds", "0.387"), ("b_Ltp", "0.025"), ("b_Nt", "158"), ("b_d", "0.01905"), ("b_ep", "0.00165"),
    ("b_Lbc", "0.200"), ("b_Lbi", "0.200"), ("b_Lbo", "0.200"), ("b_Lbb", "11.00"), ("b_Ltb", "0.8")
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── HELPERS DE CONVERSÃO E INTERFACE ────────────────────────────
def tinput(label, key, default="", help=None):
    v = st.session_state.get(key, str(default))
    return st.text_input(label, value=v, key=key, help=help)

def parse(s, name="campo"):
    try:
        return float(str(s).replace(",", ".").strip())
    except Exception:
        raise ValueError(f"Valor inválido em '{name}': '{s}'")

def iparse(s, name="campo"):
    return int(parse(s, name))

# ─── FUNÇÕES DE DIAGNÓSTICO DE ÁREA REINTEGRADAS ─────────────────
def diagnostico_area(excesso, A_calc, A_inst, Nt, Lta, d, Ltp):
    Nt_sug  = max(1, math.ceil(A_calc / (math.pi * d * Lta))) if Lta > 0 else 0
    Lta_sug = A_calc / (Nt * math.pi * d) if Nt > 0 else 0.0
    A_alvo  = A_calc * 1.15
    Nt_alvo  = max(1, math.ceil(A_alvo / (math.pi * d * Lta))) if Lta > 0 else 0
    Lta_alvo = A_alvo / (Nt * math.pi * d) if Nt > 0 else 0.0

    linhas = ["\n──── DIAGNÓSTICO — EXCESSO DE ÁREA ────────────"]
    if excesso < 0:
        linhas += [
            "  ╔══════════════════════════════════════════╗",
            "  ║  ✖  ÁREA INSUFICIENTE — PROJETO INVIÁVEL ║",
            "  ╚══════════════════════════════════════════╝",
            f"  A instalada ({A_inst:.4f} m²) é MENOR que a necessária ({A_calc:.4f} m²).",
            "  O trocador não consegue transferir o calor requerido.",
            "",
            "  ► Como corrigir (escolha uma das opções):",
            f"    • Aumentar Nt para pelo menos {Nt_sug} tubos (Sugerido com 15% folga: {Nt_alvo} tubos)",
            f"    • Aumentar Lta para pelo menos {Lta_sug:.3f} m (Sugerido com 15% folga: {Lta_alvo:.3f} m)",
            "    • Reduzir o passo Ltp para aumentar Nt no mesmo casco ou aumentar Ds",
        ]
    elif excesso < 10:
        linhas += [
            "  ╔══════════════════════════════════════════╗",
            "  ║  ⚠  MARGEM MUITO ESTREITA (< 10 %)       ║",
            "  ╚══════════════════════════════════════════╝",
            "  O trocador é viável, mas sem folga para fouling ou oscilações de processo.",
            f"  ► Recomendação: Aumentar Nt para ~{Nt_alvo} tubos ou Lta para ~{Lta_alvo:.3f} m",
        ]
    elif excesso <= 25:
        linhas += [
            "  ╔══════════════════════════════════════════╗",
            "  ║  ✔  PROJETO ADEQUADO  (10 – 25 %)        ║",
            "  ╚══════════════════════════════════════════╝",
            "  Excesso de área ideal e balanceado conforme recomendações clássicas.",
        ]
    elif excesso <= 35:
        linhas += [
            "  ╔══════════════════════════════════════════╗",
            "  ║  ⚠  LEVE SUPERDIMENSIONAMENTO (25–35 %)  ║",
            "  ╚══════════════════════════════════════════╝",
            "  Gasto desnecessário de material. Pode otimizar reduzindo Nt ou Lta.",
        ]
    else:
        linhas += [
            "  ╔══════════════════════════════════════════╗",
            "  ║  ✖  SUPERDIMENSIONAMENTO EXCESSIVO > 35% ║",
            "  ╚══════════════════════════════════════════╝",
            "  Área crítica excessiva. Risco de baixas velocidades e rápida deposição de fouling.",
            f"  ► Recomendado reduzir Nt para ~{Nt_alvo} tubos ou utilizar casco menor.",
        ]
    return "\n".join(linhas)

def diagnostico_bd(excesso, A_calc, A_inst, Nt, Lta, d, geo, fat, Res, Bc, Lbc, Ltp, Np):
    linhas = [diagnostico_area(excesso, A_calc, A_inst, Nt, Lta, d, Ltp)]
    linhas += ["", "── ANÁLISE DOS FATORES DE CORREÇÃO J (BELL-DELAWARE) ──"]
    ProdJ = fat["Jc"] * fat["Jl"] * fat["Jb"] * fat["Js"] * fat["Jr"]
    linhas += [f"  ∏J = {ProdJ:.4f} (Eficiência real global vs. Feixe de tubos ideal)"]
    
    if ProdJ < 0.60:
        linhas.append("  ⚠ ∏J < 0.60: Eficiência muito baixa. Percursos secundários severos.")
    if fat["Jl"] < 0.75:
        linhas.append(f"  ⚠ Jl = {fat['Jl']:.4f}: Vazamento tubo-chicana/casco elevado. Adicione tiras de vedação (Nss).")
    if fat["Jb"] < 0.85:
        linhas.append(f"  ⚠ Jb = {fat['Jb']:.4f}: Corrente de bypass feixe-casco expressiva. Reduza folga Lbb ou use Nss.")
    if fat["Jc"] < 0.90:
        linhas.append(f"  ⚠ Jc = {fat['Jc']:.4f}: Poucos tubos em escoamento cruzado. Reduza o corte da chicana Bc.")
    if Res < 100:
        linhas.append(f"  ⚠ Res = {Res:.0f}: Regime predominantemente LAMINAR no casco. Reduza Lbc para acelerar o fluido.")
    return "\n".join(linhas)

# ─── FUNÇÕES DE CALLBACK PARA MODIFICAÇÃO DE ESTADO SEGURA ───────
def callback_usar_db_kern():
    if "k_db_result" in st.session_state:
        r = st.session_state["k_db_result"]
        st.session_state["k_Ds"] = f"{r['Ds']:.4f}"
        st.session_state["k_Ltp"] = f"{r['Ltp_sug']:.5f}"
        del st.session_state["k_db_result"]

def callback_usar_db_bd():
    if "b_db_result" in st.session_state:
        r = st.session_state["b_db_result"]
        st.session_state["b_Ds"] = f"{r['Ds']:.4f}"
        st.session_state["b_Ltp"] = f"{r['Ltp_sug']:.5f}"
        del st.session_state["b_db_result"]

def callback_igualar_L_bd():
    lbc_atual = st.session_state.get("b_Lbc", "0.200")
    st.session_state["b_Lbi"] = lbc_atual
    st.session_state["b_Lbo"] = lbc_atual

def callback_recalcular_folgas_bd():
    try:
        ds_mm = float(st.session_state.get("b_Ds", "0.387").replace(",", ".").strip()) * 1000
        f_t = folgas_tema(ds_mm)
        st.session_state["b_Lbb"] = f"{f_t['Lbb_mm']:.2f}"
    except ValueError:
        pass

# ─── MOTOR PRINCIPAL DE SIMULAÇÃO TÉRMICA ────────────────────────
def _lookup(tab, theta, Re):
    tk = min([30, 45, 90], key=lambda t: abs(t - theta))
    ent = tab[tk]
    for (Rm,a1,a2,a3,a4) in reversed(ent):
        if Re <= Rm: return a1,a2,a3,a4
    return ent[0][1],ent[0][2],ent[0][3],ent[0][4]

def folgas_tema(Ds_mm):
    Lbb = 9.5 if Ds_mm<=300 else 11.0 if Ds_mm<=500 else 12.7 if Ds_mm<=700 else 15.9
    return {"Lbb_mm":Lbb,"Lsb_mm":round(3.1+0.004*Ds_mm,2),"Ltb_mm":0.8}

def bundle_diameter(Nt,do,Np,theta):
    key=(Np,theta) if (Np,theta) in K1N else (Np,90)
    K1,n1=K1N[key]
    Db=do*(Nt/K1)**(1/n1)
    Lbb=folgas_tema(Db*1000)["Lbb_mm"]/1000
    return {"Db":Db,"Ds":Db+Lbb,"K1":K1,"n1":n1,"Ltp_sug":do*1.25}

def mu_parede(mu_bulk,T_bulk,T_w,fase="liquido"):
    Tbk=T_bulk+273.15; Twk=T_w+273.15
    if abs(Tbk-Twk)<0.5: return mu_bulk
    if fase.lower().startswith("g"):
        ratio=(Twk/Tbk)**0.7
    else:
        B=-math.log(mu_bulk)*Tbk if mu_bulk<1 else 5000.0
        expo=max(-4.6,min(4.6,B*(1/Twk-1/Tbk)))
        ratio=max(0.01,min(100.0,math.exp(expo)))
    return mu_bulk*ratio

def mu_iter(Tq,Tf,Rp,get_mq,get_mf,h_casco_fn,h_tubo_fn,tol=0.1,maxn=50):
    Twq=Twf=(Tq+Tf)/2; conv=False; mwq=get_mq(Twq); mwf=get_mf(Twf); it=1
    for it in range(1,maxn+1):
        mwq=get_mq(Twq); mwf=get_mf(Twf)
        try: hq=max(1e-6,h_casco_fn(mwq)); hf=max(1e-6,h_tubo_fn(mwf))
        except: break
        Rq=1/hq; Rf=1/hf; Rt=Rq+Rp+Rf
        Q=(Tq-Tf)/Rt if Rt>0 else 0
        nTwq=Tq-Q*Rq; nTwf=nTwq-Q*Rp
        if max(abs(nTwq-Twq),abs(nTwf-Twf))<tol: Twq,Twf=nTwq,nTwf; conv=True; break
        Twq,Twf=nTwq,nTwf
    mbq=get_mq(Tq); mbf=get_mf(Tf)
    phq=(mbq/mwq)**0.14 if mwq > 0 else 1.0
    phf=(mbf/mwf)**0.14 if mwf > 0 else 1.0
    return {"Twq":Twq,"Twf":Twf,"mwq":mwq,"mwf":mwf,"phq":phq,"phf":phf,"it":it,"conv":conv}

def lmtd(Thi,Tho,Tci,Tco):
    d1,d2=Thi-Tco,Tho-Tci
    if d1<=0 or d2<=0: raise ValueError("ΔT ≤ 0 — verifique as temperaturas")
    return d1 if abs(d1-d2)<1e-6 else (d1-d2)/math.log(d1/d2)

def fator_F(Thi,Tho,Tci,Tco,Np):
    if Np==1: return 1.0
    R=(Thi-Tho)/(Tco-Tci) if Tco!=Tci else 1.0
    P=(Tco-Tci)/(Thi-Tci) if Thi!=Tci else 0.5
    if abs(R-1)<1e-4:
        if P>=1: return 0.5
        val=P/(1-P)
        if val<=0: return 1.0
        try: F=math.sqrt(2)*val/math.log((1-P)/(1-P*(1+1/val)))
        except: F=1.0
    else:
        S=math.sqrt(R**2+1)/(R-1)
        arg=(2/P-1-R+math.sqrt(R**2+1))/(2/P-1-R-math.sqrt(R**2+1))
        if arg<=0: return 0.75
        try: F=S*math.log((1-P)/(1-P*R))/math.log(arg)
        except: F=0.85
    return max(0.5,min(1.0,F))

def coef_global(hs,ht,d,di,kp,Q,dTlm,Rfe=0,Rfi=0,F=1):
    Re=1/hs; Rc=d*math.log(d/di)/(2*kp); Ri=(d/di)/ht
    Rf=Rfe+(d/di)*Rfi; U=1/(Re+Rc+Ri+Rf)
    A=Q/(U*dTlm*F) if dTlm>0 and F>0 else 0
    return {"U":U,"A":A,"Re":Re,"Rc":Rc,"Ri":Ri,"Rf":Rf}

def resolver_T(obj,Thi,Tci,Tval,ms,cps,mt,cpt,Q_lat_s=0,Q_lat_t=0):
    if "Th,o" in obj:
        Tho=Tval; Q=ms*cps*(Thi-Tho)+Q_lat_s
        if Q<=0: raise ValueError("Q≤0: Th,o deve ser menor que Th,i")
        Tco=Tci+(Q-Q_lat_t)/(mt*cpt)
    else:
        Tco=Tval; Q=mt*cpt*(Tco-Tci)+Q_lat_t
        if Q<=0: raise ValueError("Q≤0: Tc,o deve ser maior que Tc,i")
        Tho=Thi-(Q-Q_lat_s)/(ms*cps)
    return Tho,Tco,Q

# ─── RELAÇÕES GEOMÉTRICAS E SUB-ROTINAS KERN ─────────────────────
def kern_geo(d,di,Lta,Ltp,theta,Ds,Lbc,Np):
    Dhs=4*(Ltp**2-math.pi*d**2/4)/(math.pi*d) if theta in(45,90) else \
        4*(0.866*Ltp**2/2-math.pi*d**2/8)/(math.pi*d/2)
    return{"Dhs":Dhs,"C":Ltp-d,"Atc":Ds*(Ltp-d)*Lbc/Ltp}

def kern_casco(ms,mu_s,cp_s,k_s,geo):
    Gs=ms/geo["Atc"]; Res=geo["Dhs"]*Gs/mu_s; Prs=mu_s*cp_s/k_s
    return{"Gs":Gs,"Res":Res,"Prs":Prs,"hs":(0.36*k_s/geo["Dhs"])*Res**0.55*Prs**(1/3)}

def kern_dPs(Gs,Res,rho_s,Ds,Dhs,mu_s,mws,Nb):
    phi=(mu_s/mws)**0.14; Rc=max(Res,400)
    fs=math.exp(0.576-0.19*math.log(Rc))
    return{"fs":fs,"dPs":fs*Gs**2*(Nb+1)*Ds/(2*rho_s*Dhs*phi),"fora":Res<400}

def kern_tubos(mt,rho_t,mu_t,cp_t,k_t,mwt,d,di,Lta,Nt,Np):
    At=math.pi/4*di**2*Nt; Gt=mt/(At/Np); Ret=di*Gt/mu_t; Prt=mu_t*cp_t/k_t
    if Ret<2300:
        arg=max(Ret*Prt*di/Lta,1e-6)
        Nut=max(3.66,1.86*arg**(1/3)*(mu_t/mwt)**0.14); reg="Laminar (Sieder-Tate)"
    elif Ret>10000:
        Nut=0.027*Ret**0.8*Prt**(1/3)*(mu_t/mwt)**0.14; reg="Turbulento (Sieder-Tate)"
    else:
        fp=(0.790*math.log(Ret)-1.64)**(-2)
        dn=1+12.7*math.sqrt(fp/8)*(Prt**(2/3)-1)
        Nut=max(3.66,(fp/8)*(Ret-1000)*Prt/dn*(mu_t/mwt)**0.14 if dn>0 else 10); reg="Transição (Gnielinski)"
    ft=64/Ret if Ret<2300 else 0.3164/Ret**0.25
    phi=(mu_t/mwt)**0.14 if Ret>=2300 else (mu_t/mwt)**0.25
    dPf=ft*(Lta/di)*(Gt**2/(2*rho_t))*(1/phi)*Np
    dPr=4*max(Np-1,0)*(Gt**2/(2*rho_t))
    return{"Gt":Gt,"vt":Gt/rho_t,"Ret":Ret,"Prt":Prt,"Nut":Nut,"ht":Nut*k_t/di,
           "ft":ft,"dPt":dPf+dPr,"dPf":dPf,"dPr":dPr,"reg":reg}

# ─── CONTEXTO GEOMÉTRICO BELL-DELAWARE ───────────────────────────
def bd_geo(d,Lta,Ltp,theta,Ds,Bc,Lbc,Lbi,Lbo,Nt,Nss,Lbb_m=None,Ltb_m=8e-4):
    Lbb = Lbb_m if Lbb_m is not None else (12+0.005*(Ds*1000))/1000
    Dotl=Ds-Lbb; Dctl=Dotl-d; Nb=max(1,int(Lta/Lbc)-1)
    ads=max(-1,min(1,1-2*Bc/100)); tds=2*math.acos(ads)
    act=max(-1,min(1,(Ds/Dctl)*(1-2*Bc/100))); tct=2*math.acos(act)
    Leff=0.707*Ltp if theta==45 else Ltp
    Sm=Lbc*(Lbb+Dctl/Leff*(Ltp-d))
    Swg=(math.pi/4)*Ds**2*(tds/(2*math.pi)-math.sin(tds)/(2*math.pi))
    Fw=tct/(2*math.pi)-math.sin(tct)/(2*math.pi); Fc=1-2*Fw
    Nwt=Nt*Fw; Swt=Nwt*math.pi/4*d**2; Sw=Swg-Swt
    dDw=math.pi*d*Nwt+math.pi*Ds*tds/(2*math.pi)
    Dw=4*Sw/dDw if dDw>0 else 1e-3
    Lpp={30:Ltp*0.866,45:Ltp*0.707,60:Ltp*0.866,90:Ltp}.get(theta,Ltp)
    Ntcc=abs(Ds/Lpp*(1-2*Bc/100)); Ntcw=max(0,0.8/Lpp*(Ds*Bc/100-(Ds-Dctl)/2))
    Sb=Lbc*(Ds-Dotl); Fsbp=Sb/Sm
    Lsb=(3.1+0.004*(Ds*1000))/1000
    Ssb=math.pi*Ds*(Lsb/2)*(2*math.pi-tds)/(2*math.pi)
    Stb=math.pi*d*Ltb_m*Nt*(1-Fw)
    return{"Lbb":Lbb,"Nb":Nb,"tds":tds,"tct":tct,"Sm":Sm,"Sw":Sw,"Dw":Dw,
           "Fc":Fc,"Fw":Fw,"Nwt":Nwt,"Ntcc":Ntcc,"Ntcw":Ntcw,"Sb":Sb,"Fsbp":Fsbp,
           "Ssb":Ssb,"Stb":Stb,"Lbc":Lbc}

def bd_fat(geo,Res,Nb,Lbi,Lbo,Lbc,Nss):
    Fc=geo["Fc"]; Ssb=geo["Ssb"]; Stb=geo["Stb"]
    Sm=geo["Sm"]; Fsbp=geo["Fsbp"]; Ntcc=geo["Ntcc"]; Ntcw=geo["Ntcw"]
    Jc=0.55+0.72*Fc
    rs=Ssb/(Ssb+Stb); rlm=(Ssb+Stb)/Sm; x=-0.15*(1+rs)+0.8
    Jl=0.44*(1-rs)+(1-0.44*(1-rs))*math.exp(-2.2*rlm)
    Rl=math.exp(-1.33*(1+rs)*rlm**x)
    rss=min(Nss/Ntcc if Ntcc>0 else 0,0.5)
    Cbh=1.35 if Res>100 else 1.25; Cbp=3.7 if Res>100 else 4.5
    if rss>=0.5: Jb=Rb=1.0
    else:
        fj=(2*rss)**(1/3) if rss>0 else 0; fr=rss**(1/3) if rss>0 else 0
        Jb=math.exp(-Cbh*Fsbp*(1-fj)); Rb=math.exp(-Cbp*Fsbp*(1-fr))
    Nc=(Ntcc+Ntcw)*(Nb+1)
    if Res>100: Jr=1.0
    elif Res<=20: Jr=max(0.4,1.51/Nc**0.18)
    else: Jr_l=1.51/Nc**0.18; Jr=max(0.4,Jr_l+(20-Res)/80*(Jr_l-1))
    Li=Lbi/Lbc; Lo=Lbo/Lbc; nJ=0.6 if Res>100 else 1.0
    Js_n=(Nb-1)+Li**(1-nJ)+Lo**(1-nJ)
    Js_d=(Nb-1)+Li+Lo if Nb>1 else Li+Lo
    Js=Js_n/Js_d if Js_d!=0 else 1.0
    nR=0.2 if Res>100 else 1.0
    Rs=0.5*(Li**(nR-2)+Lo**(nR-2))
    return{"Jc":Jc,"Jl":Jl,"Jb":Jb,"Js":Js,"Jr":Jr,"Rl":Rl,"Rb":Rb,"Rs":Rs}

def bd_casco(ms,mu_s,cp_s,k_s,mws,d,Ltp,theta,geo,fat):
    Gs=ms/geo["Sm"]; Res=d*Gs/mu_s; Prs=mu_s*cp_s/k_s
    tk=min([30,45,90],key=lambda t:abs(t-theta))
    a1,a2,a3,a4=_lookup(TAB10,tk,Res)
    a=a3/(1+0.14*Res**a4) if a3 else 0.0
    ji=a1*(1.33/(Ltp/d))**a*Res**a2; phi=(mu_s/mws)**0.14
    hi=ji*cp_s*Gs*phi/Prs**(2/3)
    hs=hi*fat["Jc"]*fat["Jl"]*fat["Jb"]*fat["Js"]*fat["Jr"]
    return{"Gs":Gs,"Res":Res,"Prs":Prs,"ji":ji,"phi":phi,"hi":hi,"hs":hs}

def bd_dPs(ms,rho_s,mu_s,mws,d,Ltp,theta,geo,fat):
    Sm=geo["Sm"]; Sw=geo["Sw"]; Dw=geo["Dw"]
    Ntcc=geo["Ntcc"]; Ntcw=geo["Ntcw"]; Nb=geo["Nb"]; Lbc=geo["Lbc"]
    Gs=ms/Sm; Res=d*Gs/mu_s
    tk=min([30,45,90],key=lambda t:abs(t-theta))
    b1,b2,b3,b4=_lookup(TAB11,tk,Res)
    b=b3/(1+0.14*Res**b4) if b3 else 0.0
    fs=b1*(1.33/(Ltp/d))**b*Res**b2; phi_i=(mu_s/mws)**(-0.14)
    dPbi=2*fs*Ntcc*Gs**2/rho_s*phi_i
    dPc=(Nb-1)*dPbi*fat["Rb"]*fat["Rl"] if Nb>1 else 0
    r=Ntcw/Ntcc if Ntcc>0 else 0
    dPe=2*dPbi*(1+r)*fat["Rb"]*fat["Rs"]
    Gw=ms/math.sqrt(Sm*Sw) if Sw>0 else 1e-6
    dPwi=(2+0.6*Ntcw)*Gw**2/(2*rho_s) if Res>=100 else \
         26*Gw*mu_s/rho_s*(Ntcw/(Ltp-d)+Lbc/Dw)+2*Gw**2/rho_s
    dPw=dPwi*Nb*fat["Rl"] if Nb>0 else 0
    return{"fs":fs,"dPc":dPc,"dPw":dPw,"dPe":dPe,"dPs":dPc+dPw+dPe}


# ─── MONTAGEM E RENDERIZAÇÃO DA INTERFACE STREAMLIT ──────────────
st.title("⚙️ Simulador Casco-e-Tubo")
st.caption("**Kern** & **Bell-Delaware** |  v5  |  Streamlit Engenharia Avançada")
st.divider()

tab_k, tab_b = st.tabs(["🔵  KERN", "🟠  BELL-DELAWARE"])

# ═════════════════════════════════════════════════════════════════
# ABA KERN
# ═════════════════════════════════════════════════════════════════
with tab_k:
    L, R = st.columns([1,1], gap="large")
    with L:
        st.subheader("🌡️ Temperaturas")
        k_Thi=parse(tinput("Th,i — quente entrada (°C)","k_Thi","100"),"Th,i")
        k_Tci=parse(tinput("Tc,i — frio entrada (°C)","k_Tci","20"),"Tc,i")
        k_obj=st.radio("Objetivo:",["Th,o → calcula Tc,o","Tc,o → calcula Th,o"], horizontal=True,key="k_obj")
        lbl="Th,o (°C)" if "Th,o" in k_obj else "Tc,o (°C)"
        k_Tsaida=parse(tinput(lbl,"k_Tsaida","60"),"T saída")

        st.divider()
        st.subheader("⚡ Limites de ΔP")
        k_pre=st.selectbox("Preset serviço:",list(LIMITES_DP.keys()),key="k_pre")
        ds0,dt0,ref0=LIMITES_DP[k_pre]
        if ds0>0: st.caption(f"Ref: {ref0}  |  ΔPs={ds0} kPa  ΔPt={dt0} kPa")
        if k_pre!="Personalizado" and ds0>0:
            st.session_state["k_dPs_max"]=str(ds0); st.session_state["k_dPt_max"]=str(dt0)
        k_dPs_max=parse(tinput("ΔPmax casco (kPa)","k_dPs_max","70"),"ΔPmax casco")
        k_dPt_max=parse(tinput("ΔPmax tubos (kPa)","k_dPt_max","100"),"ΔPmax tubos")

        st.divider()
        st.subheader("🔵 Fluido — Casco (quente)")
        c1,c2=st.columns(2)
        with c1:
            k_rho_s=parse(tinput("ρₛ (kg/m³)","k_rho_s","983"),"ρs")
            k_cp_s=parse(tinput("cp,s (J/kg·K)","k_cp_s","4190"),"cp,s")
        with c2:
            k_mu_s=parse(tinput("μₛ (Pa·s)","k_mu_s","0.00046"),"μs")
            k_k_s=parse(tinput("kₛ (W/m·K)","k_k_s","0.659"),"ks")
        k_ms=parse(tinput("ṁₛ (kg/s)","k_ms","4.3"),"ṁs")

        st.divider()
        st.subheader("🔵 Fluido — Tubos (frio)")
        c1,c2=st.columns(2)
        with c1:
            k_rho_t=parse(tinput("ρₜ (kg/m³)","k_rho_t","998"),"ρt")
            k_cp_t=parse(tinput("cp,t (J/kg·K)","k_cp_t","4182"),"cp,t")
        with c2:
            k_mu_t=parse(tinput("μₜ (Pa·s)","k_mu_t","0.00089"),"μt")
            k_k_t=parse(tinput("kₜ (W/m·K)","k_k_t","0.600"),"kt")
        k_mt=parse(tinput("ṁₜ (kg/s)","k_mt","5.7"),"ṁt")

        st.divider()
        with st.expander("⇌ Mudança de Fase (calor latente)", expanded=False):
            k_fase_on=st.checkbox("Ativar mudança de fase",key="k_fase_on")
            if k_fase_on:
                k_fase_lado=st.radio("Lado afetado:",["Casco (quente)","Tubos (frio)"],key="k_fase_lado")
                k_lam=parse(tinput("Calor latente λ (kJ/kg)","k_lam","2257"),"λ")*1000
                k_frac=parse(tinput("Fração de mudança x [0-1]","k_frac","1.0"),"x")
            else:
                k_fase_lado=""; k_lam=0; k_frac=0

        st.divider()
        st.subheader("📐 Geometria — Tubo")
        k_d=parse(tinput("do externo (m)","k_d","0.01905"),"do")
        k_ep=parse(tinput("Espessura e (m)","k_ep","0.00165"),"e")
        k_di=k_d-2*k_ep
        st.caption(f"di calculado = **{k_di*1000:.3f} mm**")
        k_mat=st.selectbox("Material:",list(MATERIAIS.keys()),key="k_mat")
        k_kpar=MATERIAIS[k_mat]

        st.divider()
        st.subheader("🏗️ Casco e Chicanas")
        k_Ds=parse(tinput("Ds — diâm. casco (m)","k_Ds","0.387"),"Ds")
        k_Lta=parse(tinput("Lta — comp. tubo (m)","k_Lta","4.877"),"Lta")
        k_Ltp=parse(tinput("Ltp — passo tubos (m)","k_Ltp","0.025"),"Ltp")
        k_Lbc=parse(tinput("Lbc — espaç. chicanas (m)","k_Lbc","0.200"),"Lbc")
        k_Nt=iparse(tinput("Nt — nº tubos","k_Nt","158"),"Nt")
        k_Nb=max(1,int(k_Lta/k_Lbc)-1) if k_Lbc>0 else 1
        k_theta=st.selectbox("Ângulo θ:",[30,45,60,90],key="k_theta")
        k_Np=st.selectbox("Passes Np:",[1,2,4,6,8],key="k_Np")

        with st.expander("📐 Estimar Db → Ds (Coulson & Richardson)"):
            if st.button("Calcular Db e Ds",key="k_btn_db"):
                st.session_state["k_db_result"]=bundle_diameter(k_Nt,k_d,k_Np,k_theta)
            if "k_db_result" in st.session_state:
                r=st.session_state["k_db_result"]
                st.success(f"**Db = {r['Db']*1000:.1f} mm** |  **Ds estimado = {r['Ds']*1000:.1f} mm**")
                st.button("↑  Usar estes valores nos campos acima",key="k_usar_db",on_click=callback_usar_db_kern)

        st.divider()
        st.subheader("🔧 Fouling (TEMA)")
        k_fp=st.selectbox("Preset:",list(FOULING_PRESETS.keys()),key="k_fp")
        fe0,fi0=FOULING_PRESETS[k_fp]
        if k_fp!="Personalizado":
            st.session_state["k_Rfe"]=str(fe0); st.session_state["k_Rfi"]=str(fi0)
        k_Rfe=parse(tinput("Rf ext (m²·K/W)","k_Rfe",str(fe0)),"Rf ext")
        k_Rfi=parse(tinput("Rf int (m²·K/W)","k_Rfi",str(fi0)),"Rf int")

        st.divider()
        calcular_k=st.button("▶ CALCULAR — KERN",type="primary",use_container_width=True,key="btn_k")

    with R:
        st.subheader("📊 Resultados — Kern")
        if calcular_k:
            try:
                Q_lat_s=k_ms*k_lam*k_frac if k_fase_on and "Casco" in k_fase_lado else 0
                Q_lat_t=k_mt*k_lam*k_frac if k_fase_on and "Tubo" in k_fase_lado else 0

                Tho,Tco,Q_W=resolver_T(k_obj,k_Thi,k_Tci,k_Tsaida,k_ms,k_cp_s,k_mt,k_cp_t,Q_lat_s,Q_lat_t)
                dTlm=lmtd(k_Thi,Tho,k_Tci,Tco)
                F=fator_F(k_Thi,Tho,k_Tci,Tco,k_Np)
                Tbs=(k_Thi+Tho)/2; Tbt=(k_Tci+Tco)/2
                Rp=k_d*math.log(k_d/k_di)/(2*k_kpar) if k_di>0 else 0

                geo0=kern_geo(k_d,k_di,k_Lta,k_Ltp,k_theta,k_Ds,k_Lbc,k_Np)
                
                # CALIBRAÇÃO DA RESISTÊNCIA DE PAREDE KERN: Inserindo mw na chamada da sub-rotina
                def hck(mw):
                    base_hs = kern_casco(k_ms,k_mu_s,k_cp_s,k_k_s,geo0)["hs"]
                    return base_hs * ((k_mu_s/mw)**0.14 if mw>0 else 1.0)
                def htk(mw): 
                    return kern_tubos(k_mt,k_rho_t,k_mu_t,k_cp_t,k_k_t,mw,k_d,k_di,k_Lta,k_Nt,k_Np)["ht"]
                
                fase_s = "gas" if k_fase_on and "Casco" in k_fase_lado else "liquido"
                mw=mu_iter(Tbs,Tbt,Rp,lambda T:mu_parede(k_mu_s,Tbs,T,fase=fase_s),lambda T:mu_parede(k_mu_t,Tbt,T),hck,htk)

                geo=kern_geo(k_d,k_di,k_Lta,k_Ltp,k_theta,k_Ds,k_Lbc,k_Np)
                cas=kern_casco(k_ms,k_mu_s,k_cp_s,k_k_s,geo)
                hs_real = cas["hs"] * mw["phq"]

                prs=kern_dPs(cas["Gs"],cas["Res"],k_rho_s,k_Ds,geo["Dhs"],k_mu_s,mw["mwq"],k_Nb)
                tub=kern_tubos(k_mt,k_rho_t,k_mu_t,k_cp_t,k_k_t,mw["mwf"],k_d,k_di,k_Lta,k_Nt,k_Np)
                
                gl=coef_global(hs_real,tub["ht"],k_d,k_di,k_kpar,Q_W,dTlm,k_Rfe,k_Rfi,F)
                Ai=k_Nt*math.pi*k_d*k_Lta; ex=(Ai/gl["A"]-1)*100 if gl["A"]>0 else 0

                m1,m2,m3,m4=st.columns(4)
                m1.metric("U (W/m²·K)",f"{gl['U']:.1f}")
                m2.metric("Área calc. (m²)",f"{gl['A']:.3f}")
                m3.metric("Área inst. (m²)",f"{Ai:.3f}")
                m4.metric("Excesso (%)",f"{ex:.1f}")
                
                m1,m2,m3,m4=st.columns(4)
                m1.metric("Q (kW)",f"{Q_W/1000:.2f}")
                m2.metric("LMTD (°C)",f"{dTlm:.2f}")
                m3.metric("F",f"{F:.4f}")
                m4.metric("ΔPs (kPa)",f"{prs['dPs']/1000:.2f}")

                if F<0.75: st.warning("⚠️ F < 0,75 — considere mais passes ou 2 cascos em série")

                st.subheader("Verificação ΔP")
                dPs=prs["dPs"]/1000; dPt=tub["dPt"]/1000
                c1,c2=st.columns(2)
                c1.metric("ΔPs (kPa)",f"{dPs:.3f}",f"Máx {k_dPs_max:.1f} — {'✓ OK' if dPs<=k_dPs_max else '⚠ EXCEDE'}")
                c2.metric("ΔPt (kPa)",f"{dPt:.3f}",f"Máx {k_dPt_max:.1f} — {'✓ OK' if dPt<=k_dPt_max else '⚠ EXCEDE'}")

                diag_text = diagnostico_area(ex, gl["A"], Ai, k_Nt, k_Lta, k_d, k_Ltp)

                txt=f"""
╔═══════════════════════════════════════════╗
║      RESULTADO — MÉTODO DE KERN           ║
╚═══════════════════════════════════════════╝

─── TEMPERATURAS ───────────────────────────
  Quente : {k_Thi:.2f} → {Tho:.2f} °C
  Frio   : {k_Tci:.2f} → {Tco:.2f} °C

─── BALANÇO ────────────────────────────────
  Q total  = {Q_W/1000:.4f} kW
  Q latente= {(Q_lat_s+Q_lat_t)/1000:.4f} kW
  LMTD     = {dTlm:.4f} °C  |  F = {F:.4f}

─── PAREDE (iterativo: {mw['it']} iter {'✓' if mw['conv'] else '⚠'}) ──────
  Tw casco = {mw['Twq']:.2f}°C  μw,s={mw['mwq']:.3e}  φs={mw['phq']:.4f}
  Tw tubo  = {mw['Twf']:.2f}°C  μw,t={mw['mwf']:.3e}  φt={mw['phf']:.4f}

─── COEFICIENTES DE FILME ──────────────────
  hs real  = {hs_real:.2f} W/m²·K (base ideal hs = {cas['hs']:.2f})
  ht real  = {tub['ht']:.2f} W/m²·K

─── GEOMETRIA ──────────────────────────────
  Nb={k_Nb}  Dhs={geo['Dhs']*1000:.2f}mm  Atc={geo['Atc']*1e4:.4f}cm²

─── CASCO ──────────────────────────────────
  Gs={cas['Gs']:.4f} kg/m²s  Re={cas['Res']:.0f}  Pr={cas['Prs']:.4f}
  ΔPs={prs['dPs']:.2f}Pa ({prs['dPs']/1000:.4f}kPa){'  ⚠Re<400' if prs['fora'] else ''}

─── TUBOS ──────────────────────────────────
  Re={tub['Ret']:.0f} [{tub['reg']}]
  Nu={tub['Nut']:.4f}  v={tub['vt']:.3f}m/s
  ΔPt total={tub['dPt']:.2f}Pa ({tub['dPt']/1000:.4f}kPa)

─── GLOBAL ─────────────────────────────────
  U={gl['U']:.2f} W/m²K  | Área calc = {gl['A']:.4f} m² | Instalada = {Ai:.4f} m²
{diag_text}
"""
                st.markdown(f'<div class="result-box">{txt}</div>',unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro no cálculo: {e}")

# ═════════════════════════════════════════════════════════════════
# ABA BELL-DELAWARE
# ═════════════════════════════════════════════════════════════════
with tab_b:
    L,R=st.columns([1,1],gap="large")
    with L:
        st.subheader("🌡️ Temperaturas")
        b_Thi=parse(tinput("Th,i — quente entrada (°C)","b_Thi","100"),"Th,i")
        b_Tci=parse(tinput("Tc,i — frio entrada (°C)","b_Tci","20"),"Tc,i")
        b_obj=st.radio("Objetivo:",["Th,o → calcula Tc,o","Tc,o → calcula Th,o"],horizontal=True,key="b_obj")
        lbl="Th,o (°C)" if "Th,o" in b_obj else "Tc,o (°C)"
        b_Tsaida=parse(tinput(lbl,"b_Tsaida","60"),"T saída")

        st.divider()
        st.subheader("⚡ Limites de ΔP")
        b_pre=st.selectbox("Preset serviço:",list(LIMITES_DP.keys()),key="b_pre")
        ds1,dt1,ref1=LIMITES_DP[b_pre]
        if ds1>0: st.caption(f"Ref: {ref1}  |  ΔPs={ds1} kPa  ΔPt={dt1} kPa")
        if b_pre!="Personalizado" and ds1>0:
            st.session_state["b_dPs_max"]=str(ds1); st.session_state["b_dPt_max"]=str(dt1)
        b_dPs_max=parse(tinput("ΔPmax casco (kPa)","b_dPs_max","70"),"ΔPmax casco")
        b_dPt_max=parse(tinput("ΔPmax tubos (kPa)","b_dPt_max","100"),"ΔPmax tubos")

        st.divider()
        st.subheader("🟠 Fluido — Casco (quente)")
        c1,c2=st.columns(2)
        with c1:
            b_rho_s=parse(tinput("ρₛ (kg/m³)","b_rho_s","983"),"ρs")
            b_cp_s=parse(tinput("cp,s (J/kg·K)","b_cp_s","4190"),"cp,s")
        with c2:
            b_mu_s=parse(tinput("μₛ (Pa·s)","b_mu_s","0.00046"),"μs")
            b_k_s=parse(tinput("kₛ (W/m·K)","b_k_s","0.659"),"ks")
        b_ms=parse(tinput("ṁₛ (kg/s)","b_ms","4.3"),"ṁs")

        st.divider()
        st.subheader("🟠 Fluido — Tubos (frio)")
        c1,c2=st.columns(2)
        with c1:
            b_rho_t=parse(tinput("ρₜ (kg/m³)","b_rho_t","998"),"ρt")
            b_cp_t=parse(tinput("cp,t (J/kg·K)","b_cp_t","4182"),"cp,t")
        with c2:
            b_mu_t=parse(tinput("μₜ (Pa·s)","b_mu_t","0.00089"),"μt")
            b_k_t=parse(tinput("kₜ (W/m·K)","b_k_t","0.600"),"kt")
        b_mt=parse(tinput("ṁₜ (kg/s)","b_mt","5.7"),"ṁt")

        st.divider()
        with st.expander("⇌ Mudança de Fase (calor latente)", expanded=False):
            b_fase_on=st.checkbox("Ativar mudança de fase",key="b_fase_on")
            if b_fase_on:
                b_fase_lado=st.radio("Lado afetado:",["Casco (quente)","Tubos (frio)"],key="b_fase_lado")
                b_lam=parse(tinput("Calor latente λ (kJ/kg)","b_lam","2257"),"λ")*1000
                b_frac=parse(tinput("Fração de mudança x [0-1]","b_frac","1.0"),"x")
            else:
                b_fase_lado=""; b_lam=0; b_frac=0

        st.divider()
        st.subheader("📐 Geometria — Tubo")
        b_d=parse(tinput("do externo (m)","b_d","0.01905"),"do")
        b_ep=parse(tinput("Espessura e (m)","b_ep","0.00165"),"e")
        b_di=b_d-2*b_ep
        st.caption(f"di calculado = **{b_di*1000:.3f} mm**")
        b_mat=st.selectbox("Material:",list(MATERIAIS.keys()),key="b_mat")
        b_kpar=MATERIAIS[b_mat]

        st.divider()
        st.subheader("🏗️ Casco e Chicanas")
        b_Ds=parse(tinput("Ds — diâm. casco (m)","b_Ds","0.387"),"Ds")
        b_Lta=parse(tinput("Lta — comp. tubo (m)","b_Lta","4.877"),"Lta")
        b_Ltp=parse(tinput("Ltp — passo tubos (m)","b_Ltp","0.025"),"Ltp")
        b_Bc=parse(tinput("Bc — corte chicana (%)","b_Bc","25"),"Bc")
        b_Lbc=parse(tinput("Lbc — espaç. central (m)","b_Lbc","0.200"),"Lbc")
        b_Lbi=parse(tinput("Lbi — espaç. entrada (m)","b_Lbi","0.200"),"Lbi")
        b_Lbo=parse(tinput("Lbo — espaç. saída (m)","b_Lbo","0.200"),"Lbo")
        st.button("↓  Lbi = Lbo = Lbc",key="b_igualar_L",on_click=callback_igualar_L_bd)
        
        b_Nss=parse(tinput("Nss — tiras vedação","b_Nss","1"),"Nss")
        b_Nt=iparse(tinput("Nt — nº tubos","b_Nt","158"),"Nt")
        b_theta=st.selectbox("Ângulo θ:",[30,45,90],key="b_theta")
        b_Np=st.selectbox("Passes Np:",[1,2,4,6,8],key="b_Np")

        with st.expander("📐 Estimar Db → Ds (Coulson & Richardson)"):
            if st.button("Calcular Db e Ds",key="b_btn_db"):
                st.session_state["b_db_result"]=bundle_diameter(b_Nt,b_d,b_Np,b_theta)
            if "b_db_result" in st.session_state:
                r=st.session_state["b_db_result"]
                st.success(f"**Db = {r['Db']*1000:.1f} mm** |  **Ds estimado = {r['Ds']*1000:.1f} mm**")
                st.button("↑ Usar estes valores",key="b_usar_db",on_click=callback_usar_db_bd)

        st.divider()
        st.subheader("📏 Folgas TEMA")
        f_t=folgas_tema(b_Ds*1000)
        
        # INTERAÇÃO SEGURA DAS FOLGAS TEMA VIA ON_CLICK CALLBACK
        b_Lbb=parse(tinput("Lbb (mm)","b_Lbb",str(f_t["Lbb_mm"])),"Lbb")/1000
        b_Ltb=parse(tinput("Ltb (mm)","b_Ltb","0.8"),"Ltb")/1000
        st.button("↻ Recalcular folgas TEMA",key="b_tema",on_click=callback_recalcular_folgas_bd)

        st.divider()
        st.subheader("🔧 Fouling (TEMA)")
        b_fp=st.selectbox("Preset:",list(FOULING_PRESETS.keys()),key="b_fp")
        fe1,fi1=FOULING_PRESETS[b_fp]
        if b_fp!="Personalizado":
            st.session_state["b_Rfe"]=str(fe1); st.session_state["b_Rfi"]=str(fi1)
        b_Rfe=parse(tinput("Rf ext (m²·K/W)","b_Rfe",str(fe1)),"Rf ext")
        b_Rfi=parse(tinput("Rf int (m²·K/W)","b_Rfi",str(fi1)),"Rf int")

        st.divider()
        calcular_b=st.button("▶ CALCULAR — BELL-DELAWARE",type="primary",use_container_width=True,key="btn_b")

    with R:
        st.subheader("📊 Resultados — Bell-Delaware")
        if calcular_b:
            try:
                Q_lat_s=b_ms*b_lam*b_frac if b_fase_on and "Casco" in b_fase_lado else 0
                Q_lat_t=b_mt*b_lam*b_frac if b_fase_on and "Tubo" in b_fase_lado else 0
                Tho,Tco,Q_W=resolver_T(b_obj,b_Thi,b_Tci,b_Tsaida,b_ms,b_cp_s,b_mt,b_cp_t,Q_lat_s,Q_lat_t)
                dTlm=lmtd(b_Thi,Tho,b_Tci,Tco)
                F=fator_F(b_Thi,Tho,b_Tci,Tco,b_Np)
                Tbs=(b_Thi+Tho)/2; Tbt=(b_Tci+Tco)/2
                Rp=b_d*math.log(b_d/b_di)/(2*b_kpar) if b_di>0 else 0

                geo0=bd_geo(b_d,b_Lta,b_Ltp,b_theta,b_Ds,b_Bc,b_Lbc,b_Lbi,b_Lbo,b_Nt,b_Nss,b_Lbb,b_Ltb)
                Gs0=b_ms/geo0["Sm"]; Res0=b_d*Gs0/b_mu_s
                fat0=bd_fat(geo0,Res0,geo0["Nb"],b_Lbi,b_Lbo,b_Lbc,b_Nss)
                def hcb(mw): return bd_casco(b_ms,b_mu_s,b_cp_s,b_k_s,mw,b_d,b_Ltp,b_theta,geo0,fat0)["hs"]
                def htb(mw): return kern_tubos(b_mt,b_rho_t,b_mu_t,b_cp_t,b_k_t,mw,b_d,b_di,b_Lta,b_Nt,b_Np)["ht"]
                
                fase_s_b = "gas" if b_fase_on and "Casco" in b_fase_lado else "liquido"
                mw=mu_iter(Tbs,Tbt,Rp,lambda T:mu_parede(b_mu_s,Tbs,T,fase=fase_s_b),lambda T:mu_parede(b_mu_t,Tbt,T),hcb,htb)

                geo=bd_geo(b_d,b_Lta,b_Ltp,b_theta,b_Ds,b_Bc,b_Lbc,b_Lbi,b_Lbo,b_Nt,b_Nss,b_Lbb,b_Ltb)
                Nb=geo["Nb"]; Gs_e=b_ms/geo["Sm"]; Res_e=b_d*Gs_e/b_mu_s
                fat=bd_fat(geo,Res_e,Nb,b_Lbi,b_Lbo,b_Lbc,b_Nss)
                cas=bd_casco(b_ms,b_mu_s,b_cp_s,b_k_s,mw["mwq"],b_d,b_Ltp,b_theta,geo,fat)
                prs=bd_dPs(b_ms,b_rho_s,b_mu_s,mw["mwq"],b_d,b_Ltp,b_theta,geo,fat)
                tub=kern_tubos(b_mt,b_rho_t,b_mu_t,b_cp_t,b_k_t,mw["mwf"],b_d,b_di,b_Lta,b_Nt,b_Np)
                gl=coef_global(cas["hs"],tub["ht"],b_d,b_di,b_kpar,Q_W,dTlm,b_Rfe,b_Rfi,F)
                Ai=b_Nt*math.pi*b_d*b_Lta; ex=(Ai/gl["A"]-1)*100 if gl["A"]>0 else 0
                PJ=fat["Jc"]*fat["Jl"]*fat["Jb"]*fat["Js"]*fat["Jr"]

                m1,m2,m3,m4=st.columns(4)
                m1.metric("U (W/m²·K)",f"{gl['U']:.1f}")
                m2.metric("Área calc. (m²)",f"{gl['A']:.3f}")
                m3.metric("Área inst. (m²)",f"{Ai:.3f}")
                m4.metric("Excesso (%)",f"{ex:.1f}")
                m1,m2,m3,m4=st.columns(4)
                m1.metric("Q (kW)",f"{Q_W/1000:.2f}")
                m2.metric("LMTD (°C)",f"{dTlm:.2f}")
                m3.metric("F",f"{F:.4f}")
                m4.metric("∏J",f"{PJ:.4f}")

                if F<0.75: st.warning("⚠️ F < 0,75")
                if PJ<0.6: st.warning(f"⚠️ ∏J={PJ:.3f} — eficiência muito baixa, revise geometria")

                st.subheader("Fatores J")
                jt={"Fator":["Jc","Jl","Jb","Js","Jr","∏J"],
                    "Valor":[f"{fat['Jc']:.4f}",f"{fat['Jl']:.4f}",f"{fat['Jb']:.4f}",
                             f"{fat['Js']:.4f}",f"{fat['Jr']:.4f}",f"{PJ:.4f}"],
                    "Status":["✅" if fat['Jc']>=0.9 else "⚠️",
                              "✅" if fat['Jl']>=0.75 else ("❌" if fat['Jl']<0.6 else "⚠️"),
                              "✅" if fat['Jb']>=0.85 else ("❌" if fat['Jb']<0.7 else "⚠️"),
                              "✅" if fat['Js']>=0.9 else "⚠️",
                              "✅" if fat['Jr']>=1.0 else "⚠️",
                              "✅" if PJ>=0.7 else ("❌" if PJ<0.6 else "⚠️")]}
                st.table(jt)

                st.subheader("Verificação ΔP")
                dPs=prs["dPs"]/1000; dPt=tub["dPt"]/1000
                c1,c2=st.columns(2)
                c1.metric("ΔPs (kPa)",f"{dPs:.3f}",f"Máx {b_dPs_max:.1f} — {'✓ OK' if dPs<=b_dPs_max else '⚠ EXCEDE'}")
                c2.metric("ΔPt (kPa)",f"{dPt:.3f}",f"Máx {b_dPt_max:.1f} — {'✓ OK' if dPt<=b_dPt_max else '⚠ EXCEDE'}")

                diag_text = diagnostico_bd(ex, gl["A"], Ai, b_Nt, b_Lta, b_d, geo, fat, cas["Res"], b_Bc, b_Lbc, b_Ltp, b_Np)

                txt=f"""
╔═══════════════════════════════════════════╗
║      RESULTADO — BELL-DELAWARE            ║
╚═══════════════════════════════════════════╝

─── TEMPERATURAS ───────────────────────────
  Quente : {b_Thi:.2f} → {Tho:.2f} °C
  Frio   : {b_Tci:.2f} → {Tco:.2f} °C

─── BALANÇO ────────────────────────────────
  Q total  = {Q_W/1000:.4f} kW
  LMTD     = {dTlm:.4f} °C  |  F = {F:.4f}

─── PAREDE (iterativo: {mw['it']} iter {'✓' if mw['conv'] else '⚠'}) ──────
  Tw casco = {mw['Twq']:.2f}°C  μw,s={mw['mwq']:.3e}  φs={mw['phq']:.4f}
  Tw tubo  = {mw['Twf']:.2f}°C  μw,t={mw['mwf']:.3e}  φt={mw['phf']:.4f}

─── FOLGAS ─────────────────────────────────
  Lbb={b_Lbb*1000:.2f}mm  Ltb={b_Ltb*1000:.1f}mm

─── GEOMETRIA BD ───────────────────────────
  Nb={Nb}  Sm={geo['Sm']*1e4:.4f}cm²  Sw={geo['Sw']*1e4:.4f}cm²
  Fc={geo['Fc']:.4f}  Ntcc={geo['Ntcc']:.2f}  Ntcw={geo['Ntcw']:.2f}  Fsbp={geo['Fsbp']:.4f}

─── FATORES J ──────────────────────────────
  Jc={fat['Jc']:.4f}  Jl={fat['Jl']:.4f}  Jb={fat['Jb']:.4f}
  Js={fat['Js']:.4f}  Jr={fat['Jr']:.4f}  ∏J={PJ:.4f}

─── CASCO ──────────────────────────────────
  Gs={cas['Gs']:.4f}kg/m²s  Re={cas['Res']:.0f}  Pr={cas['Prs']:.4f}
  hi={cas['hi']:.2f}W/m²K (ideal)  hs={cas['hs']:.2f}W/m²K (real)
  ΔPs={prs['dPs']:.2f}Pa ({prs['dPs']/1000:.4f}kPa)

─── TUBOS ──────────────────────────────────
  Re={tub['Ret']:.0f} [{tub['reg']}]
  Nu={tub['Nut']:.4f}  ht={tub['ht']:.2f}W/m²K  v={tub['vt']:.3f}m/s
  ΔPt total={tub['dPt']:.2f}Pa ({tub['dPt']/1000:.4f}kPa)

─── DIMENSIONAMENTO GLOBAL ─────────────────
  U={gl['U']:.2f} W/m²K  | Área calc = {gl['A']:.4f} m² | Instalada = {Ai:.4f} m²
{diag_text}
"""
                st.markdown(f'<div class="result-box">{txt}</div>',unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro no cálculo: {e}")

st.divider()
st.caption("Fórmulas baseadas em Kern(1950) · Kakaç&Liu(2002) · Thulukkanam(2013) · TEMA Standards")
