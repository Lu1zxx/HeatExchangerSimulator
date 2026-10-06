"""
Simulador Casco-e-Tubo — Streamlit
Kern & Bell-Delaware
"""
import math
import streamlit as st

# ═════════════════════════════════════════════════════════════════
try:
    import CoolProp.CoolProp as _CP
    COOLPROP_DISPONIVEL = True
    COOLPROP_VERSAO = _CP.get_global_param_string("version")
except ImportError:
    _CP = None; COOLPROP_DISPONIVEL = False; COOLPROP_VERSAO = None

# ═════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Simulador — Casco-e-Tubo",
                   page_icon="⚙️", layout="wide",
                   initial_sidebar_state="expanded")


st.markdown("""
<style>
.stApp{background:#0B1520!important}
[data-testid="stSidebar"]{background:#111E2D!important}
.stApp,.stApp p,.stApp span,.stApp label,.stApp div{color:#DFF0FF}
[data-testid="stExpander"]{background:#172435;border:1px solid #1F4068!important;border-radius:8px}
.stTextInput input,.stSelectbox>div>div{background:#1E3048!important;color:#DFF0FF!important;border:1px solid #1F4068!important}
.stTextInput label,.stSelectbox label,.stRadio label{color:#8FB0CF!important;font-size:13px!important}
.stButton>button{background:#1F4068!important;color:#DFF0FF!important;border:1px solid #00C2FF!important;border-radius:6px!important;font-weight:600!important}
.stButton>button:hover{background:#00C2FF!important;color:#0B1520!important}
.stButton>button[kind="primary"]{background:#00C2FF!important;color:#0B1520!important}
.stTabs [data-baseweb="tab"]{background:#172435;color:#6A90B0;border-radius:6px 6px 0 0;padding:8px 18px;font-weight:600}
.stTabs [aria-selected="true"]{background:#00C2FF!important;color:#0B1520!important}
h1,h2,h3{color:#DFF0FF!important}
.stage-nav{background:#111E2D;border:1px solid #1F4068;border-radius:8px;padding:12px 18px;margin-bottom:12px}
.stage-nav .title{color:#00C2FF;font-family:'Courier New',monospace;font-weight:700;font-size:14px;letter-spacing:.5px}
.stage-nav .progress{color:#8FB0CF;font-size:12px;margin-top:4px}
.val-box{background:#2B1D0E;border:2px solid #FFD166;border-radius:8px;padding:14px 18px;margin:12px 0}
.val-box .h{color:#FFD166;font-weight:700;font-size:15px;margin-bottom:8px}
.val-box ul{margin:6px 0 0 20px;padding:0}
.val-box li{color:#FFE9A8;margin:4px 0;font-size:13px}
.card-info{background:#0F2438;border-left:4px solid #00C2FF;border-radius:6px;padding:14px 18px;margin:10px 0;color:#C8E4FF;font-size:13px;line-height:1.7}
.card-warn{background:#2B1D0E;border-left:4px solid #FFD166;border-radius:6px;padding:14px 18px;margin:10px 0;color:#FFE9A8;font-size:13px;line-height:1.7}
.card-ok{background:#0D2A1A;border-left:4px solid #00E5A0;border-radius:6px;padding:14px 18px;margin:10px 0;color:#A8FFD7;font-size:13px;line-height:1.7}
.result-box{background:#0A1018;border:1px solid #1F4068;border-radius:8px;padding:18px;font-family:'Courier New',monospace;font-size:12.5px;white-space:pre-wrap;line-height:1.6;color:#00E5A0;max-height:700px;overflow-y:auto}
.formula{background:#0A1018;border:1px solid #C084FC;border-radius:8px;padding:16px 20px;margin:10px 0}
.formula h4{color:#C084FC;margin:0 0 10px 0;font-size:14px}
.formula .expl{color:#8FB0CF;font-size:12px;margin-top:8px;line-height:1.6}
</style>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
#  DADOS DE REFERÊNCIA
# ═════════════════════════════════════════════════════════════════
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
FLUIDOS_DB = {
    "Água (líquida)": {
        "rho": lambda T: 999.85 + 0.0523*T - 0.00744*T**2 + 1.7e-5*T**3,
        "mu":  lambda T: 2.414e-5 * 10**(247.8/((T+273.15)-140.0)),
        "cp":  lambda T: 4217.4 - 3.72*T + 0.1412*T**2 - 0.00191*T**3 + 9.6e-6*T**4,
        "k":   lambda T: 0.5636 + 0.001946*T - 8.151e-6*T**2,
        "faixa": (0, 200), "fonte": "Incropera (2007) Tab. A.6"},
    "Ar (1 atm)": {
        "rho": lambda T: 353.05 / (T + 273.15),
        "mu":  lambda T: 1.716e-5 * ((T+273.15)/273.15)**1.5 * (273.15+110.4)/((T+273.15)+110.4),
        "cp":  lambda T: 1006.0 + 0.0448*T + 1.6e-4*T**2,
        "k":   lambda T: 0.0241 + 7.5e-5*T - 1.0e-8*T**2,
        "faixa": (-20, 400), "fonte": "Incropera (2007) Tab. A.4"},
}
FLUIDOS_COOLPROP = {
    "Água (CoolProp)":"Water","Ar (CoolProp)":"Air","Nitrogênio":"Nitrogen",
    "Oxigênio":"Oxygen","Argônio":"Argon","Hélio":"Helium","Hidrogênio":"Hydrogen",
    "CO₂":"CarbonDioxide","Amônia (NH₃)":"Ammonia","Metano":"Methane","Etano":"Ethane",
    "Propano":"n-Propane","Isobutano":"IsoButane","n-Butano":"n-Butane",
    "n-Pentano":"n-Pentane","n-Hexano":"n-Hexane","n-Heptano":"n-Heptane",
    "n-Octano":"n-Octane","n-Decano":"n-Decane","Benzeno":"Benzene",
    "Tolueno":"Toluene","Etilbenzeno":"EthylBenzene","Metanol":"Methanol","Etanol":"Ethanol",
    "R134a":"R134a","R410A":"R410A","R404A":"R404A","R407C":"R407C","R507A":"R507A",
    "R32":"R32","R152a":"R152A","R1234yf":"R1234yf","R1234ze(E)":"R1234ze(E)",
    "R245fa":"R245fa","R125":"R125","R143a":"R143a","R227ea":"R227EA",
    "R22 (legado)":"R22","R11 (legado)":"R11","R12 (legado)":"R12","R123 (legado)":"R123",
}
TAB10 = {
    30:[(1e5,0.321,-0.388,1.450,0.519),(1e4,0.321,-0.388,None,None),
        (1e3,0.593,-0.477,None,None),(1e2,1.360,-0.657,None,None),(10,1.400,-0.667,None,None)],
    45:[(1e5,0.370,-0.396,1.930,0.500),(1e4,0.370,-0.396,None,None),
        (1e3,0.730,-0.500,None,None),(1e2,0.498,-0.656,None,None),(10,1.550,-0.667,None,None)],
    90:[(1e5,0.370,-0.395,1.187,0.370),(1e4,0.107,-0.266,None,None),
        (1e3,0.408,-0.460,None,None),(1e2,0.900,-0.631,None,None),(10,0.970,-0.667,None,None)]}
TAB11 = {
    30:[(1e5,0.372,-0.123,7.00,0.500),(1e4,0.486,-0.152,None,None),
        (1e3,4.570,-0.476,None,None),(1e2,45.100,-0.973,None,None),(10,48.000,-1.000,None,None)],
    45:[(1e5,0.303,-0.126,6.59,0.520),(1e4,0.333,-0.136,None,None),
        (1e3,3.500,-0.476,None,None),(1e2,26.200,-0.913,None,None),(10,32.000,-1.000,None,None)],
    90:[(1e5,0.391,-0.148,6.30,0.378),(1e4,0.0815,+0.022,None,None),
        (1e3,6.090,-0.602,None,None),(1e2,32.100,-0.963,None,None),(10,35.000,-1.000,None,None)]}
K1N = {
    (1,30):(0.319,2.142),(1,45):(0.319,2.142),(1,60):(0.319,2.142),(1,90):(0.215,2.207),
    (2,30):(0.249,2.207),(2,45):(0.249,2.207),(2,60):(0.249,2.207),(2,90):(0.156,2.291),
    (4,30):(0.175,2.285),(4,45):(0.175,2.285),(4,60):(0.175,2.285),(4,90):(0.158,2.263),
    (6,30):(0.0743,2.499),(6,45):(0.0743,2.499),(6,60):(0.0743,2.499),(6,90):(0.0402,2.617),
    (8,30):(0.0365,2.675),(8,45):(0.0365,2.675),(8,60):(0.0365,2.675),(8,90):(0.0331,2.643)}

# ═════════════════════════════════════════════════════════════════
#  PERSISTÊNCIA COM NONCE  ← CORREÇÃO RAIZ
#  ─────────────────────────────────────────────────────────────────
#  Quando alteramos um valor programaticamente (ex: buscar fluido),
#  o widget do Streamlit NÃO atualiza sozinho. A solução é dar um
#  "nonce" (número) à chave do widget: quando bumpamos o nonce, o
#  widget antigo é descartado e um novo é criado com o valor novo.
# ═════════════════════════════════════════════════════════════════
if "_vals" not in st.session_state:
    st.session_state["_vals"] = {}
if "_nonce" not in st.session_state:
    st.session_state["_nonce"] = {}

def _V(key, default=""):
    return st.session_state["_vals"].get(key, default)

def _S(key, val):
    """Grava valor E invalida o widget atual (bump nonce)."""
    st.session_state["_vals"][key] = val
    st.session_state["_nonce"][key] = st.session_state["_nonce"].get(key, 0) + 1

def _n(key):
    return st.session_state["_nonce"].get(key, 0)

def ptext(label, key, default="", help=None, disabled=False, placeholder=""):
    """Text input persistente. O widget_key inclui o nonce, então cada _S() cria um widget novo."""
    widget_key = f"_w_{key}_{_n(key)}"
    v = st.text_input(label, value=_V(key, default), key=widget_key,
                      help=help, disabled=disabled, placeholder=placeholder)
    st.session_state["_vals"][key] = v
    return v

def pselect(label, key, options, default=None, help=None):
    widget_key = f"_w_{key}_{_n(key)}"
    cur = _V(key, default if default is not None else options[0])
    if cur not in options: cur = options[0]
    idx = options.index(cur)
    v = st.selectbox(label, options, index=idx, key=widget_key, help=help)
    st.session_state["_vals"][key] = v
    return v

def pradio(label, key, options, default=None, horizontal=True, help=None):
    widget_key = f"_w_{key}_{_n(key)}"
    cur = _V(key, default if default is not None else options[0])
    if cur not in options: cur = options[0]
    idx = options.index(cur)
    v = st.radio(label, options, index=idx, key=widget_key,
                 horizontal=horizontal, help=help)
    st.session_state["_vals"][key] = v
    return v

def pf(key, default=0.0):
    try: return float(str(_V(key,"")).replace(",",".").strip())
    except: return default

def pi_(key, default=0):
    try: return int(float(str(_V(key,"")).replace(",",".").strip()))
    except: return default

# ═════════════════════════════════════════════════════════════════
#  HELPERS DE CÁLCULO
# ═════════════════════════════════════════════════════════════════
def _lookup(tab, theta, Re):
    ent = tab[theta]
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
    phq=(mbq/mwq)**0.14 if mwq>0 else 1.0
    phf=(mbf/mwf)**0.14 if mwf>0 else 1.0
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
        if Q<=0: raise ValueError("Q ≤ 0 → Th,o deve ser menor que Th,i")
        Tco=Tci+(Q-Q_lat_t)/(mt*cpt)
        if Tco >= Thi:
            raise ValueError(
                f"Tc,o calculado ({Tco:.1f} °C) ficou ≥ Th,i ({Thi:.1f} °C). "
                f"Isso viola a 2ª Lei. Verifique as vazões (ṁₛ, ṁₜ) e os "
                f"calores específicos (cp,s, cp,t) — provavelmente ṁₜ está "
                f"pequeno demais para a carga térmica.")
    else:
        Tco=Tval; Q=mt*cpt*(Tco-Tci)+Q_lat_t
        if Q<=0: raise ValueError("Q ≤ 0 → Tc,o deve ser maior que Tc,i")
        Tho=Thi-(Q-Q_lat_s)/(ms*cps)
        if Tho <= Tci:
            raise ValueError(
                f"Th,o calculado ({Tho:.1f} °C) ficou ≤ Tc,i ({Tci:.1f} °C). "
                f"Isso viola a 2ª Lei. Verifique as vazões (ṁₛ, ṁₜ) e os "
                f"calores específicos (cp,s, cp,t).")
    return Tho,Tco,Q

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
        Nut=max(3.66,1.86*arg**(1/3)*(mu_t/mwt)**0.14); reg="Laminar"
    elif Ret>10000:
        Nut=0.027*Ret**0.8*Prt**(1/3)*(mu_t/mwt)**0.14; reg="Turbulento"
    else:
        fp=(0.790*math.log(Ret)-1.64)**(-2)
        dn=1+12.7*math.sqrt(fp/8)*(Prt**(2/3)-1)
        Nut=max(3.66,(fp/8)*(Ret-1000)*Prt/dn*(mu_t/mwt)**0.14 if dn>0 else 10); reg="Transição"
    _A=(2.457*math.log(1/((7/Ret)**0.9+0.27*(0.000046/di))))**16
    _B=(37530/Ret)**16
    ft=8*((8/Ret)**12+1/(_A+_B)**1.5)**(1/12)
    phi=(mu_t/mwt)**0.14 if Ret>=2300 else (mu_t/mwt)**0.25
    dPf=ft*(Lta/di)*(Gt**2/(2*rho_t))*(1/phi)*Np
    dPr=4*max(Np-1,0)*(Gt**2/(2*rho_t))
    return{"Gt":Gt,"vt":Gt/rho_t,"Ret":Ret,"Prt":Prt,"Nut":Nut,"ht":Nut*k_t/di,
           "ft":ft,"dPt":dPf+dPr,"dPf":dPf,"dPr":dPr,"reg":reg}

def bd_geo(d,Lta,Ltp,theta,Ds,Bc,Lbc,Lbi,Lbo,Nt,Nss,Lbb_m=None,Ltb_m=8e-4):
    Lbb=Lbb_m if Lbb_m else (12+0.005*(Ds*1000))/1000
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

def propriedades_fluido(nome, T_C, P_Pa=101325.0):
    if nome in FLUIDOS_DB:
        f = FLUIDOS_DB[nome]; Tmin, Tmax = f["faixa"]
        fora = not (Tmin <= T_C <= Tmax)
        return {"rho":f["rho"](T_C),"mu":f["mu"](T_C),
                "cp":f["cp"](T_C),"k":f["k"](T_C),
                "fora_faixa":fora,"faixa":f["faixa"],"fonte":f["fonte"]}
    if nome in FLUIDOS_COOLPROP:
        if not COOLPROP_DISPONIVEL:
            raise RuntimeError("CoolProp não instalado. Instale com: pip install CoolProp")
        fid = FLUIDOS_COOLPROP[nome]; T_K = T_C + 273.15
        try:
            Tmin_K = _CP.PropsSI("Tmin", fid); Tmax_K = _CP.PropsSI("Tmax", fid)
            rho = _CP.PropsSI("D","T",T_K,"P",P_Pa,fid)
            mu  = _CP.PropsSI("V","T",T_K,"P",P_Pa,fid)
            cp  = _CP.PropsSI("C","T",T_K,"P",P_Pa,fid)
            k   = _CP.PropsSI("L","T",T_K,"P",P_Pa,fid)
        except Exception as e:
            raise RuntimeError(f"CoolProp falhou: {str(e)[:150]}")
        try: fase_b = _CP.PhaseSI("T",T_K,"P",P_Pa,fid)
        except: fase_b = "unknown"
        fase_pt = {"liquid":"líquido","gas":"gás","twophase":"bifásico",
                   "supercritical":"supercrítico","unknown":"indefinida"}.get(fase_b,fase_b)
        fora = not (Tmin_K <= T_K <= Tmax_K)
        return {"rho":rho,"mu":mu,"cp":cp,"k":k,"fora_faixa":fora,
                "faixa":(Tmin_K-273.15,Tmax_K-273.15),"fase":fase_pt,
                "fonte":f"CoolProp {COOLPROP_VERSAO or ''}"}
    raise KeyError(nome)

# ═════════════════════════════════════════════════════════════════
#  NESTA ETAPA — com LaTeX (corrige fórmulas estranhas)
# ═════════════════════════════════════════════════════════════════
def render_nesta_etapa(pag):
    """Conteúdo teórico da aba 'Nesta Etapa'."""
    if pag == 0:
        st.markdown("## 🌡️ Temperaturas e Objetivo")
        st.markdown("Nesta etapa você define as **temperaturas de entrada** dos dois "
                    "fluidos e escolhe **qual temperatura de saída** o programa deve calcular.")
        st.markdown("### 📐 Fórmulas")
        st.markdown("**Balanço de energia (1ª Lei da Termodinâmica):**")
        st.latex(r"Q = \dot{m} \cdot c_p \cdot |\Delta T|")
        st.markdown("**Igualdade dos calores trocados:**")
        st.latex(r"Q_{\text{quente}} = Q_{\text{frio}}")
        st.markdown("**Diferença de temperatura média logarítmica (LMTD):**")
        st.latex(r"\text{LMTD} = \frac{\Delta T_1 - \Delta T_2}{\ln(\Delta T_1 / \Delta T_2)}")
        st.markdown(r"onde $\Delta T_1 = T_{h,i} - T_{c,o}$ e $\Delta T_2 = T_{h,o} - T_{c,i}$")
        st.markdown("### 💥 Impacto no projeto")
        st.markdown("""
- Essas temperaturas definem o **Q TOTAL** do trocador.
- Quanto **menor** o ΔT, **menor** a força motriz (LMTD) → mais área.
- Se a T de saída violar a 2ª Lei, o programa avisa em vermelho.
""")
        st.markdown("### 📖 Glossário")
        st.markdown(r"""
- $T_{h,i}, T_{h,o}$ — entrada/saída do fluido **quente** (°C)
- $T_{c,i}, T_{c,o}$ — entrada/saída do fluido **frio** (°C)
- $Q$ — taxa de calor trocado (W)
- $\dot{m}$ — vazão mássica (kg/s)
- $c_p$ — calor específico (J/kg·K)
- $\Delta T$ — diferença de temperatura (°C)
- LMTD — diferença de temperatura média logarítmica
- 2ª Lei — o frio nunca sai mais quente que o quente entrou
""")

    elif pag == 1:
        st.markdown("## 🧪 Fluidos e Vazões")
        st.markdown("Nesta etapa você define as 4 propriedades físicas dos fluidos "
                    "(ρ, μ, cp, k) avaliadas na temperatura média, mais as vazões mássicas.")
        st.markdown("### 📐 Fórmulas")
        st.markdown("**Número de Reynolds:**")
        st.latex(r"Re = \frac{D \cdot G}{\mu} \qquad \text{com } G = \frac{\dot{m}}{A}")
        st.markdown("**Número de Prandtl:**")
        st.latex(r"Pr = \frac{\mu \cdot c_p}{k}")
        st.markdown("**Correção de viscosidade na parede:**")
        st.latex(r"\phi = \left(\frac{\mu_{\text{bulk}}}{\mu_w}\right)^{0{,}14}"
                 r" \qquad h_{\text{real}} = h_{\text{ideal}} \cdot \phi")
        st.markdown("### 🔵 Correlações de h")
        st.markdown("**Casco (Kern):**")
        st.latex(r"h_s = 0{,}36 \cdot \frac{k}{D_{hs}} \cdot Re^{0{,}55} \cdot Pr^{1/3}")
        st.markdown("**Tubos (Sieder-Tate / Gnielinski):**")
        st.latex(r"Nu = f(Re, Pr) \quad \Rightarrow \quad h = \frac{Nu \cdot k}{d_i}")
        st.markdown("### 🧱 Temperatura da parede (iterativo)")
        st.markdown(r"""
A viscosidade dos líquidos muda perto da parede, distorcendo o perfil de
velocidade e alterando h. Ignorar isso **superestima h** em até 20–30%.

**Algoritmo do programa:**
1. Chutar $T_w = (T_q + T_f)/2$
2. Calcular $\mu_w$ em $T_w$ (equação de Andrade para líquidos)
3. Recalcular $h$ com $\phi = (\mu_{\text{bulk}}/\mu_w)^{0{,}14}$
4. Recalcular $T_w$ pelo circuito de resistências
5. Repetir até $|\Delta T_w| < 0{,}1$ °C (2–4 iterações)
""")
        st.markdown("### 💥 Impacto no projeto")
        st.markdown(r"""
- Fluidos **mais viscosos** (μ alto) → Re menor → regime laminar → h menor → **mais área**.
- $c_p$ alto no fluido de menor vazão limita quanto ele pode aquecer/resfriar.
- A viscosidade $\mu$ informada é do fluido **bulk** — o programa calcula sozinho a viscosidade **junto à parede**.
""")
        st.markdown("### 📖 Glossário")
        st.markdown(r"""
- $\rho$ — massa específica (kg/m³)
- $\mu$ — viscosidade dinâmica bulk (Pa·s)
- $\mu_w$ — viscosidade junto à parede (Pa·s)
- $c_p$ — calor específico a pressão constante (J/kg·K)
- $k$ — condutividade térmica (W/m·K)
- $\dot{m}_s, \dot{m}_t$ — vazões mássicas casco/tubos (kg/s)
- $Re, Pr$ — Reynolds e Prandtl (adimensionais)
- $h_s, h_t$ — coef. de película casco/tubos (W/m²·K)
- $\phi$ — fator de correção de viscosidade na parede
""")

    elif pag == 2:
        st.markdown("## 📐 Geometria do Trocador")
        st.markdown("A geometria define a **área disponível de troca** e como os "
                    "fluidos escoam dentro do trocador.")
        st.markdown("### 📐 Fórmulas")
        st.markdown("**Diâmetro interno do tubo:**")
        st.latex(r"d_i = d_o - 2e")
        st.markdown("**Número de chicanas:**")
        st.latex(r"N_b = \lfloor L_{ta} / L_{bc} \rfloor - 1")
        st.markdown("**Área instalada:**")
        st.latex(r"A_{\text{inst}} = N_t \cdot \pi \cdot d_o \cdot L_{ta}")
        st.markdown("**Fator de correção da LMTD (multipasse):**")
        st.latex(r"F = f(P, R, N_p) \qquad N_p = 1 \Rightarrow F = 1{,}0")
        st.markdown("### 💥 Impacto no projeto")
        st.markdown(r"""
- Chicanas mais próximas ($L_{bc}$ menor) → mais turbulência → $h$ maior, **mas também** mais $\Delta P$. Trade-off.
- $D_s$ e $L_{tp}$ definem quantos tubos cabem e a velocidade no casco.
- $\theta = 30°$ empacota mais tubos que $\theta = 90°$.
- $N_p > 1$ aumenta velocidade nos tubos (mais $h$) mas reduz $F$.
""")
        st.markdown("### 📊 Tabela Nₜ × Dₛ (tubo 3/4\", θ=30°, 1 passe)")
        st.markdown("""
| Dₛ (m) | Dₛ (pol.) | Nₜ aprox. |
|:---:|:---:|:---:|
| 0,203 | 8\" | ~37 |
| 0,254 | 10\" | ~62 |
| 0,305 | 12\" | ~92 |
| 0,387 | 15¼\" | ~151 |
| 0,489 | 19¼\" | ~277 |
| 0,591 | 23¼\" | ~377 |
""")
        st.markdown("### 📖 Glossário")
        st.markdown(r"""
- $d_o, d_i$ — diâmetros externo e interno do tubo (m)
- $e$ — espessura da parede do tubo (m)
- $L_{ta}$ — comprimento do tubo (m)
- $L_{tp}$ — passo entre tubos, centro-a-centro (m)
- $D_s$ — diâmetro interno do casco (m)
- $L_{bc}$ — espaçamento entre chicanas (m)
- $N_b$ — número de chicanas (calculado)
- $N_t$ — número de tubos
- $\theta$ — ângulo do arranjo (°) : 30, 45, 60, 90
- $N_p$ — número de passes nos tubos
- $F$ — fator de correção da LMTD (multipasse)
""")

    else:
        st.markdown("## ⚙️ Limites, Fase, Fouling e Cálculo")
        st.markdown("Última etapa: limites operacionais, mudança de fase e fouling.")
        st.markdown("### 📐 Fórmulas")
        st.markdown("**Queda de pressão no casco (Kern):**")
        st.latex(r"\Delta P_s = \frac{f_s \cdot G_s^2 \cdot (N_b+1) \cdot D_s}"
                 r"{2 \cdot \rho_s \cdot D_{hs} \cdot \phi_s}")
        st.markdown("**Queda de pressão nos tubos:**")
        st.latex(r"\Delta P_t = f_t \cdot \frac{L_{ta}}{d_i} \cdot "
                 r"\frac{G_t^2}{2\rho_t} \cdot N_p + \Delta P_{\text{retorno}}")
        st.markdown("**Resistência de fouling:**")
        st.latex(r"R_{\text{foul}} = R_{f,\text{ext}} + "
                 r"\frac{d_o}{d_i} \cdot R_{f,\text{int}}")
        st.markdown("**Coeficiente global e área:**")
        st.latex(r"U = \frac{1}{R_{\text{ext}} + R_{\text{cond}} + R_{\text{int}} + R_{\text{foul}}}")
        st.latex(r"A = \frac{Q}{U \cdot \text{LMTD} \cdot F}")
        st.markdown("**Mudança de fase:**")
        st.latex(r"Q_{\text{total}} = Q_{\text{sensível}} + \dot{m} \cdot \lambda \cdot x")
        st.markdown("### 💥 Impacto no projeto")
        st.markdown(r"""
- Se $\Delta P$ calculado > limite definido, o projeto é **reprovado**.
- Fouling é a maior fonte de incerteza em projetos reais: quanto maior $R_f$, menor $U$ → maior a área.
- Trocadores são superdimensionados (excesso de área) para compensar o fouling.
""")
        st.markdown("### 📊 Faixas de excesso de área (TEMA)")
        st.markdown(r"""
- $< 0\%$ → ❌ Área insuficiente
- $0$–$10\%$ → ⚠️ Margem estreita
- $10$–$25\%$ → ✅ **Ideal**
- $25$–$35\%$ → ⚠️ Leve superdimensionamento
- $> 35\%$ → ❌ Superdimensionamento excessivo
""")
        st.markdown("### 📖 Glossário")
        st.markdown(r"""
- $\Delta P_s, \Delta P_t$ — queda de pressão casco/tubos (kPa)
- $f_s, f_t$ — fatores de atrito casco/tubos
- $R_f$ — resistência de fouling (m²·K/W)
- $R_{\text{foul}}$ — resistência total de fouling já combinada
- $U$ — coeficiente global de troca (W/m²·K)
- $A$ — área de troca térmica (m²)
- $\lambda$ — calor latente de mudança de fase (kJ/kg)
- $x$ — fração da vazão que muda de fase (0 a 1)
- TEMA — Tubular Exchanger Manufacturers Association
""")
def render_dicas(pag, metodo="kern"):
    """Aba 'Dicas' — guia prático por etapa."""
    if pag == 0:
        st.markdown("## 💡 Dicas — Temperaturas e Objetivo")
        st.markdown("### 🎯 Como escolher as temperaturas de entrada?")
        st.markdown("""
**Se você tem um processo real:**
- Use as temperaturas medidas ou de projeto da planta
- Geralmente vêm do balanço global de massa/energia

**Se você está estudando e não tem dados:**
""")
        st.markdown("""
| Aplicação típica | T quente (°C) | T frio (°C) |
|:---|:---:|:---:|
| Resfriamento de água | 80–100 → 40–60 | 20–30 → 35–45 |
| Trocador de óleo | 120–180 → 60–90 | 25–35 → 50–80 |
| Condensador de vapor | 100–150 (vapor) → 100 | 20–30 → 40–60 |
| Água de resfriamento | 30–40 → 25–30 | 15–25 → 25–30 |
| Recuperador de calor | 150–250 → 80–120 | 30–50 → 70–100 |
""")
        st.markdown("### ⚠️ Escolhendo o objetivo")
        st.markdown("""
Você informa **uma** temperatura de saída (a que você tem ou quer atingir).
O programa calcula a outra pelo balanço.

- **Definir Th,o** → você sabe quanto o fluido quente resfria
- **Definir Tc,o** → você sabe quanto o fluido frio aquece
""")
        st.markdown("### 🚨 Erros comuns")
        st.markdown(r"""
- $T_{c,o} < T_{h,i}$ (o frio nunca sai mais quente que o quente entrou)
- $T_{h,o} > T_{c,i}$ (o quente nunca sai mais frio que o frio entrou)
- ΔT muito pequeno (< 10 °C) → LMTD baixa → área enorme
""")

    elif pag == 1:
        st.markdown("## 💡 Dicas — Fluidos e Vazões")
        st.markdown("### 📚 Onde encontrar as propriedades?")
        st.markdown("""
**1. Use o banco integrado (mais rápido):**
- Escolha o fluido no combobox
- Insira a temperatura
- Clique em 🔎 Buscar propriedades

**2. CoolProp (se instalado):**
- 42 fluidos extras: refrigerantes, hidrocarbonetos, criogênicos
- Botão 💡 P sugere a pressão de saturação

**3. Tabelas impressas:**
- **Incropera** — Tabelas A.4 a A.8 (ar, água, óleos)
- **Perry's** — Seção 2 (Physical and Chemical Data)
- **NIST WebBook** — online, gratuito
""")
        st.markdown("### 🎯 Valores típicos para sanidade")
        st.markdown("""
| Fluido | ρ (kg/m³) | μ (mPa·s) | cp (kJ/kg·K) | k (W/m·K) |
|:---|:---:|:---:|:---:|:---:|
| Água (20 °C) | 998 | 1,00 | 4,18 | 0,60 |
| Ar (20 °C) | 1,20 | 0,018 | 1,005 | 0,026 |
| Etanol (20 °C) | 789 | 1,20 | 2,44 | 0,155 |
| Óleo SAE 30 (20 °C) | 890 | ~200 | 1,90 | 0,145 |
| Glicerina (20 °C) | 1260 | ~1500 | 2,43 | 0,285 |
| Amônia líquida (–20 °C) | 665 | 0,26 | 4,50 | 0,54 |
""")
        st.markdown("### ⚙️ Escolhendo vazões típicas")
        st.markdown("""
**Regras práticas para o casco:**
- Líquidos: velocidade 0,3–1,0 m/s
- Gases: 10–30 m/s
- Vapor: 15–60 m/s

**Para os tubos:**
- Líquidos: 1,0–3,0 m/s
- Gases: 10–30 m/s
- Água de resfriamento: 1,5–2,5 m/s

**Fórmula da vazão a partir da velocidade:**
""")
        st.latex(r"\dot{m} = \rho \cdot v \cdot A_{\text{escoamento}}")

    elif pag == 2:
        st.markdown("## 💡 Dicas — Geometria")
        st.markdown("### 📏 Tamanhos comerciais de tubo (TEMA)")
        st.markdown("""
| Polegada | d_o (m) | BWG | e (m) | di (m) |
|:---:|:---:|:---:|:---:|:---:|
| 1/2\" | 0,01270 | 16 | 0,00165 | 0,00940 |
| 5/8\" | 0,01588 | 16 | 0,00165 | 0,01258 |
| 3/4\" | 0,01905 | 14 | 0,00211 | 0,01483 |
| 3/4\" | 0,01905 | 16 | 0,00165 | 0,01575 |
| 1\" | 0,02540 | 14 | 0,00211 | 0,02118 |
| 1\" | 0,02540 | 16 | 0,00165 | 0,02210 |
| 1¼\" | 0,03175 | 16 | 0,00165 | 0,02845 |
| 1½\" | 0,03810 | 16 | 0,00165 | 0,03480 |
""")
        st.markdown("### 🎯 Como escolher cada parâmetro")
        st.markdown(r"""
**Comprimento $L_{ta}$ (comercial):**
1,83 / 2,44 / 3,66 / 4,88 / 6,10 m

**Passo $L_{tp}$:**
$L_{tp} \geq 1{,}25 \cdot d_o$ (mínimo TEMA)

**Espaçamento de chicanas $L_{bc}$:**
- Faixa válida: $0{,}2 \cdot D_s$ a $1{,}0 \cdot D_s$
- Recomendado: $0{,}3$ a $0{,}5 \cdot D_s$

**Diâmetro do casco $D_s$:**
- Até 300 mm: tubos 1/2\" ou 3/4\"
- 300–600 mm: tubos 3/4\" ou 1\"
- 600–1500 mm: tubos 1\" a 1¼\"
""")
        st.markdown("### 🚀 Caminho rápido")
        st.markdown("""
**Não sabe por onde começar?**

1. Preencha as páginas 1 e 2 (temperaturas e fluidos)
2. Volte aqui e clique em **🔮 Estimar geometria**
3. O programa deriva tudo: d_o, Nt, Ds, Lta, Ltp, Lbc
4. Ajuste se quiser (opcional)
""")

    else:
        st.markdown("## 💡 Dicas — Limites, Fase e Fouling")
        st.markdown("### ⚡ Quedas de pressão típicas")
        st.markdown("""
| Tipo de serviço | ΔPs máx (kPa) | ΔPt máx (kPa) | Referência |
|:---|:---:|:---:|:---|
| Líquido geral | 35 | 70 | Kern / TEMA |
| Bomba de baixa pressão | 20 | 35 | Thulukkanam |
| Líquido viscoso | 50 | 100 | Kakaç & Liu |
| Gás baixa pressão | 7 | 14 | Perry's |
| Vapor condensando | 14 | 35 | Thulukkanam |
| Gás alta pressão | 35 | 70 | Kakaç & Liu |
| Criogênico | 14 | 35 | Perry's |
""")
        st.markdown("### 🔧 Fouling (TEMA RGP-T-2.4)")
        st.markdown("""
| Serviço | Rf (m²·K/W) |
|:---|:---:|
| Água tratada | 0,000176 |
| Água não tratada | 0,000352 |
| Vapor d'água | 0,0000882 |
| Hidrocarbonetos leves | 0,000176 |
| Hidrocarbonetos pesados | 0,000528 |
| Gases industriais | 0,000176 |
""")
        st.markdown("### 💧 Calores latentes comuns")
        st.markdown("""
| Fluido | λ (kJ/kg) | T_ebulição @ 1 atm |
|:---|:---:|:---:|
| Água | 2257 | 100 °C |
| Amônia | 1371 | –33 °C |
| R134a | 217 | –26 °C |
| R410A | 275 | –52 °C |
| Etanol | 846 | 78 °C |
| Metanol | 1100 | 65 °C |
""")
        st.markdown("### ⚠️ Quando ativar mudança de fase?")
        st.markdown(r"""
- **Condensação** — se o fluido quente muda de vapor → líquido
- **Vaporização** — se o fluido frio muda de líquido → vapor
- Use $x = 1$ para condensação/vaporização total
- Use $x = 0{,}5$ se apenas metade da corrente muda de fase
""")

# ═════════════════════════════════════════════════════════════════
#  CABEÇALHO
# ═════════════════════════════════════════════════════════════════
st.title("⚙️ Simulador Casco-e-Tubo")
st.caption("**Kern** & **Bell-Delaware** · v5 · com Mudança de Fase, Fouling e CoolProp")

tab_k, tab_b = st.tabs(["🔵 KERN", "🟠 BELL-DELAWARE"])

# ═════════════════════════════════════════════════════════════════
#  VALIDAÇÃO
# ═════════════════════════════════════════════════════════════════
def validar_pagina(prefixo, pag):
    obrig = {
        0: [("Thi","Th,i — T entrada quente"),
            ("Tci","Tc,i — T entrada frio"),
            ("Tsaida","T de saída")],
        1: [("rho_s","ρₛ"), ("mu_s","μₛ"), ("cp_s","cp,s"), ("k_s","kₛ"), ("ms","ṁₛ"),
            ("rho_t","ρₜ"), ("mu_t","μₜ"), ("cp_t","cp,t"), ("k_t","kₜ"), ("mt","ṁₜ")],
        2: [("d","d_o"), ("e_parede","e"), ("Ds","Dₛ"), ("Lta","Lₜₐ"),
            ("Ltp","Lₜₚ"), ("Lbc","Lbc"), ("Nt","Nₜ")],
        3: [],
    }
    faltando = []
    for k, nome in obrig.get(pag, []):
        v = _V(f"{prefixo}_{k}", "")
        if not str(v).strip():
            faltando.append(nome)
    return (len(faltando)==0, faltando)

# ═════════════════════════════════════════════════════════════════
#  WIDGET DE FLUIDO
# ═════════════════════════════════════════════════════════════════
def widget_fluido(prefixo, lado):
    nome_lado = "Casco (quente)" if lado == "s" else "Tubos (frio)"
    nomes = list(FLUIDOS_DB.keys())
    if COOLPROP_DISPONIVEL:
        nomes += sorted(FLUIDOS_COOLPROP.keys())

    c1, c2 = st.columns([2, 1])
    with c1:
        fluido = pselect("Fluido:", f"{prefixo}_fluido_{lado}", nomes)
    with c2:
        st.markdown(f"<div style='color:#00E5A0;font-size:11px;padding-top:28px;'>"
                    f"🧬 CoolProp {COOLPROP_VERSAO}</div>" if COOLPROP_DISPONIVEL
                    else "<div style='color:#FFD166;font-size:11px;padding-top:28px;'>"
                         "⚠️ CoolProp ausente</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        ptext("T referência (°C):", f"{prefixo}_Tref_{lado}",
              help="Temperatura para avaliar as propriedades. Use a T de entrada como chute inicial.")
    with c2:
        ptext("P referência (kPa):", f"{prefixo}_Pref_{lado}", "101.325")
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_sug = st.button("💡 P", key=f"{prefixo}_sug_{lado}_{_n(f'{prefixo}_sug_{lado}')}",
                            help="Sugerir pressão de saturação (CoolProp)")

    fb_key = f"{prefixo}_fb_{lado}"
    if fb_key in st.session_state and st.session_state[fb_key]:
        st.markdown(st.session_state[fb_key], unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔎 Buscar propriedades", key=f"{prefixo}_buscar_{lado}_{_n(f'{prefixo}_buscar_{lado}')}",
                     use_container_width=True):
            try:
                T = pf(f"{prefixo}_Tref_{lado}")
                P_kPa = pf(f"{prefixo}_Pref_{lado}", 101.325)
                p = propriedades_fluido(fluido, T, P_Pa=P_kPa*1000.0)
                _S(f"{prefixo}_rho_{lado}", f"{p['rho']:.4f}")
                _S(f"{prefixo}_mu_{lado}",  f"{p['mu']:.6e}")
                _S(f"{prefixo}_cp_{lado}",  f"{p['cp']:.2f}")
                _S(f"{prefixo}_k_{lado}",   f"{p['k']:.5f}")
                aviso = "⚠️ fora da faixa!" if p["fora_faixa"] else "✔ dentro"
                fase = f" | fase: {p['fase']}" if p.get('fase') else ""
                st.session_state[fb_key] = (
                    f"<div class='card-ok'>✔ Preenchido: "
                    f"ρ={p['rho']:.3f} · μ={p['mu']:.3e} · cp={p['cp']:.1f} · k={p['k']:.4f}<br>"
                    f"<small>Faixa: {p['faixa'][0]:.1f} a {p['faixa'][1]:.1f} °C — {aviso}{fase} | {p['fonte']}</small>"
                    f"</div>")
                st.rerun()
            except Exception as e:
                st.session_state[fb_key] = f"<div class='card-warn'>⚠️ {e}</div>"
                st.rerun()
    with c2:
        if st.button("↺ Usar T média", key=f"{prefixo}_bulk_{lado}_{_n(f'{prefixo}_bulk_{lado}')}",
                     use_container_width=True):
            T_bulk = st.session_state.get(f"{prefixo}_Tbulk_{lado}")
            if T_bulk is None:
                st.session_state[fb_key] = "<div class='card-warn'>⚠️ Faça um cálculo primeiro.</div>"
                st.rerun()
            else:
                _S(f"{prefixo}_Tref_{lado}", f"{T_bulk:.2f}")
                st.rerun()

    if btn_sug:
        if fluido not in FLUIDOS_COOLPROP or not COOLPROP_DISPONIVEL:
            st.session_state[fb_key] = "<div class='card-warn'>💡 Só para fluidos CoolProp.</div>"
        else:
            try:
                T = pf(f"{prefixo}_Tref_{lado}")
                fid = FLUIDOS_COOLPROP[fluido]; T_K = T + 273.15
                T_sat_K = _CP.PropsSI("T","P",101325.0,"Q",0,fid)
                P_sat_Pa = _CP.PropsSI("P","T",T_K,"Q",0,fid)
                P_sat_kPa = P_sat_Pa/1000
                st.session_state[fb_key] = (
                    f"<div class='card-info'><b>💡 Sugestão de P</b><br>"
                    f"T_sat @ 1 atm = {T_sat_K-273.15:.1f} °C<br>"
                    f"P_sat em {T:.1f} °C = <b>{P_sat_kPa:.2f} kPa</b><br>"
                    f"▸ Líquido: P > {P_sat_kPa:.1f} kPa (sugestão {P_sat_kPa*1.2:.0f})<br>"
                    f"▸ Vapor:   P < {P_sat_kPa:.1f} kPa (sugestão {P_sat_kPa*0.5:.0f})"
                    f"</div>")
            except Exception:
                st.session_state[fb_key] = "<div class='card-warn'>⚠️ Sem saturação nesta T.</div>"
        st.rerun()

# ═════════════════════════════════════════════════════════════════
#  ESTIMAR GEOMETRIA (com validação + nonce)
# ═════════════════════════════════════════════════════════════════
def _estimar_geometria(prefixo, metodo):
    try:
        ok0, falt0 = validar_pagina(prefixo, 0)
        ok1, falt1 = validar_pagina(prefixo, 1)
        if not ok0:
            st.error("⚠️ **Página 1 (Temperaturas)** tem campos vazios: " + ", ".join(falt0))
            return
        if not ok1:
            st.error("⚠️ **Página 2 (Fluidos)** tem campos vazios: " + ", ".join(falt1) +
                     " — clique em 🔎 Buscar propriedades nos dois bancos.")
            return

        Thi = pf(f"{prefixo}_Thi"); Tci = pf(f"{prefixo}_Tci")
        Tsaida = pf(f"{prefixo}_Tsaida")
        ms = pf(f"{prefixo}_ms"); cp_s = pf(f"{prefixo}_cp_s")
        mt = pf(f"{prefixo}_mt"); cp_t = pf(f"{prefixo}_cp_t")
        obj_raw = _V(f"{prefixo}_obj", "Th,o")
        obj = "Th,o" if str(obj_raw).startswith("Th,o") else "Tc,o"

        # Validação física antes de calcular
        if ms <= 0 or mt <= 0:
            st.error("⚠️ As vazões mássicas ṁₛ e ṁₜ devem ser > 0.")
            return
        if cp_s <= 0 or cp_t <= 0:
            st.error("⚠️ Os calores específicos devem ser > 0.")
            return

        try:
            Tho, Tco, Q = resolver_T(obj, Thi, Tci, Tsaida, ms, cp_s, mt, cp_t)
            lmtd_v = lmtd(Thi, Tho, Tci, Tco)
        except ValueError as e:
            st.error(f"⚠️ {e}")
            return

        mu_max = max(pf(f"{prefixo}_mu_s", 1e-3), pf(f"{prefixo}_mu_t", 1e-3))
        U_tip, tipo = (400, "líquido–líquido viscoso") if mu_max > 1e-3 else (900, "líquido–líquido pouco viscoso")

        A_min = Q/(U_tip*lmtd_v)
        A_alvo = A_min * 1.15
        do, Lta = 0.01905, 4.88
        Ltp = 1.25 * do
        Nt = max(1, math.ceil(A_alvo/(math.pi*do*Lta)))
        Np_v = int(_V(f"{prefixo}_Np", 1))
        theta_v = int(_V(f"{prefixo}_theta", 30))
        r = bundle_diameter(Nt, do, Np_v, theta_v)
        Ds = r["Ds"]; Lbc = 0.30 * Ds

        _S(f"{prefixo}_d", f"{do:.5f}")
        _S(f"{prefixo}_e_parede", "0.00165")
        _S(f"{prefixo}_Lta", f"{Lta}")
        _S(f"{prefixo}_Ltp", f"{Ltp:.5f}")
        _S(f"{prefixo}_Ds", f"{Ds:.4f}")
        _S(f"{prefixo}_Lbc", f"{Lbc:.3f}")
        _S(f"{prefixo}_Nt", f"{Nt}")
        if metodo == "bd":
            _S(f"{prefixo}_Bc", "25")
            _S(f"{prefixo}_Lbi", f"{Lbc:.3f}")
            _S(f"{prefixo}_Lbo", f"{Lbc:.3f}")
            _S(f"{prefixo}_Nss", "2")

        st.success(
            f"✅ **Geometria estimada:**\n\n"
            f"Q = {Q/1000:.2f} kW · LMTD = {lmtd_v:.2f} °C · {tipo}\n\n"
            f"U = {U_tip} W/m²·K → A_alvo = {A_alvo:.2f} m²\n\n"
            f"• d_o = {do:.5f} m\n• Lta = {Lta} m\n• Nt = {Nt}\n"
            f"• Ltp = {Ltp:.5f} m\n• Ds = {Ds:.4f} m\n• Lbc = {Lbc:.3f} m")
        st.rerun()
    except Exception as e:
        st.error(f"Erro: {e}")

# ═════════════════════════════════════════════════════════════════
#  RENDER DE UMA ABA
# ═════════════════════════════════════════════════════════════════
def render_aba(prefixo, metodo):
    pag_key = f"{prefixo}_pagina"
    if pag_key not in st.session_state:
        st.session_state[pag_key] = 0
    pag = st.session_state[pag_key]
    titulos = ["🌡️ Temperaturas e Objetivo", "🧪 Fluidos e Vazões",
               "📐 Geometria do Trocador", "⚙️ Limites, Fase e Cálculo"]

    col_l, col_r = st.columns([1, 1], gap="large")

    # ══════════ COLUNA ESQUERDA ══════════
    with col_l:
        st.markdown(
            f"<div class='stage-nav'>"
            f"<div class='title'>🎓 MODO PASSO A PASSO</div>"
            f"<div class='progress'>Página <b>{pag+1}</b> de 4 — {titulos[pag]}</div>"
            f"</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("◀ Anterior", disabled=(pag==0), key=f"{prefixo}_ant",
                         use_container_width=True):
                st.session_state[pag_key] = pag - 1
                st.rerun()
        with c2:
            st.markdown(f"<div style='text-align:center;color:#6A90B0;padding-top:8px;font-size:14px;'>{pag+1}/4</div>",
                        unsafe_allow_html=True)
        with c3:
            if st.button("Próximo ▶", disabled=(pag==3), key=f"{prefixo}_prox",
                         use_container_width=True):
                ok, faltando = validar_pagina(prefixo, pag)
                if ok:
                    st.session_state[pag_key] = pag + 1
                    st.rerun()
                else:
                    items = "".join(f"<li>{c}</li>" for c in faltando)
                    st.markdown(
                        f"<div class='val-box'>"
                        f"<div class='h'>⚠️ Preencha os campos desta etapa</div>"
                        f"<ul>{items}</ul></div>",
                        unsafe_allow_html=True)

        st.markdown("---")

        # ─── PÁGINA 1 ───
        if pag == 0:
            st.markdown("<div class='card-info'><b>💡 Etapa 1:</b> temperaturas de entrada e saída alvo.</div>",
                        unsafe_allow_html=True)
            st.subheader("🌡️ Temperaturas do Processo")
            c1, c2 = st.columns(2)
            with c1: ptext("Th,i — quente entrada (°C) ✱", f"{prefixo}_Thi")
            with c2: ptext("Tc,i — frio entrada (°C) ✱", f"{prefixo}_Tci")

            st.markdown("**Objetivo:** qual temperatura de saída calcular?")
            obj = pradio("Objetivo", f"{prefixo}_obj",
                         ["Th,o → calcula Tc,o", "Tc,o → calcula Th,o"], horizontal=True)
            if obj.startswith("Th,o"):
                ptext("Th,o — quente saída (°C) ✱", f"{prefixo}_Tsaida")
            else:
                ptext("Tc,o — frio saída (°C) ✱", f"{prefixo}_Tsaida")

        # ─── PÁGINA 2 ───
        elif pag == 1:
            st.markdown("<div class='card-info'><b>💡 Etapa 2:</b> propriedades dos fluidos. "
                        "Use o banco para preencher automaticamente.</div>",
                        unsafe_allow_html=True)
                        # ⚠️ AVISO SOBRE T DE REFERÊNCIA
            with st.expander("⚠️ A T de referência é apenas um CHUTE inicial — leia antes de buscar",
                             expanded=True):
                st.markdown(r"""
            As propriedades (ρ, μ, cp, k) **variam com a temperatura**. Como você ainda
            não sabe a temperatura média exata do fluido (ela só aparece **depois** que
            o programa calcula as temperaturas de saída), use uma **estimativa inicial**:
            em geral, a própria **temperatura de entrada** do fluido.
            
            **Fluxo iterativo (converge em 1–2 rodadas):**
            
            1. Insira uma T-chute (ex.: a T de entrada do fluido)
            2. Clique em **🔎 Buscar propriedades**
            3. Vá para a **página 4** e clique em **▶ CALCULAR**
            4. Volte para **esta página** e clique em **↺ Usar T média**
               — o programa preenche com a $T_{\text{média}}$ que ele mesmo calculou
            5. Recalcule
            """)

            # Casco
            with st.expander("🔵 Banco de Fluidos — Casco (quente)", expanded=True):
                widget_fluido(prefixo, "s")
            st.markdown("**Propriedades do Casco (editáveis):**")
            c1, c2, c3 = st.columns(3)
            with c1:
                ptext("ρₛ (kg/m³)", f"{prefixo}_rho_s")
                ptext("cp,s (J/kg·K)", f"{prefixo}_cp_s")
            with c2:
                ptext("μₛ (Pa·s)", f"{prefixo}_mu_s")
                ptext("kₛ (W/m·K)", f"{prefixo}_k_s")
            with c3:
                ptext("ṁₛ (kg/s)", f"{prefixo}_ms")

            st.markdown("---")

            # Tubos
            with st.expander("🟠 Banco de Fluidos — Tubos (frio)", expanded=True):
                widget_fluido(prefixo, "t")
            st.markdown("**Propriedades dos Tubos (editáveis):**")
            c1, c2, c3 = st.columns(3)
            with c1:
                ptext("ρₜ (kg/m³)", f"{prefixo}_rho_t")
                ptext("cp,t (J/kg·K)", f"{prefixo}_cp_t")
            with c2:
                ptext("μₜ (Pa·s)", f"{prefixo}_mu_t")
                ptext("kₜ (W/m·K)", f"{prefixo}_k_t")
            with c3:
                ptext("ṁₜ (kg/s)", f"{prefixo}_mt")

        # ─── PÁGINA 3 ───
        elif pag == 2:
            st.markdown("<div class='card-info'><b>💡 Etapa 3:</b> geometria. Use 🔮 para estimar "
                        "a partir dos dados térmicos, ou o auxiliar abaixo.</div>",
                        unsafe_allow_html=True)

            if st.button("🔮 Estimar geometria a partir dos dados térmicos",
                         key=f"{prefixo}_estimar_{_n(f'{prefixo}_estimar')}",
                         use_container_width=True):
                _estimar_geometria(prefixo, metodo)

            st.markdown("---")
            st.markdown("#### 📐 Tubo")
            with st.expander("💡 Ajuda — Geometria do Tubo", expanded=False):
                st.markdown(
                    "**Diâmetros comerciais (TEMA):**\n"
                    "- d_o = 3/4\" → 0,01905 m\n"
                    "- d_o = 1\"   → 0,02540 m\n"
                    "- d_o = 1¼\"  → 0,03175 m\n"
                    "- d_o = 1½\"  → 0,03810 m\n\n"
                    "**Espessura (BWG 16-14):** 0,00165–0,00211 m\n\n"
                    "**Fórmula:** $d_i = d_o - 2e$")

            c1, c2 = st.columns(2)
            with c1:
                ptext("d_o — diâm. externo (m)", f"{prefixo}_d")
                ptext("e — espessura (m)", f"{prefixo}_e_parede")
            with c2:
                d_v = pf(f"{prefixo}_d"); e_v = pf(f"{prefixo}_e_parede")
                di_txt = f"{d_v - 2*e_v:.5f}" if (d_v - 2*e_v) > 0 else "—"
                st.text_input("di — diâm. interno (m) [calculado]", value=di_txt, disabled=True)
                pselect("Material:", f"{prefixo}_material", list(MATERIAIS.keys()))

            st.markdown("#### 🏗️ Casco e Chicanas")
            c1, c2 = st.columns(2)
            with c1:
                ptext("Dₛ — diâm. casco (m)", f"{prefixo}_Ds")
                ptext("Lₜₐ — comp. tubo (m)", f"{prefixo}_Lta")
                ptext("Lₜₚ — passo tubos (m)", f"{prefixo}_Ltp")
            with c2:
                ptext("Lbc — espaç. chicanas (m)", f"{prefixo}_Lbc")
                ptext("Nₜ — nº de tubos", f"{prefixo}_Nt")
                if metodo == "bd":
                    ptext("Bc — corte chicana (%)", f"{prefixo}_Bc", "25")
                    ptext("Lbi — chicana-entrada (m)", f"{prefixo}_Lbi")
                    ptext("Lbo — chicana-saída (m)", f"{prefixo}_Lbo")
                    ptext("Nss — pares de tiras", f"{prefixo}_Nss", "2")

            Lta_v = pf(f"{prefixo}_Lta"); Lbc_v = pf(f"{prefixo}_Lbc")
            if Lbc_v > 0:
                Nb_calc = max(1, int(Lta_v/Lbc_v) - 1)
                st.markdown(f"<div class='card-ok'>Nb calculado = <b>{Nb_calc}</b> chicanas</div>",
                            unsafe_allow_html=True)

            st.markdown("#### ⚙️ Arranjo e Passes")
            c1, c2 = st.columns(2)
            with c1:
                theta_opts = [30,45,60,90] if metodo=="kern" else [30,45,90]
                pselect("Ângulo θ:", f"{prefixo}_theta", theta_opts)
                with st.expander("💡 O que é θ?", expanded=False):
                    st.markdown(
                        "| θ | Compacidade | Limpeza mecânica | ΔP casco |\n"
                        "|:---:|:---:|:---:|:---:|\n"
                        "| **30°** | ✅ Alta | ❌ Só química | Alto |\n"
                        "| **45°** | Média | Limitada | Médio |\n"
                        "| **60°** | Alta | ❌ Só química | Alto |\n"
                        "| **90°** | Baixa | ✅ Fácil | Baixo |\n\n"
                        "**Recomendação:** limpos → 30° · com fouling → 90°")
            with c2:
                pselect("Passes Nₚ:", f"{prefixo}_Np", [1,2,4,6,8])
                with st.expander("💡 O que é Nₚ?", expanded=False):
                    st.markdown(
                        "| Nₚ | v_tubo | h_tubo | ΔP_tubo | Fator F |\n"
                        "|:---:|:---:|:---:|:---:|:---:|\n"
                        "| 1 | Menor | Menor | Mínimo | 1,00 |\n"
                        "| 2 | Dupla | Maior | 2× | ~0,90 |\n"
                        "| 4 | Alta | Muito maior | 4× | ~0,85 |\n"
                        "| 6 | Muito alta | — | 6× | Pode ser < 0,75 |\n\n"
                        "**Recomendação:** Nₚ=2 na maioria dos casos.")

            with st.expander("📐 Calculadora Db → Ds (Coulson & Richardson)"):
                if st.button("Calcular Db e Ds", key=f"{prefixo}_btn_db_{_n(f'{prefixo}_btn_db')}"):
                    try:
                        Nt_v = pi_(f"{prefixo}_Nt")
                        do_v = pf(f"{prefixo}_d")
                        Np_v = int(_V(f"{prefixo}_Np", 1))
                        th_v = int(_V(f"{prefixo}_theta", 30))
                        if Nt_v == 0 or do_v == 0:
                            st.error("Preencha Nₜ e d_o primeiro.")
                        else:
                            r = bundle_diameter(Nt_v, do_v, Np_v, th_v)
                            _S(f"{prefixo}_Ds_est", f"{r['Ds']:.4f}")
                            _S(f"{prefixo}_Ltp_sug", f"{r['Ltp_sug']:.5f}")
                            st.success(f"**Db = {r['Db']*1000:.1f} mm**  |  **Ds = {r['Ds']*1000:.1f} mm**")
                            st.caption(f"K₁ = {r['K1']}  n = {r['n1']}")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if _V(f"{prefixo}_Ds_est"):
                    if st.button("↑ Usar Ds sugerido", key=f"{prefixo}_usar_db_{_n(f'{prefixo}_usar_db')}"):
                        _S(f"{prefixo}_Ds", _V(f"{prefixo}_Ds_est"))
                        _S(f"{prefixo}_Ltp", _V(f"{prefixo}_Ltp_sug"))
                        st.rerun()

        # ─── PÁGINA 4 ───
        elif pag == 3:
            st.markdown("<div class='card-info'><b>💡 Etapa 4:</b> limites de ΔP, fase, fouling. "
                        "Depois clique em ▶ CALCULAR.</div>",
                        unsafe_allow_html=True)

            st.markdown("#### ⚡ Limites de ΔP")
            preset = pselect("Preset de serviço:", f"{prefixo}_preset_dp",
                             list(LIMITES_DP.keys()))
            ds0, dt0, ref0 = LIMITES_DP.get(preset, (0,0,""))
            if ds0 > 0 and _V(f"{prefixo}_preset_anterior", "") != preset:
                # Aplica uma vez ao trocar de preset
                _S(f"{prefixo}_dPs_max", str(ds0))
                _S(f"{prefixo}_dPt_max", str(dt0))
                _S(f"{prefixo}_preset_anterior", preset)
            if ds0 > 0:
                st.markdown(f"<div class='card-info'>📖 <b>{ref0}</b><br>"
                            f"ΔPs = {ds0} kPa  |  ΔPt = {dt0} kPa</div>",
                            unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: ptext("ΔP máx. casco (kPa)", f"{prefixo}_dPs_max")
            with c2: ptext("ΔP máx. tubos (kPa)", f"{prefixo}_dPt_max")

            st.markdown("---")
            st.markdown("#### ⇌ Mudança de Fase")
            ativa = st.checkbox("Há mudança de fase?",
                                key=f"{prefixo}_fase_on_{_n(f'{prefixo}_fase_on')}",
                                value=st.session_state.get(f"{prefixo}_fase_on_val", False))
            st.session_state[f"{prefixo}_fase_on_val"] = ativa
            if ativa:
                pradio("Tipo:", f"{prefixo}_fase_tipo", ["Condensação","Vaporização"], horizontal=True)
                pradio("Lado:", f"{prefixo}_fase_lado", ["Casco (quente)","Tubos (frio)"], horizontal=True)
                c1, c2 = st.columns(2)
                with c1: ptext("λ — calor latente (kJ/kg)", f"{prefixo}_lambda", "2257")
                with c2: ptext("x — fração [0-1]", f"{prefixo}_frac", "1.0")

            st.markdown("---")
            st.markdown("#### 🔧 Fouling (incrustação)")
            fp = pselect("Preset TEMA:", f"{prefixo}_fp", list(FOULING_PRESETS.keys()))
            fe0, fi0 = FOULING_PRESETS.get(fp, (0.0002, 0.0002))
            if fp != "Personalizado" and _V(f"{prefixo}_fp_anterior", "") != fp:
                _S(f"{prefixo}_Rfe", str(fe0))
                _S(f"{prefixo}_Rfi", str(fi0))
                _S(f"{prefixo}_fp_anterior", fp)
            c1, c2 = st.columns(2)
            with c1: ptext("Rf externo (m²·K/W)", f"{prefixo}_Rfe")
            with c2: ptext("Rf interno (m²·K/W)", f"{prefixo}_Rfi")

            st.markdown("---")
            if st.button(f"▶ CALCULAR — {metodo.upper()}",
                         key=f"{prefixo}_calc_{_n(f'{prefixo}_calc')}",
                         use_container_width=True, type="primary"):
                _executar_calculo(prefixo, metodo)

    # ══════════ COLUNA DIREITA ══════════
    with col_r:
        st.markdown(f"### 📊 Resultados — {metodo.upper()}")
        t_etapa, t_dicas, t_resumo, t_memo = st.tabs(
            ["🧭 Nesta Etapa", "💡 Dicas", "📊 Resumo", "📘 Memorial"])

        with t_etapa:
            render_nesta_etapa(pag)

        with t_dicas:
            render_dicas(pag, metodo)

        with t_resumo:
            resultado = st.session_state.get(f"{prefixo}_resultado")
            if resultado:
                st.markdown(f"<div class='result-box'>{resultado}</div>",
                            unsafe_allow_html=True)
            else:
                st.info("Preencha os campos e clique em ▶ CALCULAR.")

        with t_memo:
            memo = st.session_state.get(f"{prefixo}_memorial")
            if memo:
                st.markdown(f"<div class='result-box'>{memo}</div>",
                            unsafe_allow_html=True)
            else:
                st.info("O memorial aparece após CALCULAR.")
        

# ═════════════════════════════════════════════════════════════════
#  EXECUTAR CÁLCULO (com validação completa)
# ═════════════════════════════════════════════════════════════════
def _executar_calculo(prefixo, metodo):
    # Valida TODAS as páginas
    for p in [0, 1, 2]:
        ok, faltando = validar_pagina(prefixo, p)
        if not ok:
            items = "".join(f"<li>{c}</li>" for c in faltando)
            st.error(f"⚠️ **Página {p+1}** tem campos vazios:")
            st.markdown(f"<div class='val-box'><ul>{items}</ul></div>",
                        unsafe_allow_html=True)
            return

    try:
        Thi = pf(f"{prefixo}_Thi"); Tci = pf(f"{prefixo}_Tci")
        Tsaida = pf(f"{prefixo}_Tsaida")
        obj_raw = _V(f"{prefixo}_obj", "Th,o")
        obj = "Th,o" if str(obj_raw).startswith("Th,o") else "Tc,o"
        rho_s = pf(f"{prefixo}_rho_s"); mu_s = pf(f"{prefixo}_mu_s")
        cp_s = pf(f"{prefixo}_cp_s"); k_s = pf(f"{prefixo}_k_s"); ms = pf(f"{prefixo}_ms")
        rho_t = pf(f"{prefixo}_rho_t"); mu_t = pf(f"{prefixo}_mu_t")
        cp_t = pf(f"{prefixo}_cp_t"); k_t = pf(f"{prefixo}_k_t"); mt = pf(f"{prefixo}_mt")
        d = pf(f"{prefixo}_d"); e_p = pf(f"{prefixo}_e_parede"); di = d - 2*e_p
        Lta = pf(f"{prefixo}_Lta"); Ltp = pf(f"{prefixo}_Ltp")
        Ds = pf(f"{prefixo}_Ds"); Lbc = pf(f"{prefixo}_Lbc"); Nt = pi_(f"{prefixo}_Nt")
        theta = int(_V(f"{prefixo}_theta", 30)); Np = int(_V(f"{prefixo}_Np", 1))
        kpar = MATERIAIS.get(_V(f"{prefixo}_material", "Aço Carbono"), 50.0)

        if di <= 0:
            st.error("⚠️ di ≤ 0 — verifique d_o e espessura e")
            return

        lam = frac = 0.0; lado_fase = ""
        if st.session_state.get(f"{prefixo}_fase_on_val"):
            lam = pf(f"{prefixo}_lambda") * 1000.0
            frac = pf(f"{prefixo}_frac", 1.0)
            lado_fase = _V(f"{prefixo}_fase_lado", "")
        Q_lat_s = ms * lam * frac if "Casco" in lado_fase else 0
        Q_lat_t = mt * lam * frac if "Tubo" in lado_fase else 0

        Tho, Tco, Q_W = resolver_T(obj, Thi, Tci, Tsaida, ms, cp_s, mt, cp_t, Q_lat_s, Q_lat_t)
        dTlm = lmtd(Thi, Tho, Tci, Tco)
        F = fator_F(Thi, Tho, Tci, Tco, Np)
        Tbs = (Thi + Tho)/2; Tbt = (Tci + Tco)/2
        Rp = d*math.log(d/di)/(2*kpar)

        Rfe = pf(f"{prefixo}_Rfe", 0.0002)
        Rfi = pf(f"{prefixo}_Rfi", 0.0002)

        if metodo == "kern":
            geo0 = kern_geo(d, di, Lta, Ltp, theta, Ds, Lbc, Np)
            def hck(mw): return kern_casco(ms, mu_s, cp_s, k_s, geo0)["hs"]
            def htk(mw): return kern_tubos(mt, rho_t, mu_t, cp_t, k_t, mw, d, di, Lta, Nt, Np)["ht"]
            mw = mu_iter(Tbs, Tbt, Rp, lambda T: mu_parede(mu_s, Tbs, T),
                         lambda T: mu_parede(mu_t, Tbt, T), hck, htk)
            casco = kern_casco(ms, mu_s, cp_s, k_s, geo0)
            Nb = max(1, int(Lta/Lbc)-1) if Lbc > 0 else 1
            press = kern_dPs(casco["Gs"], casco["Res"], rho_s, Ds, geo0["Dhs"], mu_s, mw["mwq"], Nb)
            tubos = kern_tubos(mt, rho_t, mu_t, cp_t, k_t, mw["mwf"], d, di, Lta, Nt, Np)
            glob = coef_global(casco["hs"], tubos["ht"], d, di, kpar, Q_W, dTlm, Rfe, Rfi, F)
            Ai = Nt * math.pi * d * Lta
            ex = (Ai/glob["A"]-1)*100 if glob["A"] > 0 else 0
            dPs_kPa = press["dPs"]/1000; dPt_kPa = tubos["dPt"]/1000
            label = "KERN"
            fat = None
        else:
            Bc = pf(f"{prefixo}_Bc", 25); Lbi = pf(f"{prefixo}_Lbi", Lbc)
            Lbo = pf(f"{prefixo}_Lbo", Lbc); Nss = pf(f"{prefixo}_Nss", 2)
            Lbb_m = pf(f"{prefixo}_Lbb")/1000 if _V(f"{prefixo}_Lbb") else None
            Ltb_m = pf(f"{prefixo}_Ltb", 0.8)/1000
            geo0 = bd_geo(d, Lta, Ltp, theta, Ds, Bc, Lbc, Lbi, Lbo, Nt, Nss, Lbb_m, Ltb_m)
            Gs0 = ms/geo0["Sm"]; Res0 = d*Gs0/mu_s
            fat0 = bd_fat(geo0, Res0, geo0["Nb"], Lbi, Lbo, Lbc, Nss)
            def hcb(mw): return bd_casco(ms, mu_s, cp_s, k_s, mw, d, Ltp, theta, geo0, fat0)["hi"]
            def htb(mw): return kern_tubos(mt, rho_t, mu_t, cp_t, k_t, mw, d, di, Lta, Nt, Np)["ht"]
            mw = mu_iter(Tbs, Tbt, Rp, lambda T: mu_parede(mu_s, Tbs, T),
                         lambda T: mu_parede(mu_t, Tbt, T), hcb, htb)
            geo = bd_geo(d, Lta, Ltp, theta, Ds, Bc, Lbc, Lbi, Lbo, Nt, Nss, Lbb_m, Ltb_m)
            Nb = geo["Nb"]; Res_e = d*(ms/geo["Sm"])/mu_s
            fat = bd_fat(geo, Res_e, Nb, Lbi, Lbo, Lbc, Nss)
            casco = bd_casco(ms, mu_s, cp_s, k_s, mw["mwq"], d, Ltp, theta, geo, fat)
            press = bd_dPs(ms, rho_s, mu_s, mw["mwq"], d, Ltp, theta, geo, fat)
            tubos = kern_tubos(mt, rho_t, mu_t, cp_t, k_t, mw["mwf"], d, di, Lta, Nt, Np)
            glob = coef_global(casco["hs"], tubos["ht"], d, di, kpar, Q_W, dTlm, Rfe, Rfi, F)
            Ai = Nt * math.pi * d * Lta
            ex = (Ai/glob["A"]-1)*100 if glob["A"] > 0 else 0
            dPs_kPa = press["dPs"]/1000; dPt_kPa = tubos["dPt"]/1000
            PJ = fat["Jc"]*fat["Jl"]*fat["Jb"]*fat["Js"]*fat["Jr"]
            label = "BELL-DELAWARE"

        # Grava T bulk
        st.session_state[f"{prefixo}_Tbulk_s"] = Tbs
        st.session_state[f"{prefixo}_Tbulk_t"] = Tbt

        dPs_max = pf(f"{prefixo}_dPs_max", 70); dPt_max = pf(f"{prefixo}_dPt_max", 100)
        ok_ps = "✓ OK" if dPs_kPa <= dPs_max else "⚠️ EXCEDE"
        ok_pt = "✓ OK" if dPt_kPa <= dPt_max else "⚠️ EXCEDE"

        if ex < 0: diag = "❌ ÁREA INSUFICIENTE"
        elif ex < 10: diag = "⚠️ MARGEM ESTREITA (< 10%)"
        elif ex <= 25: diag = "✅ PROJETO ADEQUADO (10–25%)"
        elif ex <= 35: diag = "⚠️ LEVE SUPERDIMENSIONAMENTO (25–35%)"
        else: diag = "❌ SUPERDIMENSIONAMENTO EXCESSIVO (> 35%)"

        txt = f"""
╔══════════════════════════════════════════════╗
║   RESULTADO — {label:<26} ║
╚══════════════════════════════════════════════╝

─── TEMPERATURAS ─────────────────────────────
  Quente : {Thi:.2f} → {Tho:.2f} °C
  Frio   : {Tci:.2f} → {Tco:.2f} °C

─── BALANÇO ENERGÉTICO ───────────────────────
  Q     = {Q_W/1000:.4f} kW
  LMTD  = {dTlm:.4f} °C
  F     = {F:.4f}   (Np = {Np})

─── VISCOSIDADE NA PAREDE (iter {mw['it']}) ───
  {'✓ convergiu' if mw['conv'] else '⚠️ não convergiu'}
  Tw casco = {mw['Twq']:.2f} °C   μw,s = {mw['mwq']:.3e}   φs = {mw['phq']:.4f}
  Tw tubo  = {mw['Twf']:.2f} °C   μw,t = {mw['mwf']:.3e}   φt = {mw['phf']:.4f}

─── CASCO ────────────────────────────────────
  Gs  = {casco['Gs']:.4f} kg/m²·s
  Res = {casco['Res']:.0f}   Prs = {casco['Prs']:.4f}
  hs  = {casco['hs']:.2f} W/m²·K
  ΔPs = {dPs_kPa:.4f} kPa   [máx {dPs_max:.1f}]  {ok_ps}

─── TUBOS ────────────────────────────────────
  Gt  = {tubos['Gt']:.4f} kg/m²·s   v = {tubos['vt']:.3f} m/s
  Ret = {tubos['Ret']:.0f} [{tubos['reg']}]
  ht  = {tubos['ht']:.2f} W/m²·K
  ΔPt = {dPt_kPa:.4f} kPa   [máx {dPt_max:.1f}]  {ok_pt}

─── COEFICIENTE GLOBAL ───────────────────────
  R_ext  = {glob['Re']:.6f}   R_cond = {glob['Rc']:.6f}
  R_int  = {glob['Ri']:.6f}   R_foul = {glob['Rf']:.6f}
  U      = {glob['U']:.2f} W/m²·K

─── DIMENSIONAMENTO ──────────────────────────
  A calculada = {glob['A']:.4f} m²
  A instalada = {Ai:.4f} m²
  Excesso     = {ex:.1f} %

─── DIAGNÓSTICO ──────────────────────────────
  {diag}
"""
        if metodo == "bd":
            txt += (f"\n─── FATORES J ────────────────────────────────\n"
                    f"  Jc = {fat['Jc']:.4f}   Jl = {fat['Jl']:.4f}   Jb = {fat['Jb']:.4f}\n"
                    f"  Js = {fat['Js']:.4f}   Jr = {fat['Jr']:.4f}\n"
                    f"  ∏J = {PJ:.4f}\n")

        st.session_state[f"{prefixo}_resultado"] = txt

        memo = f"""════════════════════════════════════════════════════════════
  MEMORIAL DE CÁLCULO — {label}
════════════════════════════════════════════════════════════

[ETAPA 1] BALANÇO DE ENERGIA
  Q = ṁ · cp · |ΔT|
  Q_quente = {ms:.4f} × {cp_s:.1f} × ({Thi:.2f} − {Tho:.2f}) = {Q_W/1000:.4f} kW
  Q_frio   = {mt:.4f} × {cp_t:.1f} × ({Tco:.2f} − {Tci:.2f}) = {Q_W/1000:.4f} kW

[ETAPA 2] LMTD E FATOR F
  ΔT1 = {Thi:.2f} − {Tco:.2f} = {Thi-Tco:.4f} °C
  ΔT2 = {Tho:.2f} − {Tci:.2f} = {Tho-Tci:.4f} °C
  LMTD = {dTlm:.4f} °C
  F = {F:.4f}  (Np = {Np})

[ETAPA 3] GEOMETRIA
  di = d_o − 2e = {d:.5f} − 2×{e_p:.5f} = {di:.5f} m
  Nb = floor(Lta/Lbc) − 1 = {Nb}

[ETAPA 4] COEFICIENTE — CASCO
  Gs = {casco['Gs']:.4f} kg/m²·s   Res = {casco['Res']:.1f}
  hs = {casco['hs']:.2f} W/m²·K

[ETAPA 5] COEFICIENTE — TUBOS
  Ret = {tubos['Ret']:.1f}  [{tubos['reg']}]   Nut = {tubos['Nut']:.4f}
  ht = {tubos['ht']:.2f} W/m²·K

[ETAPA 6] TEMPERATURA NA PAREDE (iter {mw['it']}×)
  Tw,s = {mw['Twq']:.2f}°C → μw,s = {mw['mwq']:.4e} → φs = {mw['phq']:.4f}
  Tw,t = {mw['Twf']:.2f}°C → μw,t = {mw['mwf']:.4e} → φt = {mw['phf']:.4f}

[ETAPA 7] QUEDA DE PRESSÃO
  ΔPs = {dPs_kPa:.4f} kPa   ΔPt = {dPt_kPa:.4f} kPa

[ETAPA 8] COEFICIENTE GLOBAL
  R_ext={glob['Re']:.6f}  R_cond={glob['Rc']:.6f}
  R_int={glob['Ri']:.6f}  R_foul={glob['Rf']:.6f}
  U = {glob['U']:.2f} W/m²·K

[ETAPA 9] ÁREA DE TROCA
  A = Q / (U · LMTD · F)
  A = {Q_W:.2f} / ({glob['U']:.2f} × {dTlm:.4f} × {F:.4f}) = {glob['A']:.4f} m²
  Instalada = {Ai:.4f} m²   Excesso = {ex:.1f} %

════════════════════════════════════════════════════════════
"""
        st.session_state[f"{prefixo}_memorial"] = memo
        st.success("✅ Cálculo concluído! Veja os resultados na coluna direita.")
        st.rerun()

    except ValueError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")

# ═════════════════════════════════════════════════════════════════
with tab_k:
    render_aba("k", "kern")

with tab_b:
    render_aba("b", "bd")

st.markdown("---")
st.caption("Kern(1950) · Bell&Mueller(2001) · Kakaç&Liu(2002) · Thulukkanam(2013) · TEMA")
