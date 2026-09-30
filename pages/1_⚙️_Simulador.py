"""
Simulador Casco-e-Tubo — Streamlit
Kern & Bell-Delaware | v5 | CoolProp integrado
"""
import math
import streamlit as st

# ═════════════════════════════════════════════════════════════════
#  COOLPROP
# ═════════════════════════════════════════════════════════════════
try:
    import CoolProp.CoolProp as _CP
    COOLPROP_DISPONIVEL = True
    COOLPROP_VERSAO = _CP.get_global_param_string("version")
except ImportError:
    _CP = None
    COOLPROP_DISPONIVEL = False
    COOLPROP_VERSAO = None

# ═════════════════════════════════════════════════════════════════
#  CONFIG + CSS  (Correção 1 — estética)
# ═════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Simulador — Casco-e-Tubo",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Força tema escuro do Streamlit */
.stApp { background-color: #0B1520 !important; }
[data-testid="stSidebar"] { background-color: #111E2D !important; }
.stApp, .stApp p, .stApp span, .stApp label, .stApp div { color: #DFF0FF; }

/* Cartões do Streamlit */
[data-testid="stExpander"] {
    background-color: #172435; border: 1px solid #1F4068 !important;
    border-radius: 8px;
}
[data-testid="stExpander"] summary { color: #00C2FF !important; font-weight: 600; }

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox select {
    background-color: #1E3048 !important;
    color: #DFF0FF !important;
    border: 1px solid #1F4068 !important;
    border-radius: 6px !important;
}
.stTextInput label, .stSelectbox label, .stRadio label {
    color: #8FB0CF !important; font-size: 13px !important;
}

/* Botões */
.stButton > button {
    background-color: #1F4068 !important;
    color: #DFF0FF !important;
    border: 1px solid #00C2FF !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
}
.stButton > button:hover {
    background-color: #00C2FF !important;
    color: #0B1520 !important;
}
.stButton > button[kind="primary"] {
    background-color: #00C2FF !important;
    color: #0B1520 !important;
}

/* Abas */
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    background-color: #172435; color: #6A90B0;
    border-radius: 6px 6px 0 0; padding: 8px 18px; font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #00C2FF !important; color: #0B1520 !important;
}

/* Títulos */
h1, h2, h3 { color: #DFF0FF !important; }

/* Cabeçalho de navegação da etapa */
.stage-nav {
    background: #111E2D; border: 1px solid #1F4068;
    border-radius: 8px; padding: 12px 18px; margin-bottom: 12px;
}
.stage-nav .title {
    color: #00C2FF; font-family: 'Courier New', monospace;
    font-weight: 700; font-size: 14px; letter-spacing: 0.5px;
}
.stage-nav .progress {
    color: #8FB0CF; font-size: 12px; margin-top: 4px;
}

/* Aviso de validação */
.val-box {
    background: #2B1D0E; border: 2px solid #FFD166; border-radius: 8px;
    padding: 14px 18px; margin: 12px 0;
}
.val-box .h {
    color: #FFD166; font-weight: 700; font-size: 15px; margin-bottom: 8px;
}
.val-box ul { margin: 6px 0 0 20px; padding: 0; }
.val-box li { color: #FFE9A8; margin: 4px 0; font-size: 13px; }

/* Cards de destaque */
.card-info {
    background: #0F2438; border-left: 4px solid #00C2FF;
    border-radius: 6px; padding: 14px 18px; margin: 10px 0;
    color: #C8E4FF; font-size: 13px; line-height: 1.7;
}
.card-warn {
    background: #2B1D0E; border-left: 4px solid #FFD166;
    border-radius: 6px; padding: 14px 18px; margin: 10px 0;
    color: #FFE9A8; font-size: 13px; line-height: 1.7;
}
.card-ok {
    background: #0D2A1A; border-left: 4px solid #00E5A0;
    border-radius: 6px; padding: 14px 18px; margin: 10px 0;
    color: #A8FFD7; font-size: 13px; line-height: 1.7;
}
.card-title { font-weight: 700; color: #00C2FF; margin-bottom: 6px; }

/* Output */
.result-box {
    background: #0A1018; border: 1px solid #1F4068;
    border-radius: 8px; padding: 18px;
    font-family: 'Courier New', monospace; font-size: 12.5px;
    white-space: pre-wrap; line-height: 1.6; color: #00E5A0;
    max-height: 700px; overflow-y: auto;
}
.nesta-box {
    background: #0A1018; border: 1px solid #C084FC;
    border-radius: 8px; padding: 20px;
    font-family: 'Courier New', monospace; font-size: 12.5px;
    white-space: pre-wrap; line-height: 1.7; color: #D6B8FF;
    max-height: 700px; overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

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
        "faixa": (0, 200),
        "fonte": "Incropera et al. (2007), Tab. A.6",
    },
    "Ar (1 atm)": {
        "rho": lambda T: 353.05 / (T + 273.15),
        "mu":  lambda T: 1.716e-5 * ((T+273.15)/273.15)**1.5 * (273.15+110.4)/((T+273.15)+110.4),
        "cp":  lambda T: 1006.0 + 0.0448*T + 1.6e-4*T**2,
        "k":   lambda T: 0.0241 + 7.5e-5*T - 1.0e-8*T**2,
        "faixa": (-20, 400),
        "fonte": "Incropera et al. (2007), Tab. A.4",
    },
}

FLUIDOS_COOLPROP = {
    "Água (CoolProp)":"Water","Água pesada (D2O)":"HeavyWater",
    "Ar (CoolProp)":"Air","Nitrogênio":"Nitrogen","Oxigênio":"Oxygen",
    "Argônio":"Argon","Hélio":"Helium","Hidrogênio":"Hydrogen",
    "Dióxido de carbono (CO₂)":"CarbonDioxide","Amônia (NH₃)":"Ammonia",
    "Metano":"Methane","Etano":"Ethane","Propano":"n-Propane",
    "Isobutano":"IsoButane","n-Butano":"n-Butane",
    "n-Pentano":"n-Pentane","n-Hexano":"n-Hexane","n-Heptano":"n-Heptane",
    "n-Octano":"n-Octane","n-Decano":"n-Decane",
    "Benzeno":"Benzene","Tolueno":"Toluene","Etilbenzeno":"EthylBenzene",
    "Metanol":"Methanol","Etanol":"Ethanol",
    "R134a":"R134a","R410A":"R410A","R404A":"R404A","R407C":"R407C",
    "R507A":"R507A","R32":"R32","R152a":"R152A","R1234yf":"R1234yf",
    "R1234ze(E)":"R1234ze(E)","R245fa":"R245fa","R125":"R125",
    "R143a":"R143a","R227ea":"R227EA",
    "R22 (legado)":"R22","R11 (legado)":"R11","R12 (legado)":"R12","R123 (legado)":"R123",
}

TAB10 = {
    30:[(1e5,0.321,-0.388,1.450,0.519),(1e4,0.321,-0.388,None,None),
        (1e3,0.593,-0.477,None,None),(1e2,1.360,-0.657,None,None),(10,1.400,-0.667,None,None)],
    45:[(1e5,0.370,-0.396,1.930,0.500),(1e4,0.370,-0.396,None,None),
        (1e3,0.730,-0.500,None,None),(1e2,0.498,-0.656,None,None),(10,1.550,-0.667,None,None)],
    90:[(1e5,0.370,-0.395,1.187,0.370),(1e4,0.107,-0.266,None,None),
        (1e3,0.408,-0.460,None,None),(1e2,0.900,-0.631,None,None),(10,0.970,-0.667,None,None)],
}
TAB11 = {
    30:[(1e5,0.372,-0.123,7.00,0.500),(1e4,0.486,-0.152,None,None),
        (1e3,4.570,-0.476,None,None),(1e2,45.100,-0.973,None,None),(10,48.000,-1.000,None,None)],
    45:[(1e5,0.303,-0.126,6.59,0.520),(1e4,0.333,-0.136,None,None),
        (1e3,3.500,-0.476,None,None),(1e2,26.200,-0.913,None,None),(10,32.000,-1.000,None,None)],
    90:[(1e5,0.391,-0.148,6.30,0.378),(1e4,0.0815,+0.022,None,None),
        (1e3,6.090,-0.602,None,None),(1e2,32.100,-0.963,None,None),(10,35.000,-1.000,None,None)],
}
K1N = {
    (1,30):(0.319,2.142),(1,45):(0.319,2.142),(1,60):(0.319,2.142),(1,90):(0.215,2.207),
    (2,30):(0.249,2.207),(2,45):(0.249,2.207),(2,60):(0.249,2.207),(2,90):(0.156,2.291),
    (4,30):(0.175,2.285),(4,45):(0.175,2.285),(4,60):(0.175,2.285),(4,90):(0.158,2.263),
    (6,30):(0.0743,2.499),(6,45):(0.0743,2.499),(6,60):(0.0743,2.499),(6,90):(0.0402,2.617),
    (8,30):(0.0365,2.675),(8,45):(0.0365,2.675),(8,60):(0.0365,2.675),(8,90):(0.0331,2.643),
}

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
        if Q<=0: raise ValueError("Q≤0 → Th,o deve ser menor que Th,i")
        Tco=Tci+(Q-Q_lat_t)/(mt*cpt)
    else:
        Tco=Tval; Q=mt*cpt*(Tco-Tci)+Q_lat_t
        if Q<=0: raise ValueError("Q≤0 → Tc,o deve ser maior que Tc,i")
        Tho=Thi-(Q-Q_lat_s)/(ms*cps)
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
#  PERSISTÊNCIA DE VALORES (Correção 5 — valores somem ao voltar)
# ═════════════════════════════════════════════════════════════════
if "_vals" not in st.session_state:
    st.session_state["_vals"] = {}

def _V(key, default=""):
    """Lê valor persistente."""
    return st.session_state["_vals"].get(key, default)

def _S(key, val):
    """Grava valor persistente."""
    st.session_state["_vals"][key] = val

def ptext(label, key, default="", help=None, disabled=False):
    """Text input persistente entre páginas."""
    widget_key = f"_w_{key}"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = _V(key, default)
    v = st.text_input(label, key=widget_key, help=help, disabled=disabled)
    _S(key, v)
    return v

def pselect(label, key, options, default=None, help=None):
    """Selectbox persistente."""
    widget_key = f"_w_{key}"
    if widget_key not in st.session_state:
        if default is None: default = options[0]
        st.session_state[widget_key] = _V(key, default)
    # Garante que o valor esteja nas opções
    if st.session_state[widget_key] not in options:
        st.session_state[widget_key] = options[0]
    v = st.selectbox(label, options, key=widget_key, help=help)
    _S(key, v)
    return v

def pradio(label, key, options, default=None, horizontal=True, help=None):
    """Radio persistente."""
    widget_key = f"_w_{key}"
    if widget_key not in st.session_state:
        if default is None: default = options[0]
        st.session_state[widget_key] = _V(key, default)
    if st.session_state[widget_key] not in options:
        st.session_state[widget_key] = options[0]
    v = st.radio(label, options, key=widget_key, horizontal=horizontal, help=help)
    _S(key, v)
    return v

def pf(key, default=0.0):
    """Parse float do valor persistente."""
    try:
        return float(str(_V(key, "")).replace(",", ".").strip())
    except:
        return default

def pi(key, default=0):
    """Parse int do valor persistente."""
    try:
        return int(float(str(_V(key, "")).replace(",", ".").strip()))
    except:
        return default

# ═════════════════════════════════════════════════════════════════
#  TEXTO "NESTA ETAPA" (Correção 6 — equações legíveis)
# ═════════════════════════════════════════════════════════════════
NESTA_ETAPA = [
"""┌─ 🌡️  TEMPERATURAS E OBJETIVO ────────────────────────┐

FÓRMULAS DESTA ETAPA
─────────────────────
  ▸ Balanço de energia (1ª Lei da Termodinâmica):

        Q = ṁ · cp · ΔT          (para cada lado)

  ▸ Igualdade dos calores trocados:

        Q_quente = Q_frio

  ▸ Diferença de temperatura média logarítmica (LMTD):

        ΔT₁ − ΔT₂
        ─────────────────────  onde  ΔT₁ = Th,i − Tc,o
          ln(ΔT₁ / ΔT₂)                ΔT₂ = Th,o − Tc,i

IMPACTO NO PROJETO
───────────────────
  • Essas temperaturas definem o Q TOTAL do trocador.
  • Quanto MENOR o ΔT entre os fluidos, MENOR a força motriz
    térmica → para o mesmo Q, exige MAIS área de troca.
  • Se a T de saída pedida violar a 2ª Lei, o programa avisa.

GLOSSÁRIO
─────────
  Th,i / Th,o  T entrada / saída do fluido QUENTE (°C)
  Tc,i / Tc,o  T entrada / saída do fluido FRIO   (°C)
  Q            Taxa de calor trocado (W)
  ṁ            Vazão mássica (kg/s)
  cp           Calor específico (J/kg·K)
  ΔT           Diferença de temperatura (°C)
""",
"""┌─ 🧪  FLUIDOS E VAZÕES ────────────────────────────────┐

FÓRMULAS DESTA ETAPA
─────────────────────
  ▸ Número de Reynolds (regime de escoamento):

        Re = D · G / μ        com  G = ṁ / A

  ▸ Número de Prandtl (difusão qtd.mov. / difusão calor):

        Pr = μ · cp / k

  ▸ Correção de viscosidade na parede:

        φ = (μ_bulk / μ_w)^0,14
        h_real = h_ideal × φ

COMO O PROGRAMA USA
───────────────────
  ▸ No casco (Kern):

        hs = (0,36 · k / Dhs) · Re^0,55 · Pr^(1/3)

  ▸ Nos tubos (Sieder-Tate / Gnielinski):

        Nu = f(Re, Pr)    →    h = Nu · k / di

IMPACTO NO PROJETO
───────────────────
  • Fluidos MAIS VISCOSOS → Re menor → h menor → mais área.
  • Use o BANCO DE DADOS para preencher ρ, μ, cp, k automaticamente.
  • Após calcular, clique em ↺ para refinar com a T média real.

GLOSSÁRIO
─────────
  ρ (rho)   Massa específica (kg/m³)
  μ (mu)    Viscosidade dinâmica bulk (Pa·s)
  cp        Calor específico (J/kg·K)
  k         Condutividade térmica (W/m·K)
  ṁₛ / ṁₜ   Vazão mássica casco / tubo (kg/s)
  Re / Pr   Adimensionais (Reynolds / Prandtl)
""",
"""┌─ 📐  GEOMETRIA DO TROCADOR ───────────────────────────┐

FÓRMULAS DESTA ETAPA
─────────────────────
  ▸ Diâmetro interno do tubo:

        di = d_o − 2·e

  ▸ Número de chicanas:

        Nb = ⌊Lta / Lbc⌋ − 1

  ▸ Fator de correção da LMTD (multipasse, Bowman-Mueller):

        F = f(P, R, Nₚ)     →     Nₚ = 1  ⇒  F = 1,0

IMPACTO NO PROJETO
───────────────────
  • A geometria define a ÁREA DISPONÍVEL:

        A_inst = Nt · π · d_o · Lta

  • Use 🔮 "Estimar geometria" para derivar tudo a partir de Q.
  • Chicanas mais próximas (Lbc↓) → mais h, mas mais ΔP.
  • θ = 30° empacota mais tubos que θ = 90°.

TABELA DE REFERÊNCIA — Nₜ × Dₛ (aprox., tubo 3/4")
    Dₛ (m)     Dₛ (pol.)     Nₜ aprox.
    ───────    ──────────    ──────────
     0,203        8"             ~37
     0,254       10"             ~62
     0,305       12"             ~92
     0,387      15¼"            ~151
     0,489      19¼"            ~277
     0,591      23¼"            ~377

GLOSSÁRIO
─────────
  d_o / di   Diâmetro externo / interno do tubo (m)
  e          Espessura da parede (m)
  Lta / Ltp  Comprimento do tubo / Passo entre tubos (m)
  Ds / Lbc   Diâmetro do casco / Espaç. chicanas (m)
  θ / Nₚ     Ângulo do arranjo (°) / Nº de passes
""",
"""┌─ ⚙️  LIMITES, FASE, FOULING E CÁLCULO ────────────────┐

FÓRMULAS DESTA ETAPA
─────────────────────
  ▸ Queda de pressão (casco, Kern):

        ΔPs = fs · Gs² · (Nb+1) · Ds / (2 · ρₛ · Dhs · φₛ)

  ▸ Queda de pressão (tubos):

        ΔPt = ft · (Lta/di) · (Gt²/2ρₜ) · Np + retornos

  ▸ Resistência de fouling:

        R_foul = Rf,ext + (d_o / di) · Rf,int

  ▸ Coeficiente global e área:

        U = 1 / (R_ext + R_cond + R_int + R_foul)

        A = Q / (U · LMTD · F)

IMPACTO NO PROJETO
───────────────────
  • ΔP calculado > limite definido → projeto REPROVADO.
  • Mudança de fase adiciona calor latente:

        Q_total = Q_sensível + ṁ · λ · x

  • Fouling maior → U menor → área maior.
  • Excesso de área ideal: entre 10 % e 25 %.

GLOSSÁRIO
─────────
  ΔPs / ΔPt   Queda de pressão casco / tubos (kPa)
  Rf          Resistência de fouling (m²·K/W)
  U / A       Coef. global (W/m²·K) / Área de troca (m²)
  λ / x       Calor latente (kJ/kg) / Fração que muda de fase
""",
]

# ═════════════════════════════════════════════════════════════════
#  WIDGET DE BANCO DE FLUIDOS (Correção 4 — funciona para casco e tubo)
# ═════════════════════════════════════════════════════════════════
def widget_fluido(prefixo, lado, cor):
    """lado = 's' (casco) ou 't' (tubos)"""
    nome_lado = "Casco (quente)" if lado == "s" else "Tubos (frio)"
    emoji = "🔵" if lado == "s" else "🟠"

    st.markdown(f"**{emoji} Banco de Fluidos — {nome_lado}**")

    nomes = list(FLUIDOS_DB.keys())
    if COOLPROP_DISPONIVEL:
        nomes += sorted(FLUIDOS_COOLPROP.keys())

    c1, c2 = st.columns([2, 1])
    with c1:
        fluido = pselect("Fluido:", f"{prefixo}_fluido_{lado}", nomes)
    with c2:
        if COOLPROP_DISPONIVEL:
            st.markdown(
                f"<div style='color:#00E5A0;font-size:11px;padding-top:28px;'>"
                f"🧬 CoolProp {COOLPROP_VERSAO}</div>",
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        T_ref = ptext("T ref. (°C):", f"{prefixo}_Tref_{lado}")
    with c2:
        P_ref = ptext("P ref. (kPa):", f"{prefixo}_Pref_{lado}", "101.325")
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_sug = st.button("💡 P", key=f"{prefixo}_sug_{lado}", help="Sugerir P de saturação")

    # Feedback
    fb_key = f"{prefixo}_fb_{lado}"
    if fb_key in st.session_state:
        st.markdown(st.session_state[fb_key], unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button(f"🔎 Buscar propriedades", key=f"{prefixo}_buscar_{lado}",
                     use_container_width=True):
            try:
                T = pf(f"{prefixo}_Tref_{lado}")
                P_kPa = pf(f"{prefixo}_Pref_{lado}", 101.325)
                p = propriedades_fluido(fluido, T, P_Pa=P_kPa*1000.0)
                _S(f"{prefixo}_rho_{lado}", f"{p['rho']:.4f}")
                _S(f"{prefixo}_mu_{lado}",  f"{p['mu']:.6e}")
                _S(f"{prefixo}_cp_{lado}",  f"{p['cp']:.2f}")
                _S(f"{prefixo}_k_{lado}",   f"{p['k']:.5f}")
                aviso = "⚠️ fora da faixa!" if p["fora_faixa"] else "✔ dentro da faixa"
                fase = f" | fase: {p['fase']}" if p.get('fase') else ""
                st.session_state[fb_key] = (
                    f"<div class='card-ok'>"
                    f"✔ Preenchido: ρ={p['rho']:.2f} kg/m³ · μ={p['mu']:.3e} Pa·s · "
                    f"cp={p['cp']:.1f} J/kg·K · k={p['k']:.4f} W/m·K<br>"
                    f"<small>Faixa: {p['faixa'][0]:.1f} a {p['faixa'][1]:.1f} °C — {aviso}{fase} | {p['fonte']}</small>"
                    f"</div>")
                st.rerun()
            except Exception as e:
                st.session_state[fb_key] = f"<div class='card-warn'>⚠️ {e}</div>"
                st.rerun()
    with c2:
        if st.button("↺ Usar T média (bulk)", key=f"{prefixo}_bulk_{lado}",
                     use_container_width=True, help="Após calcular"):
            T_bulk = st.session_state.get(f"{prefixo}_Tbulk_{lado}")
            if T_bulk is None:
                st.session_state[fb_key] = "<div class='card-warn'>⚠️ Faça um cálculo primeiro.</div>"
                st.rerun()
            else:
                _S(f"{prefixo}_Tref_{lado}", f"{T_bulk:.2f}")
                st.rerun()

    # Sugerir P
    if btn_sug:
        if fluido not in FLUIDOS_COOLPROP or not COOLPROP_DISPONIVEL:
            st.session_state[fb_key] = "<div class='card-warn'>💡 Sugestão de P só para fluidos CoolProp.</div>"
        else:
            try:
                T = pf(f"{prefixo}_Tref_{lado}")
                fid = FLUIDOS_COOLPROP[fluido]
                T_K = T + 273.15
                T_sat_K = _CP.PropsSI("T","P",101325.0,"Q",0,fid)
                P_sat_Pa = _CP.PropsSI("P","T",T_K,"Q",0,fid)
                P_sat_kPa = P_sat_Pa/1000
                st.session_state[fb_key] = (
                    f"<div class='card-info'>"
                    f"<b>💡 Sugestão de Pressão</b><br>"
                    f"T_sat @ 1 atm = {T_sat_K-273.15:.1f} °C<br>"
                    f"P_sat em {T:.1f} °C = <b>{P_sat_kPa:.2f} kPa</b><br>"
                    f"▸ Líquido: P > {P_sat_kPa:.1f} kPa (sugestão {P_sat_kPa*1.2:.0f})<br>"
                    f"▸ Vapor:   P < {P_sat_kPa:.1f} kPa (sugestão {P_sat_kPa*0.5:.0f})"
                    f"</div>")
            except Exception as e:
                st.session_state[fb_key] = f"<div class='card-warn'>⚠️ Sem saturação nesta T.</div>"
        st.rerun()

# ═════════════════════════════════════════════════════════════════
#  CABEÇALHO
# ═════════════════════════════════════════════════════════════════
st.title("⚙️ Simulador Casco-e-Tubo")
st.caption("**Kern** & **Bell-Delaware**  ·  v5  ·  com Mudança de Fase, Fouling e CoolProp")

tab_k, tab_b = st.tabs(["🔵 KERN", "🟠 BELL-DELAWARE"])

# ═════════════════════════════════════════════════════════════════
#  VALIDAÇÃO POR PÁGINA
# ═════════════════════════════════════════════════════════════════
def validar_pagina(prefixo, pag):
    obrig = {
        0: [("Thi","Th,i — T entrada quente"),
            ("Tci","Tc,i — T entrada frio"),
            ("Tsaida","T de saída")],
        1: [("rho_s","ρₛ — massa específica casco"),
            ("mu_s","μₛ — viscosidade casco"),
            ("cp_s","cp,s — calor esp. casco"),
            ("k_s","kₛ — condutividade casco"),
            ("ms","ṁₛ — vazão casco"),
            ("rho_t","ρₜ — massa específica tubos"),
            ("mu_t","μₜ — viscosidade tubos"),
            ("cp_t","cp,t — calor esp. tubos"),
            ("k_t","kₜ — condutividade tubos"),
            ("mt","ṁₜ — vazão tubos")],
        2: [("d","d_o — diâm. externo tubo"),
            ("e_parede","e — espessura parede"),
            ("Ds","Dₛ — diâmetro casco"),
            ("Lta","Lₜₐ — comprimento tubo"),
            ("Ltp","Lₜₚ — passo tubos"),
            ("Lbc","Lbc — espaç. chicanas"),
            ("Nt","Nₜ — número de tubos")],
        3: [],
    }
    faltando = []
    for k, nome in obrig.get(pag, []):
        v = _V(f"{prefixo}_{k}", "")
        if not str(v).strip():
            faltando.append(nome)
    return (len(faltando)==0, faltando)

# ═════════════════════════════════════════════════════════════════
#  RENDER DE UMA ABA
# ═════════════════════════════════════════════════════════════════
def render_aba(prefixo, cor, metodo):
    pag_key = f"{prefixo}_pagina"
    if pag_key not in st.session_state:
        st.session_state[pag_key] = 0
    pag = st.session_state[pag_key]
    titulos = ["🌡️ Temperaturas e Objetivo", "🧪 Fluidos e Vazões",
               "📐 Geometria do Trocador", "⚙️ Limites, Fase e Cálculo"]

    col_l, col_r = st.columns([1, 1], gap="large")

    # ══════════ COLUNA ESQUERDA ══════════
    with col_l:
        # Barra de navegação (Correção 2 — formato limpo)
        st.markdown(
            f"<div class='stage-nav'>"
            f"<div class='title'>🎓 MODO PASSO A PASSO</div>"
            f"<div class='progress'>Página <b>{pag+1}</b> de 4 — {titulos[pag]}</div>"
            f"</div>", unsafe_allow_html=True)

        nav1, nav2, nav3 = st.columns([1, 1, 1])
        with nav1:
            if st.button("◀ Anterior", disabled=(pag==0), key=f"{prefixo}_ant",
                         use_container_width=True):
                st.session_state[pag_key] = pag - 1
                st.rerun()
        with nav2:
            # indicador vazio
            st.markdown(f"<div style='text-align:center;color:#6A90B0;padding-top:8px;'>"
                        f"{pag+1}/4</div>", unsafe_allow_html=True)
        with nav3:
            if st.button("Próximo ▶", disabled=(pag==3), key=f"{prefixo}_prox",
                         use_container_width=True):
                ok, faltando = validar_pagina(prefixo, pag)
                if ok:
                    st.session_state[pag_key] = pag + 1
                    st.rerun()
                else:
                    # Correção 2 — mensagem de validação limpa
                    items = "".join(f"<li>{c}</li>" for c in faltando)
                    st.markdown(
                        f"<div class='val-box'>"
                        f"<div class='h'>⚠️ Preencha os campos desta etapa</div>"
                        f"<div>Para avançar, preencha todos os campos obrigatórios:</div>"
                        f"<ul>{items}</ul>"
                        f"</div>", unsafe_allow_html=True)

        st.markdown("---")

        # ─── PÁGINA 1 ───
        if pag == 0:
            st.markdown(
                "<div class='card-info'>"
                "<b>💡 Objetivo desta etapa:</b> definir as temperaturas de entrada "
                "e escolher qual temperatura de saída o programa deve calcular."
                "</div>", unsafe_allow_html=True)

            st.subheader("🌡️ Temperaturas do Processo")
            c1, c2 = st.columns(2)
            with c1:
                ptext("Th,i — quente entrada (°C) ✱", f"{prefixo}_Thi")
            with c2:
                ptext("Tc,i — frio entrada (°C) ✱", f"{prefixo}_Tci")

            st.markdown("**Objetivo:** qual temperatura de saída calcular?")
            obj = pradio("Objetivo",
                         f"{prefixo}_obj",
                         ["Th,o → calcula Tc,o", "Tc,o → calcula Th,o"],
                         horizontal=True)
            if obj.startswith("Th,o"):
                ptext("Th,o — quente saída (°C) ✱", f"{prefixo}_Tsaida")
            else:
                ptext("Tc,o — frio saída (°C) ✱", f"{prefixo}_Tsaida")

        # ─── PÁGINA 2 ───
        elif pag == 1:
            st.markdown(
                "<div class='card-info'>"
                "<b>💡 Objetivo:</b> definir propriedades dos fluidos e vazões. "
                "Use o banco de fluidos abaixo para preencher automaticamente."
                "</div>", unsafe_allow_html=True)

            # Banco de fluidos do casco
            with st.expander("🔵 Banco de Dados — Fluido do Casco", expanded=True):
                widget_fluido(prefixo, "s", cor)
            st.markdown("**Propriedades do Casco (editáveis):**")
            c1, c2 = st.columns(2)
            with c1:
                ptext("ρₛ (kg/m³)", f"{prefixo}_rho_s")
                ptext("cp,s (J/kg·K)", f"{prefixo}_cp_s")
                ptext("ṁₛ (kg/s)", f"{prefixo}_ms")
            with c2:
                ptext("μₛ (Pa·s)", f"{prefixo}_mu_s")
                ptext("kₛ (W/m·K)", f"{prefixo}_k_s")

            st.markdown("---")

            # Banco de fluidos dos tubos
            with st.expander("🟠 Banco de Dados — Fluido dos Tubos", expanded=True):
                widget_fluido(prefixo, "t", cor)
            st.markdown("**Propriedades dos Tubos (editáveis):**")
            c1, c2 = st.columns(2)
            with c1:
                ptext("ρₜ (kg/m³)", f"{prefixo}_rho_t")
                ptext("cp,t (J/kg·K)", f"{prefixo}_cp_t")
                ptext("ṁₜ (kg/s)", f"{prefixo}_mt")
            with c2:
                ptext("μₜ (Pa·s)", f"{prefixo}_mu_t")
                ptext("kₜ (W/m·K)", f"{prefixo}_k_t")

        # ─── PÁGINA 3 ───
        elif pag == 2:
            st.markdown(
                "<div class='card-info'>"
                "<b>💡 Objetivo:</b> definir a geometria do trocador. Use o botão "
                "🔮 para estimar tudo a partir dos dados térmicos das páginas 1 e 2."
                "</div>", unsafe_allow_html=True)

            if st.button("🔮 Estimar geometria a partir dos dados térmicos",
                         key=f"{prefixo}_estimar", use_container_width=True):
                _estimar_geometria(prefixo, metodo)

            # Correção 10 — ajuda contextual do tubo
            st.markdown("#### 📐 Tubo")
            with st.expander("💡 Ajuda — Geometria do Tubo", expanded=False):
                st.markdown(
                    "<div class='card-info'>"
                    "<b>Valores comerciais (TEMA):</b><br>"
                    "• d_o = 3/4\" → 0,01905 m<br>"
                    "• d_o = 1\"   → 0,02540 m<br>"
                    "• d_o = 1¼\"  → 0,03175 m<br>"
                    "• d_o = 1½\"  → 0,03810 m<br><br>"
                    "<b>Espessura típica (BWG 16-14):</b> 0,00165–0,00211 m<br><br>"
                    "<b>Fórmula:</b> di = d_o − 2·e"
                    "</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                ptext("d_o — diâm. externo (m)", f"{prefixo}_d")
                ptext("e — espessura (m)", f"{prefixo}_e_parede")
            with c2:
                try:
                    d_v = pf(f"{prefixo}_d"); e_v = pf(f"{prefixo}_e_parede")
                    di_v = d_v - 2*e_v
                    di_txt = f"{di_v:.5f}" if di_v > 0 else "—"
                except:
                    di_txt = "—"
                st.text_input("di — diâm. interno (m) [calculado]",
                              value=di_txt, disabled=True)
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

            # Nb calculado
            Lta_v = pf(f"{prefixo}_Lta"); Lbc_v = pf(f"{prefixo}_Lbc")
            if Lbc_v > 0:
                Nb_calc = max(1, int(Lta_v/Lbc_v) - 1)
                st.markdown(
                    f"<div class='card-ok'>Nb calculado = <b>{Nb_calc}</b> chicanas</div>",
                    unsafe_allow_html=True)

            # Correção 10 — ajuda contextual de θ e Np
            st.markdown("#### ⚙️ Arranjo e Passes")
            c1, c2 = st.columns(2)
            with c1:
                theta_opts = [30,45,60,90] if metodo=="kern" else [30,45,90]
                theta = pselect("Ângulo θ:", f"{prefixo}_theta", theta_opts)
                with st.expander("💡 O que é θ?", expanded=False):
                    st.markdown("""
**Ângulo do arranjo dos tubos** — define como os tubos são distribuídos
no interior do casco.

| θ | Compacidade | Limpeza mecânica | ΔP casco |
|:---:|:---:|:---:|:---:|
| **30°** (triangular) | ✅ Alta | ❌ Só química | Alto |
| **45°** (quadrado rot.) | Média | Limitada | Médio |
| **60°** (triangular rot.) | Alta | ❌ Só química | Alto |
| **90°** (quadrado) | Baixa | ✅ Fácil | Baixo |

**Recomendação:**
- Fluidos limpos → 30°
- Fluidos com fouling → 90°
- Caso intermediário → 45°
""")
            with c2:
                Np = pselect("Passes Nₚ:", f"{prefixo}_Np", [1,2,4,6,8])
                with st.expander("💡 O que é Nₚ?", expanded=False):
                    st.markdown("""
**Número de passes nos tubos** — quantas vezes o fluido frio percorre
o feixe antes de sair.

| Nₚ | v_tubo | h_tubo | ΔP_tubo | Fator F |
|:---:|:---:|:---:|:---:|:---:|
| 1 | Menor | Menor | Mínimo | 1,00 |
| 2 | Dupla | Maior | 2× | ~0,90 |
| 4 | Alta | Muito maior | 4× | ~0,85 |
| 6 | Muito alta | — | 6× | Pode ser < 0,75 |

**Recomendação:**
- Nₚ = 1 → quando F precisa ser 1,0 (contracorrente)
- Nₚ = 2 → maioria dos casos industriais
- Nₚ = 4 → fluidos viscosos no tubo
- Nₚ ≥ 6 → use 2 cascos em série
""")

            # Calculadora Db → Ds
            with st.expander("📐 Calculadora Db → Ds (Coulson & Richardson)"):
                if st.button("Calcular Db e Ds", key=f"{prefixo}_btn_db"):
                    try:
                        Nt_v = pi(f"{prefixo}_Nt")
                        do_v = pf(f"{prefixo}_d")
                        Np_v = int(_V(f"{prefixo}_Np", 1))
                        th_v = int(_V(f"{prefixo}_theta", 30))
                        r = bundle_diameter(Nt_v, do_v, Np_v, th_v)
                        _S(f"{prefixo}_Ds_est", f"{r['Ds']:.4f}")
                        _S(f"{prefixo}_Ltp_sug", f"{r['Ltp_sug']:.5f}")
                        st.success(f"**Db = {r['Db']*1000:.1f} mm**  |  **Ds sugerido = {r['Ds']*1000:.1f} mm**")
                        st.caption(f"K₁ = {r['K1']}  n = {r['n1']}  |  Ltp sug. = {r['Ltp_sug']*1000:.2f} mm")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if _V(f"{prefixo}_Ds_est"):
                    if st.button("↑ Usar Ds sugerido nos campos", key=f"{prefixo}_usar_db"):
                        _S(f"{prefixo}_Ds", _V(f"{prefixo}_Ds_est"))
                        _S(f"{prefixo}_Ltp", _V(f"{prefixo}_Ltp_sug"))
                        st.rerun()

        # ─── PÁGINA 4 ───
        elif pag == 3:
            st.markdown(
                "<div class='card-info'>"
                "<b>💡 Objetivo:</b> limites de ΔP, mudança de fase e fouling. "
                "Depois clique em <b>▶ CALCULAR</b>."
                "</div>", unsafe_allow_html=True)

            st.markdown("#### ⚡ Limites de ΔP")
            preset = pselect("Preset de serviço:", f"{prefixo}_preset_dp",
                             list(LIMITES_DP.keys()))
            ds0, dt0, ref0 = LIMITES_DP.get(preset, (0,0,""))
            if ds0 > 0:
                _S(f"{prefixo}_dPs_max", str(ds0))
                _S(f"{prefixo}_dPt_max", str(dt0))
                st.markdown(
                    f"<div class='card-info'>📖 <b>Referência:</b> {ref0}<br>"
                    f"ΔPs máx = {ds0} kPa  |  ΔPt máx = {dt0} kPa</div>",
                    unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                ptext("ΔP máx. casco (kPa)", f"{prefixo}_dPs_max")
            with c2:
                ptext("ΔP máx. tubos (kPa)", f"{prefixo}_dPt_max")

            st.markdown("---")
            st.markdown("#### ⇌ Mudança de Fase")
            ativa = st.checkbox("Há mudança de fase?", key=f"{prefixo}_fase_on")
            if ativa:
                pradio("Tipo:", f"{prefixo}_fase_tipo",
                       ["Condensação","Vaporização"], horizontal=True)
                pradio("Lado afetado:", f"{prefixo}_fase_lado",
                       ["Casco (quente)","Tubos (frio)"], horizontal=True)
                c1, c2 = st.columns(2)
                with c1:
                    ptext("λ — calor latente (kJ/kg)", f"{prefixo}_lambda", "2257")
                with c2:
                    ptext("x — fração [0-1]", f"{prefixo}_frac", "1.0")

            st.markdown("---")
            st.markdown("#### 🔧 Fouling (incrustação)")
            fp = pselect("Preset TEMA:", f"{prefixo}_fp",
                         list(FOULING_PRESETS.keys()))
            fe0, fi0 = FOULING_PRESETS.get(fp, (0.0002, 0.0002))
            if fp != "Personalizado":
                _S(f"{prefixo}_Rfe", str(fe0))
                _S(f"{prefixo}_Rfi", str(fi0))
            c1, c2 = st.columns(2)
            with c1:
                ptext("Rf externo (m²·K/W)", f"{prefixo}_Rfe")
            with c2:
                ptext("Rf interno (m²·K/W)", f"{prefixo}_Rfi")

            st.markdown("---")
            if st.button(f"▶ CALCULAR — {metodo.upper()}",
                         key=f"{prefixo}_calc",
                         use_container_width=True,
                         type="primary"):
                _executar_calculo(prefixo, metodo)

    # ══════════ COLUNA DIREITA ══════════
    with col_r:
        st.markdown(f"### 📊 Resultados — {metodo.upper()}")

        # Correção 8 — "Nesta Etapa" em destaque (primeira aba)
        t_etapa, t_resumo, t_memo = st.tabs(
            ["🧭 Nesta Etapa", "📊 Resumo", "📘 Memorial"])

        with t_etapa:
            texto = NESTA_ETAPA[pag]
            st.markdown(f"<div class='nesta-box'>{texto}</div>",
                        unsafe_allow_html=True)
            # Correção 7 — T_parede explicada dentro de Nesta Etapa (pág 2)
            if pag == 1:
                st.markdown("---")
                st.markdown("#### 🧱 Temperatura da Parede (cálculo iterativo)")
                st.markdown("""
<div class='card-info'>
<b>Por que importa:</b> a viscosidade dos líquidos muda perto da parede
(mais fria ou mais quente), alterando o perfil de velocidade e o
coeficiente h. Ignorar isso <b>superestima h</b> em até 20–30%.

<b>Como o programa faz:</b>
<ol style='margin-top:8px;'>
<li>Chuta T_parede = média(T_quente, T_fria)</li>
<li>Calcula μ de cada fluido em T_parede (Andrade para líquidos)</li>
<li>Recalcula h com φ = (μ_bulk / μ_w)^0,14</li>
<li>Recalcula T_parede pelo circuito de resistências</li>
<li>Repete 2–4 até T_parede variar menos que 0,1 °C</li>
</ol>
Normalmente converge em 2–4 iterações.
</div>
""", unsafe_allow_html=True)

        with t_resumo:
            resultado = st.session_state.get(f"{prefixo}_resultado")
            if resultado:
                st.markdown(f"<div class='result-box'>{resultado}</div>",
                            unsafe_allow_html=True)
            else:
                st.info("Preencha os campos e clique em ▶ CALCULAR na coluna da esquerda.")

        with t_memo:
            memo = st.session_state.get(f"{prefixo}_memorial")
            if memo:
                st.markdown(f"<div class='result-box'>{memo}</div>",
                            unsafe_allow_html=True)
            else:
                st.info("O memorial aparece após CALCULAR.")

# ═════════════════════════════════════════════════════════════════
#  ESTIMAR GEOMETRIA (Correção 9 — bug resolvido)
# ═════════════════════════════════════════════════════════════════
def _estimar_geometria(prefixo, metodo):
    try:
        Thi = pf(f"{prefixo}_Thi"); Tci = pf(f"{prefixo}_Tci")
        Tsaida = pf(f"{prefixo}_Tsaida")
        ms = pf(f"{prefixo}_ms"); cp_s = pf(f"{prefixo}_cp_s")
        mt = pf(f"{prefixo}_mt"); cp_t = pf(f"{prefixo}_cp_t")

        # Correção 9: leitura robusta do objetivo
        obj_raw = _V(f"{prefixo}_obj", "Th,o → calcula Tc,o")
        obj = "Th,o" if "Th,o" in str(obj_raw)[:6] else "Tc,o"

        # Validação antes de calcular
        if Thi == 0 or Tci == 0 or Tsaida == 0:
            st.error("⚠️ Preencha as temperaturas na Página 1 antes de estimar.")
            return
        if ms == 0 or cp_s == 0 or mt == 0 or cp_t == 0:
            st.error("⚠️ Preencha vazões e cp na Página 2 antes de estimar.")
            return

        Tho, Tco, Q = resolver_T(obj, Thi, Tci, Tsaida, ms, cp_s, mt, cp_t)
        lmtd_v = lmtd(Thi, Tho, Tci, Tco)

        mu_s_e = pf(f"{prefixo}_mu_s", 1e-3)
        mu_t_e = pf(f"{prefixo}_mu_t", 1e-3)
        if max(mu_s_e, mu_t_e) > 1e-3:
            U_tip, tipo = 400, "líquido–líquido viscoso"
        else:
            U_tip, tipo = 900, "líquido–líquido pouco viscoso"

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
            f"✅ **Geometria estimada com sucesso!**\n\n"
            f"Q = {Q/1000:.2f} kW · LMTD = {lmtd_v:.2f} °C · {tipo}\n\n"
            f"U típico = {U_tip} W/m²·K → A_alvo = {A_alvo:.2f} m²\n\n"
            f"• d_o = {do:.5f} m\n"
            f"• Lta = {Lta} m\n"
            f"• Nt = {Nt} tubos\n"
            f"• Ltp = {Ltp:.5f} m\n"
            f"• Ds = {Ds:.4f} m\n"
            f"• Lbc = {Lbc:.3f} m")
        st.rerun()
    except ValueError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:
        st.error(f"Erro: {e}")

# ═════════════════════════════════════════════════════════════════
#  EXECUTAR CÁLCULO
# ═════════════════════════════════════════════════════════════════
def _executar_calculo(prefixo, metodo):
    try:
        Thi = pf(f"{prefixo}_Thi"); Tci = pf(f"{prefixo}_Tci")
        Tsaida = pf(f"{prefixo}_Tsaida")
        obj_raw = _V(f"{prefixo}_obj", "Th,o")
        obj = "Th,o" if "Th,o" in str(obj_raw)[:6] else "Tc,o"
        rho_s = pf(f"{prefixo}_rho_s"); mu_s = pf(f"{prefixo}_mu_s")
        cp_s = pf(f"{prefixo}_cp_s"); k_s = pf(f"{prefixo}_k_s"); ms = pf(f"{prefixo}_ms")
        rho_t = pf(f"{prefixo}_rho_t"); mu_t = pf(f"{prefixo}_mu_t")
        cp_t = pf(f"{prefixo}_cp_t"); k_t = pf(f"{prefixo}_k_t"); mt = pf(f"{prefixo}_mt")
        d = pf(f"{prefixo}_d"); e_p = pf(f"{prefixo}_e_parede"); di = d - 2*e_p
        Lta = pf(f"{prefixo}_Lta"); Ltp = pf(f"{prefixo}_Ltp")
        Ds = pf(f"{prefixo}_Ds"); Lbc = pf(f"{prefixo}_Lbc"); Nt = pi(f"{prefixo}_Nt")
        theta = int(_V(f"{prefixo}_theta", 30)); Np = int(_V(f"{prefixo}_Np", 1))
        kpar = MATERIAIS.get(_V(f"{prefixo}_material", "Aço Carbono"), 50.0)

        lam = frac = 0.0; lado_fase = ""
        if st.session_state.get(f"{prefixo}_fase_on"):
            lam = pf(f"{prefixo}_lambda") * 1000.0
            frac = pf(f"{prefixo}_frac", 1.0)
            lado_fase = _V(f"{prefixo}_fase_lado", "")
        Q_lat_s = ms * lam * frac if "Casco" in lado_fase else 0
        Q_lat_t = mt * lam * frac if "Tubo" in lado_fase else 0

        Tho, Tco, Q_W = resolver_T(obj, Thi, Tci, Tsaida, ms, cp_s, mt, cp_t, Q_lat_s, Q_lat_t)
        dTlm = lmtd(Thi, Tho, Tci, Tco)
        F = fator_F(Thi, Tho, Tci, Tco, Np)
        Tbs = (Thi + Tho)/2; Tbt = (Tci + Tco)/2
        Rp = d*math.log(d/di)/(2*kpar) if di > 0 else 0

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

        # Guarda T_bulk para o botão de refino
        st.session_state[f"{prefixo}_Tbulk_s"] = Tbs
        st.session_state[f"{prefixo}_Tbulk_t"] = Tbt

        dPs_max = pf(f"{prefixo}_dPs_max", 70); dPt_max = pf(f"{prefixo}_dPt_max", 100)
        ok_ps = "✓ OK" if dPs_kPa <= dPs_max else "⚠️ EXCEDE"
        ok_pt = "✓ OK" if dPt_kPa <= dPt_max else "⚠️ EXCEDE"

        if ex < 0:      diag = "❌ ÁREA INSUFICIENTE"
        elif ex < 10:   diag = "⚠️ MARGEM ESTREITA (< 10%)"
        elif ex <= 25:  diag = "✅ PROJETO ADEQUADO (10–25%)"
        elif ex <= 35:  diag = "⚠️ LEVE SUPERDIMENSIONAMENTO (25–35%)"
        else:           diag = "❌ SUPERDIMENSIONAMENTO EXCESSIVO (> 35%)"

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

        # Memorial
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
  Ref: Kern(1950) · Kakaç&Liu(2002) · Thulukkanam(2013) · TEMA
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
#  EXECUTA AS ABAS
# ═════════════════════════════════════════════════════════════════
with tab_k:
    render_aba("k", "#00C2FF", "kern")

with tab_b:
    render_aba("b", "#FF6B35", "bd")

st.markdown("---")
st.caption("Kern(1950) · Bell&Mueller(2001) · Kakaç&Liu(2002) · Thulukkanam(2013) · TEMA")
