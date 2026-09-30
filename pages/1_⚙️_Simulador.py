"""
Simulador Casco-e-Tubo — versão Streamlit com etapas
Kern & Bell-Delaware | v5 | com Mudança de Fase, Fouling e CoolProp
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
#  CONFIGURAÇÃO DA PÁGINA
# ═════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Simulador — Casco-e-Tubo",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═════════════════════════════════════════════════════════════════
#  CSS
# ═════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.block-container{padding-top:1.2rem;padding-bottom:1rem}

.card-info{
    background:#1a2332;border-left:4px solid #4a9eff;border-radius:6px;
    padding:12px 16px;margin:8px 0;font-size:13px;line-height:1.6;color:#DFF0FF}
.card-warn{
    background:#2d2010;border-left:4px solid #ffaa00;border-radius:6px;
    padding:12px 16px;margin:8px 0;font-size:13px;line-height:1.6;color:#DFF0FF}
.card-ok{
    background:#0d2a1a;border-left:4px solid #28a745;border-radius:6px;
    padding:12px 16px;margin:8px 0;font-size:13px;line-height:1.6;color:#DFF0FF}
.card-erro{
    background:#2d1010;border-left:4px solid #FF4D6D;border-radius:6px;
    padding:12px 16px;margin:8px 0;font-size:13px;line-height:1.6;color:#DFF0FF}

.result-box{
    background:#0e1117;border:1px solid #21262d;border-radius:8px;
    padding:16px;font-family:'Courier New',monospace;font-size:12px;
    white-space:pre-wrap;line-height:1.55;color:#58d68d;overflow-x:auto}

.nesta-etapa{
    background:#0e1117;border:1px solid #21262d;border-radius:8px;
    padding:16px;font-family:'Courier New',monospace;font-size:12px;
    white-space:pre-wrap;line-height:1.55;color:#c084fc;overflow-x:auto}

.stage-box{
    background:#172435;border:1px solid #00C2FF;border-radius:8px;
    padding:12px 16px;margin:8px 0;color:#DFF0FF;font-family:'Courier New',monospace;font-size:13px}

h1,h2,h3{color:#DFF0FF!important}
.stTabs [data-baseweb="tab"]{background-color:#172435;border-radius:4px}
.stTabs [aria-selected="true"]{background-color:#00C2FF!important;color:#0B1520!important}
input[type=text]{font-size:14px!important}
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
        "fonte": "Incropera et al. (2007), Tabela A.6",
    },
    "Ar (1 atm)": {
        "rho": lambda T: 353.05 / (T + 273.15),
        "mu":  lambda T: 1.716e-5 * ((T+273.15)/273.15)**1.5 * (273.15+110.4)/((T+273.15)+110.4),
        "cp":  lambda T: 1006.0 + 0.0448*T + 1.6e-4*T**2,
        "k":   lambda T: 0.0241 + 7.5e-5*T - 1.0e-8*T**2,
        "faixa": (-20, 400),
        "fonte": "Incropera et al. (2007), Tabela A.4",
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
    "R22 (legado)":"R22","R11 (legado, banido)":"R11","R12 (legado, banido)":"R12",
    "R123 (legado)":"R123",
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
#  HELPERS
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
        if Q<=0: raise ValueError("Q≤0: Th,o deve ser menor que Th,i")
        Tco=Tci+(Q-Q_lat_t)/(mt*cpt)
    else:
        Tco=Tval; Q=mt*cpt*(Tco-Tci)+Q_lat_t
        if Q<=0: raise ValueError("Q≤0: Tc,o deve ser maior que Tc,i")
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

# ═════════════════════════════════════════════════════════════════
#  PROPRIEDADES DE FLUIDO (CoolProp + manual)
# ═════════════════════════════════════════════════════════════════
def propriedades_fluido(nome, T_C, P_Pa=101325.0):
    if nome in FLUIDOS_DB:
        f = FLUIDOS_DB[nome]
        Tmin, Tmax = f["faixa"]
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
            raise RuntimeError(f"CoolProp falhou em {nome} a {T_C:.1f}°C, {P_Pa/1000:.1f}kPa: {str(e)[:150]}")
        try: fase_b = _CP.PhaseSI("T",T_K,"P",P_Pa,fid)
        except: fase_b = "unknown"
        fase_pt = {"liquid":"líquido","gas":"gás","twophase":"bifásico",
                   "supercritical":"supercrítico","supercritical_liquid":"supercrítico (líq.)",
                   "supercritical_gas":"supercrítico (gás)","unknown":"indefinida"}.get(fase_b,fase_b)
        fora = not (Tmin_K <= T_K <= Tmax_K)
        return {"rho":rho,"mu":mu,"cp":cp,"k":k,"fora_faixa":fora,
                "faixa":(Tmin_K-273.15,Tmax_K-273.15),"fase":fase_pt,
                "fonte":f"CoolProp {COOLPROP_VERSAO or ''} — a {P_Pa/1000:.1f} kPa"}
    raise KeyError(nome)

# ═════════════════════════════════════════════════════════════════
#  TEXTOS "NESTA ETAPA" (por página)
# ═════════════════════════════════════════════════════════════════
def explic_etapa(idx, metodo="kern"):
    textos = [
    # ── Página 1: Temperaturas ──
"""┌─ 🌡️  TEMPERATURAS E OBJETIVO ────────────────────────┐

FÓRMULAS DESTA ETAPA
─────────────────────
  Balanço de energia (1ª Lei):
    Q = ṁ · cp · ΔT        (para cada lado)
    Q_quente = Q_frio        (o que falta é calculado daqui)

  Diferença de temperatura média (LMTD):
    LMTD = (ΔT1 − ΔT2) / ln(ΔT1/ΔT2)
    ΔT1 = Th,i − Tc,o     ΔT2 = Th,o − Tc,i

IMPACTO NO PROJETO
───────────────────
  • Essas temperaturas definem o Q TOTAL do trocador.
  • Quanto MENOR o ΔT entre os fluidos, MENOR a força
    motriz térmica → para o mesmo Q, mais área de troca.
  • Se a T de saída pedida violar a 2ª Lei, o programa
    avisa antes de você preencher o resto.

GLOSSÁRIO
─────────
  Th,i / Th,o  T entrada / saída do fluido QUENTE (°C)
  Tc,i / Tc,o  T entrada / saída do fluido FRIO (°C)
  Q            Taxa de calor trocado (W)
  ṁ            Vazão mássica (kg/s)
  cp           Calor específico (J/kg·K)
""",
    # ── Página 2: Fluidos ──
"""┌─ 🧪  FLUIDOS E VAZÕES ────────────────────────────────┐

FÓRMULAS DESTA ETAPA
─────────────────────
  Número de Reynolds (regime de escoamento):
    Re = D · G / μ        (G = velocidade mássica = ṁ/A)

  Número de Prandtl (relação difusão qtd.mov./calor):
    Pr = μ · cp / k

  Essas propriedades entram nas correlações de convecção:
    hs = (0,36·k/Dhs) · Re^0,55 · Pr^(1/3)   [casco, Kern]
    Nu = f(Re, Pr)  →  h = Nu·k/di            [tubos]

  Correção de viscosidade na parede:
    φ = (μ_bulk / μ_parede)^0,14
    h_real = h_ideal × φ

IMPACTO NO PROJETO
───────────────────
  • Fluidos MAIS VISCOSOS → Re menor → h menor → mais área.
  • Use o BANCO DE DADOS DE FLUIDOS para preencher os campos.
    Escolha "Água (líquida)" ou "Ar (1 atm)" para teste rápido.
  • Para CoolProp, informe também a PRESSÃO de referência.
  • Após calcular, use ↺ "Usar T média" para refinar.

GLOSSÁRIO
─────────
  ρ (rho)   Massa específica (kg/m³)
  μ (mu)    Viscosidade dinâmica bulk (Pa·s)
  cp        Calor específico (J/kg·K)
  k         Condutividade térmica (W/m·K)
  ṁₛ / ṁₜ   Vazão mássica casco / tubo (kg/s)
""",
    # ── Página 3: Geometria ──
"""┌─ 📐  GEOMETRIA DO TROCADOR ───────────────────────────┐

FÓRMULAS DESTA ETAPA
─────────────────────
  Diâmetro interno do tubo:
    di = d_o − 2·e

  Nº de chicanas:
    Nb = ⌊Lta / Lbc⌋ − 1

  Dependem do arranjo θ:
    Dhs = f(Ltp, d, θ)      Atc = Ds·C·Lbc/Ltp

  Fator de correção da LMTD (multipasse):
    F = f(P, R, Nₚ)   [Bowman-Mueller-Nagle]
    Nₚ = 1 → F = 1,0

IMPACTO NO PROJETO
───────────────────
  • A geometria define a ÁREA DISPONÍVEL:
    A_inst = Nt · π · d_o · Lta
  • Use 🔮 "Estimar geometria" para derivar tudo a partir de Q.
  • Chicanas mais próximas (Lbc↓) → mais h, mas mais ΔP.
  • θ = 30° (triangular) empacota mais tubos que θ = 90°.

TABELA DE REFERÊNCIA — Nₜ × Dₛ (aprox.)
    Dₛ (m)   Dₛ (pol.)   Nₜ aprox.
    0,203       8"          ~37
    0,254      10"          ~62
    0,305      12"          ~92
    0,387      15¼"        ~151
    0,489      19¼"        ~277

GLOSSÁRIO
─────────
  d_o / di   Diâmetro externo / interno (m)
  e          Espessura da parede (m)
  Lta        Comprimento do tubo (m)
  Ltp        Passo entre tubos (m)
  Ds         Diâmetro do casco (m)
  Lbc        Espaçamento entre chicanas (m)
  θ          Ângulo do arranjo (°)
  Nₚ         Nº de passes nos tubos
""",
    # ── Página 4: Cálculo ──
"""┌─ ⚙️  LIMITES, FASE, FOULING E CÁLCULO ────────────────┐

FÓRMULAS DESTA ETAPA
─────────────────────
  Queda de pressão (Kern):
    ΔPs = fs·Gs²·(Nb+1)·Ds / (2·ρₛ·Dhs·φₛ)
    ΔPt = ft·(Lta/di)·(Gt²/2ρₜ)·Np + retornos

  Fouling (incrustação):
    R_foul = Rf,ext + (d/di)·Rf,int

  Coeficiente global e área:
    U = 1 / (R_ext + R_cond + R_int + R_foul)
    A = Q / (U · LMTD · F)

IMPACTO NO PROJETO
───────────────────
  • ΔP calculado > limite → projeto REPROVADO.
  • Mudança de fase: Q_total = Q_sens + ṁ·λ·x.
  • Fouling MAIOR → U MENOR → área MAIOR.
  • Excesso de área ideal: 10–25 %.

GLOSSÁRIO
─────────
  ΔPs / ΔPt   Queda de pressão casco / tubos
  Rf          Resistência de fouling (m²·K/W)
  U           Coef. global (W/m²·K)
  A           Área de troca (m²)
  λ           Calor latente (kJ/kg)
""",
    ]
    idx = max(0, min(idx, len(textos)-1))
    return textos[idx]

# ═════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ═════════════════════════════════════════════════════════════════
def _init_state(prefixo):
    for k in [
        f"{prefixo}_pagina",
        f"{prefixo}_resultado",
        f"{prefixo}_memorial",
    ]:
        if k not in st.session_state:
            st.session_state[k] = 0 if k.endswith("pagina") else None

# ═════════════════════════════════════════════════════════════════
#  CABEÇALHO
# ═════════════════════════════════════════════════════════════════
st.title("⚙️ Simulador Casco-e-Tubo")
st.caption("**Kern** & **Bell-Delaware** | v5 | com Mudança de Fase, Fouling e CoolProp")

# ═════════════════════════════════════════════════════════════════
#  ABAS DOS MÉTODOS
# ═════════════════════════════════════════════════════════════════
tab_k, tab_b = st.tabs(["🔵 KERN", "🟠 BELL-DELAWARE"])

# ═════════════════════════════════════════════════════════════════
#  FUNÇÃO GENÉRICA: RENDERIZA UMA ABA
# ═════════════════════════════════════════════════════════════════
def render_aba(prefixo, cor, metodo):
    _init_state(prefixo)
    pag = st.session_state[f"{prefixo}_pagina"]
    titulos = ["🌡️ Temperaturas e Objetivo",
               "🧪 Fluidos e Vazões",
               "📐 Geometria do Trocador",
               "⚙️ Limites, Fase, Fouling e Cálculo"]

    col_l, col_r = st.columns([1, 1], gap="large")

    # ═════════════════════════════════════════════════════════════
    #  COLUNA ESQUERDA — PÁGINAS
    # ═════════════════════════════════════════════════════════════
    with col_l:
        # Navegador
        st.markdown(
            f"<div class='stage-box'>"
            f"🎓 <b>MODO PASSO A PASSO</b><br>"
            f"Página {pag+1} de 4 — {titulos[pag]}"
            f"</div>", unsafe_allow_html=True)
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("◀ Anterior", disabled=(pag==0), key=f"{prefixo}_ant",
                         use_container_width=True):
                st.session_state[f"{prefixo}_pagina"] = pag - 1
                st.rerun()
        with nav3:
            if st.button("Próximo ▶", disabled=(pag==3), key=f"{prefixo}_prox",
                         use_container_width=True):
                # valida antes de avançar
                ok, faltando = validar_pagina(prefixo, pag)
                if ok:
                    st.session_state[f"{prefixo}_pagina"] = pag + 1
                    st.rerun()
                else:
                    msg = "**Preencha os campos desta etapa antes de avançar:**\n\n"
                    for c in faltando: msg += f"- {c}\n"
                    st.warning(msg)

        st.markdown("---")

        # ─── PÁGINA 1: Temperaturas ──────────────────────────────
        if pag == 0:
            st.markdown(
                "<div class='card-info'>💡 Defina as temperaturas de entrada dos "
                "dois fluidos e escolha qual temperatura de saída o programa "
                "deve calcular. Isso é o balanço de energia: "
                "<b>Q = ṁ · cp · ΔT</b> (1ª Lei da Termodinâmica).</div>",
                unsafe_allow_html=True)

            st.subheader("🌡️ Temperaturas do Processo")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Th,i — quente entrada (°C) ✱",
                              key=f"{prefixo}_Thi", placeholder="ex: 100")
            with c2:
                st.text_input("Tc,i — frio entrada (°C) ✱",
                              key=f"{prefixo}_Tci", placeholder="ex: 20")

            st.markdown("**Objetivo:** qual temperatura de saída calcular?")
            st.radio("Objetivo",
                     ["Th,o → calcula Tc,o", "Tc,o → calcula Th,o"],
                     key=f"{prefixo}_obj", horizontal=True)

            if st.session_state[f"{prefixo}_obj"] == "Th,o → calcula Tc,o":
                st.text_input("Th,o — quente saída (°C) ✱",
                              key=f"{prefixo}_Tsaida", placeholder="ex: 60")
            else:
                st.text_input("Tc,o — frio saída (°C) ✱",
                              key=f"{prefixo}_Tsaida", placeholder="ex: 45")

            st.markdown(
                "<div class='card-warn'>➗ <b>Como a temperatura que falta "
                "é calculada:</b><br>"
                "1) Q do lado conhecido: Q = ṁ·cp·ΔT<br>"
                "2) Iguala Q_quente = Q_frio<br>"
                "3) Isola a T desconhecida: T = T_ent ± Q/(ṁ·cp)</div>",
                unsafe_allow_html=True)

        # ─── PÁGINA 2: Fluidos ───────────────────────────────────
        elif pag == 1:
            st.markdown(
                "<div class='card-info'>💡 Cada fluido precisa de 4 propriedades "
                "(ρ, μ, cp, k) e da vazão mássica. Use o banco de fluidos para "
                "preencher automaticamente ou digite manualmente.</div>",
                unsafe_allow_html=True)

            if COOLPROP_DISPONIVEL:
                st.markdown(
                    f"<div class='card-ok'>🧬 CoolProp {COOLPROP_VERSAO} instalado — "
                    f"{len(FLUIDOS_COOLPROP)} fluidos adicionais disponíveis</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    "<div class='card-warn'>ℹ CoolProp não instalado — "
                    "só Água e Ar disponíveis. Instale com: pip install CoolProp</div>",
                    unsafe_allow_html=True)

            # Widget de banco de fluidos
            _widget_banco_fluidos(prefixo, cor)

            st.markdown("---")
            # Campos manuais — SEMPRE visíveis (podem ser preenchidos pelo banco)
            st.subheader("🔵 Fluido — Casco (quente)")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("ρₛ — massa específica (kg/m³)",
                              key=f"{prefixo}_rho_s", placeholder="ex: 983")
                st.text_input("cp,s — calor específico (J/kg·K)",
                              key=f"{prefixo}_cp_s", placeholder="ex: 4190")
            with c2:
                st.text_input("μₛ — viscosidade (Pa·s)",
                              key=f"{prefixo}_mu_s", placeholder="ex: 4.6e-4")
                st.text_input("kₛ — condutividade (W/m·K)",
                              key=f"{prefixo}_k_s", placeholder="ex: 0.659")
            st.text_input("ṁₛ — vazão mássica (kg/s)",
                          key=f"{prefixo}_ms", placeholder="ex: 4.3")

            st.markdown("---")
            st.subheader("🔵 Fluido — Tubos (frio)")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("ρₜ — massa específica (kg/m³)",
                              key=f"{prefixo}_rho_t", placeholder="ex: 998")
                st.text_input("cp,t — calor específico (J/kg·K)",
                              key=f"{prefixo}_cp_t", placeholder="ex: 4182")
            with c2:
                st.text_input("μₜ — viscosidade (Pa·s)",
                              key=f"{prefixo}_mu_t", placeholder="ex: 8.9e-4")
                st.text_input("kₜ — condutividade (W/m·K)",
                              key=f"{prefixo}_k_t", placeholder="ex: 0.600")
            st.text_input("ṁₜ — vazão mássica (kg/s)",
                          key=f"{prefixo}_mt", placeholder="ex: 5.7")

            # Dica
            st.markdown(
                "<div class='card-info'>🧱 <b>Temperatura da Parede (automático):</b> "
                "o programa calcula iterativamente T_w e μ_w, corrigindo h por "
                "φ = (μ_bulk/μ_w)^0.14.</div>",
                unsafe_allow_html=True)

        # ─── PÁGINA 3: Geometria ─────────────────────────────────
        elif pag == 2:
            st.markdown(
                "<div class='card-info'>💡 A geometria define a área de troca "
                "térmica disponível e como os fluidos escoam dentro do trocador."
                "</div>", unsafe_allow_html=True)

            # Card "não sabe por onde começar"
            st.markdown(
                "<div class='card-ok'>🔰 <b>NÃO SABE POR ONDE COMEÇAR?</b><br>"
                "1) d_o: 3/4\" (0,01905 m) ou 1\" (0,02540 m)<br>"
                "2) L_ta: 1,83 / 2,44 / 3,66 / 4,88 / 6,10 m<br>"
                "3) L_tp: 1,25 × d_o (mínimo TEMA)<br>"
                "4) D_s: use a calculadora Db → Ds abaixo<br>"
                "5) Lbc: 0,2–1,0 × D_s (comece com 0,3 × D_s)</div>",
                unsafe_allow_html=True)

            if st.button("🔮 Estimar geometria a partir dos dados térmicos",
                         key=f"{prefixo}_estim", use_container_width=True):
                _estimar_geometria(prefixo, metodo)

            st.markdown("---")

            st.subheader("📐 Tubo")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("d_o — diâm. externo (m)",
                              key=f"{prefixo}_d", placeholder="ex: 0.01905")
                st.text_input("e — espessura (m)",
                              key=f"{prefixo}_e_parede", placeholder="ex: 0.00165")
            with c2:
                # di calculado
                try:
                    d_v = float(str(st.session_state.get(f"{prefixo}_d","0")).replace(",",".") or 0)
                    e_v = float(str(st.session_state.get(f"{prefixo}_e_parede","0")).replace(",",".") or 0)
                    di_v = d_v - 2*e_v
                    st.text_input("di — diâm. interno (m) [calculado]",
                                  value=f"{di_v:.5f}", disabled=True)
                except:
                    st.text_input("di — diâm. interno (m) [calculado]",
                                  value="—", disabled=True)
                st.selectbox("Material:", list(MATERIAIS.keys()),
                             key=f"{prefixo}_material")

            st.markdown("---")
            st.subheader("🏗️ Casco e Chicanas")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Dₛ — diâm. casco (m)",
                              key=f"{prefixo}_Ds", placeholder="ex: 0.387")
                st.text_input("Lₜₐ — comp. tubo (m)",
                              key=f"{prefixo}_Lta", placeholder="ex: 4.877")
                st.text_input("Lₜₚ — passo tubos (m)",
                              key=f"{prefixo}_Ltp", placeholder="ex: 0.025")
            with c2:
                st.text_input("Lbc — espaç. chicanas (m)",
                              key=f"{prefixo}_Lbc", placeholder="ex: 0.2")
                st.text_input("Nₜ — nº de tubos",
                              key=f"{prefixo}_Nt", placeholder="ex: 158")

                if metodo == "bd":
                    st.text_input("Bc — corte chicana (%)",
                                  key=f"{prefixo}_Bc", placeholder="ex: 25")
                    st.text_input("Lbi — chicana-entrada (m)",
                                  key=f"{prefixo}_Lbi", placeholder="ex: 0.2")
                    st.text_input("Lbo — chicana-saída (m)",
                                  key=f"{prefixo}_Lbo", placeholder="ex: 0.2")
                    st.text_input("Nss — pares de tiras",
                                  key=f"{prefixo}_Nss", placeholder="ex: 2")

            # Nb calculado (info)
            try:
                Lta_v = float(str(st.session_state.get(f"{prefixo}_Lta","0")).replace(",",".") or 0)
                Lbc_v = float(str(st.session_state.get(f"{prefixo}_Lbc","0")).replace(",",".") or 0)
                Nb_calc = max(1, int(Lta_v/Lbc_v)-1) if Lbc_v > 0 else 0
                st.info(f"Nb calculado = **{Nb_calc}** chicanas")
            except:
                pass

            c1, c2 = st.columns(2)
            with c1:
                st.selectbox("Ângulo θ:", [30,45,60,90] if metodo=="kern" else [30,45,90],
                             key=f"{prefixo}_theta")
            with c2:
                st.selectbox("Passes Nₚ:", [1,2,4,6,8], key=f"{prefixo}_Np")

            # Calculadora Db → Ds
            with st.expander("📐 Calculadora Db → Ds (Coulson & Richardson)"):
                if st.button("Calcular Db e Ds", key=f"{prefixo}_btn_db"):
                    try:
                        Nt_v = int(float(st.session_state.get(f"{prefixo}_Nt","0") or 0))
                        do_v = float(str(st.session_state.get(f"{prefixo}_d","0")).replace(",",".") or 0)
                        Np_v = int(st.session_state.get(f"{prefixo}_Np", 1))
                        th_v = int(st.session_state.get(f"{prefixo}_theta", 30))
                        r = bundle_diameter(Nt_v, do_v, Np_v, th_v)
                        st.success(f"**Db = {r['Db']*1000:.1f} mm**  |  **Ds = {r['Ds']*1000:.1f} mm**")
                        st.caption(f"K₁={r['K1']}  n={r['n1']}  |  Ltp sugerido = {r['Ltp_sug']*1000:.2f} mm")
                        st.session_state[f"{prefixo}_Db_est"] = r['Db']
                        st.session_state[f"{prefixo}_Ds_est"] = r['Ds']
                        st.session_state[f"{prefixo}_Ltp_sug"] = r['Ltp_sug']
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if f"{prefixo}_Ds_est" in st.session_state:
                    if st.button("↑ Usar Ds e Ltp estimados", key=f"{prefixo}_usar_db"):
                        st.session_state[f"{prefixo}_Ds"] = f"{st.session_state[f'{prefixo}_Ds_est']:.4f}"
                        st.session_state[f"{prefixo}_Ltp"] = f"{st.session_state[f'{prefixo}_Ltp_sug']:.5f}"
                        st.rerun()

            if metodo == "bd":
                with st.expander("📏 Folgas TEMA"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.text_input("Lbb (mm)", key=f"{prefixo}_Lbb", placeholder="ex: 11.0")
                        st.text_input("Ltb (mm)", key=f"{prefixo}_Ltb", placeholder="ex: 0.8")
                    with c2:
                        if st.button("↻ Recalcular folgas TEMA", key=f"{prefixo}_tema"):
                            try:
                                Ds_mm = float(str(st.session_state.get(f"{prefixo}_Ds","0")).replace(",",".") or 0)*1000
                                f = folgas_tema(Ds_mm)
                                st.session_state[f"{prefixo}_Lbb"] = f"{f['Lbb_mm']:.2f}"
                                st.session_state[f"{prefixo}_Ltb"] = f"{f['Ltb_mm']:.2f}"
                                st.rerun()
                            except: pass

        # ─── PÁGINA 4: Cálculo ───────────────────────────────────
        elif pag == 3:
            st.markdown(
                "<div class='card-info'>💡 Última etapa: limites de ΔP, mudança "
                "de fase (se houver) e fouling. Depois clique em "
                "<b>▶ CALCULAR</b>.</div>", unsafe_allow_html=True)

            st.subheader("⚡ Limites de ΔP")
            preset = st.selectbox("Preset de serviço:", list(LIMITES_DP.keys()),
                                  key=f"{prefixo}_preset_dp")
            ds0, dt0, ref0 = LIMITES_DP[preset]
            if ds0 > 0:
                st.caption(f"Ref: {ref0} | ΔPs={ds0} kPa  ΔPt={dt0} kPa")
                st.session_state[f"{prefixo}_dPs_max"] = str(ds0)
                st.session_state[f"{prefixo}_dPt_max"] = str(dt0)
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("ΔP máx. casco (kPa)", key=f"{prefixo}_dPs_max", placeholder="ex: 70")
            with c2:
                st.text_input("ΔP máx. tubos (kPa)", key=f"{prefixo}_dPt_max", placeholder="ex: 100")

            st.markdown("---")
            st.subheader("⇌ Mudança de Fase")
            ativa = st.checkbox("Há mudança de fase?", key=f"{prefixo}_fase_on")
            if ativa:
                st.radio("Tipo:", ["Condensação","Vaporização"],
                         key=f"{prefixo}_fase_tipo", horizontal=True)
                st.radio("Lado afetado:", ["Casco (quente)","Tubos (frio)"],
                         key=f"{prefixo}_fase_lado", horizontal=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("λ — calor latente (kJ/kg)",
                                  key=f"{prefixo}_lambda", placeholder="ex: 2257")
                with c2:
                    st.text_input("x — fração [0-1]",
                                  key=f"{prefixo}_frac", placeholder="ex: 1.0")

            st.markdown("---")
            st.subheader("🔧 Fouling")
            fp = st.selectbox("Preset TEMA:", list(FOULING_PRESETS.keys()),
                              key=f"{prefixo}_fp")
            fe0, fi0 = FOULING_PRESETS[fp]
            if fp != "Personalizado":
                st.session_state[f"{prefixo}_Rfe"] = str(fe0)
                st.session_state[f"{prefixo}_Rfi"] = str(fi0)
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Rf ext (m²·K/W)", key=f"{prefixo}_Rfe", placeholder="ex: 0.0002")
            with c2:
                st.text_input("Rf int (m²·K/W)", key=f"{prefixo}_Rfi", placeholder="ex: 0.0002")

            st.markdown("---")
            if st.button(f"▶ CALCULAR — {metodo.upper()}", key=f"{prefixo}_calc",
                         use_container_width=True, type="primary"):
                _executar_calculo(prefixo, metodo)

    # ═════════════════════════════════════════════════════════════
    #  COLUNA DIREITA — RESULTADOS EM 3 ABAS
    # ═════════════════════════════════════════════════════════════
    with col_r:
        st.subheader(f"📊 Resultados — {metodo.upper()}")
        t_resumo, t_etapa, t_memo = st.tabs(["📊 Resumo", "🧭 Nesta Etapa", "📘 Memorial"])

        with t_resumo:
            resultado = st.session_state.get(f"{prefixo}_resultado")
            if resultado:
                st.markdown(f"<div class='result-box'>{resultado}</div>",
                            unsafe_allow_html=True)
            else:
                st.info("Preencha os campos e clique em ▶ CALCULAR.\n\n"
                        "**Novidades v5:**\n"
                        "- Etapas passo a passo com validação\n"
                        "- Aba 🧭 Nesta Etapa com fórmulas\n"
                        "- Aba 📘 Memorial de Cálculo\n"
                        "- CoolProp integrado (42 fluidos extras)")

        with t_etapa:
            texto = explic_etapa(pag, metodo)
            st.markdown(f"<div class='nesta-etapa'>{texto}</div>",
                        unsafe_allow_html=True)

        with t_memo:
            memo = st.session_state.get(f"{prefixo}_memorial")
            if memo:
                st.markdown(f"<div class='result-box'>{memo}</div>",
                            unsafe_allow_html=True)
            else:
                st.info("O memorial de cálculo passo a passo aparece aqui "
                        "após você clicar em ▶ CALCULAR.")

# ═════════════════════════════════════════════════════════════════
#  VALIDAÇÃO DE PÁGINA
# ═════════════════════════════════════════════════════════════════
def validar_pagina(prefixo, pag):
    """Retorna (ok, lista_de_faltantes)."""
    obrig = {
        0: [f"{prefixo}_Thi", f"{prefixo}_Tci", f"{prefixo}_Tsaida"],
        1: [f"{prefixo}_rho_s", f"{prefixo}_mu_s", f"{prefixo}_cp_s", f"{prefixo}_k_s",
            f"{prefixo}_ms",
            f"{prefixo}_rho_t", f"{prefixo}_mu_t", f"{prefixo}_cp_t", f"{prefixo}_k_t",
            f"{prefixo}_mt"],
        2: [f"{prefixo}_d", f"{prefixo}_e_parede", f"{prefixo}_Ds",
            f"{prefixo}_Lta", f"{prefixo}_Ltp", f"{prefixo}_Lbc", f"{prefixo}_Nt"],
        3: [],
    }
    nomes_bonitos = {
        f"{prefixo}_Thi": "Th,i — T entrada quente (°C)",
        f"{prefixo}_Tci": "Tc,i — T entrada frio (°C)",
        f"{prefixo}_Tsaida": "T de saída (°C)",
        f"{prefixo}_rho_s": "ρₛ — massa específica casco",
        f"{prefixo}_mu_s": "μₛ — viscosidade casco",
        f"{prefixo}_cp_s": "cp,s — calor específico casco",
        f"{prefixo}_k_s": "kₛ — condutividade casco",
        f"{prefixo}_ms": "ṁₛ — vazão mássica casco",
        f"{prefixo}_rho_t": "ρₜ — massa específica tubos",
        f"{prefixo}_mu_t": "μₜ — viscosidade tubos",
        f"{prefixo}_cp_t": "cp,t — calor específico tubos",
        f"{prefixo}_k_t": "kₜ — condutividade tubos",
        f"{prefixo}_mt": "ṁₜ — vazão mássica tubos",
        f"{prefixo}_d": "d_o — diâmetro externo do tubo",
        f"{prefixo}_e_parede": "e — espessura da parede",
        f"{prefixo}_Ds": "Dₛ — diâmetro do casco",
        f"{prefixo}_Lta": "Lₜₐ — comprimento do tubo",
        f"{prefixo}_Ltp": "Lₜₚ — passo dos tubos",
        f"{prefixo}_Lbc": "Lbc — espaçamento entre chicanas",
        f"{prefixo}_Nt": "Nₜ — número de tubos",
    }
    faltando = []
    for k in obrig.get(pag, []):
        v = st.session_state.get(k, "")
        if not str(v).strip():
            faltando.append(nomes_bonitos.get(k, k))
    return (len(faltando) == 0, faltando)

# ═════════════════════════════════════════════════════════════════
#  PARSER
# ═════════════════════════════════════════════════════════════════
def pf(key, default=0.0):
    try:
        return float(str(st.session_state.get(key, "")).replace(",", ".").strip())
    except:
        return default

def pi(key, default=0):
    try:
        return int(float(str(st.session_state.get(key, "")).replace(",", ".").strip()))
    except:
        return default

# ═════════════════════════════════════════════════════════════════
#  WIDGET BANCO DE FLUIDOS
# ═════════════════════════════════════════════════════════════════
def _widget_banco_fluidos(prefixo, cor):
    with st.expander("🧪 Banco de Dados de Fluidos", expanded=True):
        nomes = list(FLUIDOS_DB.keys())
        if COOLPROP_DISPONIVEL:
            nomes += sorted(FLUIDOS_COOLPROP.keys())

        fluido = st.selectbox("Fluido:", nomes, key=f"{prefixo}_fluido")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("T referência (°C)", key=f"{prefixo}_T_ref", placeholder="ex: 80")
        with c2:
            st.text_input("P referência (kPa)", key=f"{prefixo}_P_ref",
                          value="101.325")
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_sugerir = st.button("💡 Sugerir P", key=f"{prefixo}_sugerir_p")

        if btn_sugerir:
            _sugerir_pressao(prefixo, fluido)

        if st.button(f"🔎 Buscar propriedades", key=f"{prefixo}_buscar",
                     use_container_width=True):
            _buscar_fluido(prefixo, fluido, cor)

        # Refino iterativo
        st.caption("↺ Após CALCULAR, use a T média para refinar")
        if st.button("↺ Usar T média (bulk) calculada", key=f"{prefixo}_bulk"):
            _usar_bulk(prefixo, fluido, cor)

def _buscar_fluido(prefixo, nome, cor):
    try:
        T = pf(f"{prefixo}_T_ref")
        P_kPa = pf(f"{prefixo}_P_ref", 101.325)
        p = propriedades_fluido(nome, T, P_Pa=P_kPa*1000.0)
        st.session_state[f"{prefixo}_rho_s"] = f"{p['rho']:.4f}"
        st.session_state[f"{prefixo}_mu_s"]  = f"{p['mu']:.6e}"
        st.session_state[f"{prefixo}_cp_s"]  = f"{p['cp']:.2f}"
        st.session_state[f"{prefixo}_k_s"]   = f"{p['k']:.5f}"
        aviso = "⚠ T fora da faixa!" if p["fora_faixa"] else "✔ dentro da faixa"
        fase_txt = f" | fase: {p['fase']}" if p.get("fase") else ""
        st.success(f"Preenchido: ρ={p['rho']:.2f}  μ={p['mu']:.3e}  cp={p['cp']:.1f}  k={p['k']:.4f}")
        st.caption(f"Faixa: {p['faixa'][0]:.1f} a {p['faixa'][1]:.1f} °C {aviso}{fase_txt} | {p['fonte']}")
        st.rerun()
    except Exception as e:
        st.error(f"Erro: {e}")

def _sugerir_pressao(prefixo, nome):
    if nome not in FLUIDOS_COOLPROP or not COOLPROP_DISPONIVEL:
        st.info("Sugestão de P só funciona para fluidos do CoolProp.")
        return
    try:
        T = pf(f"{prefixo}_T_ref")
        fid = FLUIDOS_COOLPROP[nome]
        T_K = T + 273.15
        T_sat_K = _CP.PropsSI("T","P",101325.0,"Q",0,fid)
        P_sat_Pa = _CP.PropsSI("P","T",T_K,"Q",0,fid)
        P_sat_kPa = P_sat_Pa/1000
        st.info(
            f"T_sat @ 1 atm = {T_sat_K-273.15:.1f} °C\n\n"
            f"P_sat em {T:.1f} °C = {P_sat_kPa:.2f} kPa\n\n"
            f"Líquido: P > {P_sat_kPa:.1f} kPa (sugestão {P_sat_kPa*1.2:.0f})\n"
            f"Vapor:   P < {P_sat_kPa:.1f} kPa (sugestão {P_sat_kPa*0.5:.0f})")
    except Exception as e:
        st.warning(f"Sem saturação nesta T: {str(e)[:100]}")

def _usar_bulk(prefixo, nome, cor):
    T_bulk = st.session_state.get(f"{prefixo}_T_bulk")
    if T_bulk is None:
        st.info("Faça um cálculo primeiro para obter a T média.")
        return
    st.session_state[f"{prefixo}_T_ref"] = f"{T_bulk:.2f}"
    _buscar_fluido(prefixo, nome, cor)

# ═════════════════════════════════════════════════════════════════
#  ESTIMAR GEOMETRIA
# ═════════════════════════════════════════════════════════════════
def _estimar_geometria(prefixo, metodo):
    try:
        Thi = pf(f"{prefixo}_Thi"); Tci = pf(f"{prefixo}_Tci")
        Tsaida = pf(f"{prefixo}_Tsaida")
        ms = pf(f"{prefixo}_ms"); cp_s = pf(f"{prefixo}_cp_s")
        mt = pf(f"{prefixo}_mt"); cp_t = pf(f"{prefixo}_cp_t")
        if st.session_state.get(f"{prefixo}_obj","").startswith("Th,o"):
            Tho, Tco, Q = resolver_T("Th,o", Thi, Tci, Tsaida, ms, cp_s, mt, cp_t)
        else:
            Tho, Tco, Q = resolver_T("Tc,o", Thi, Tci, Tsaida, ms, cp_s, mt, cp_t)
        lmtd_v = lmtd(Thi, Tho, Tci, Tco)
        # U típico pela viscosidade
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
        Np = pi(f"{prefixo}_Np", 1)
        theta = pi(f"{prefixo}_theta", 30)
        r = bundle_diameter(Nt, do, Np, theta)
        Ds = r["Ds"]; Lbc = 0.30 * Ds
        st.session_state[f"{prefixo}_d"] = f"{do:.5f}"
        st.session_state[f"{prefixo}_e_parede"] = "0.00165"
        st.session_state[f"{prefixo}_Lta"] = f"{Lta}"
        st.session_state[f"{prefixo}_Ltp"] = f"{Ltp:.5f}"
        st.session_state[f"{prefixo}_Ds"] = f"{Ds:.4f}"
        st.session_state[f"{prefixo}_Lbc"] = f"{Lbc:.3f}"
        st.session_state[f"{prefixo}_Nt"] = f"{Nt}"
        if metodo == "bd":
            st.session_state[f"{prefixo}_Bc"] = "25"
            st.session_state[f"{prefixo}_Lbi"] = f"{Lbc:.3f}"
            st.session_state[f"{prefixo}_Lbo"] = f"{Lbc:.3f}"
            st.session_state[f"{prefixo}_Nss"] = "2"
        st.success(
            f"**Geometria estimada:**\n\n"
            f"Q = {Q/1000:.2f} kW | LMTD = {lmtd_v:.2f} °C | {tipo}\n"
            f"U típico = {U_tip} W/m²·K → A_alvo = {A_alvo:.2f} m²\n"
            f"d_o = {do:.5f} m | Lta = {Lta} m | Nt = {Nt} | Ds = {Ds:.4f} m | Lbc = {Lbc:.3f} m")
        st.rerun()
    except Exception as e:
        st.error(f"Erro na estimativa: {e}")

# ═════════════════════════════════════════════════════════════════
#  EXECUTAR CÁLCULO
# ═════════════════════════════════════════════════════════════════
def _executar_calculo(prefixo, metodo):
    try:
        Thi = pf(f"{prefixo}_Thi"); Tci = pf(f"{prefixo}_Tci")
        Tsaida = pf(f"{prefixo}_Tsaida")
        obj = "Th,o" if st.session_state.get(f"{prefixo}_obj","").startswith("Th,o") else "Tc,o"
        rho_s = pf(f"{prefixo}_rho_s"); mu_s = pf(f"{prefixo}_mu_s")
        cp_s = pf(f"{prefixo}_cp_s"); k_s = pf(f"{prefixo}_k_s"); ms = pf(f"{prefixo}_ms")
        rho_t = pf(f"{prefixo}_rho_t"); mu_t = pf(f"{prefixo}_mu_t")
        cp_t = pf(f"{prefixo}_cp_t"); k_t = pf(f"{prefixo}_k_t"); mt = pf(f"{prefixo}_mt")
        d = pf(f"{prefixo}_d"); e_p = pf(f"{prefixo}_e_parede"); di = d - 2*e_p
        Lta = pf(f"{prefixo}_Lta"); Ltp = pf(f"{prefixo}_Ltp")
        Ds = pf(f"{prefixo}_Ds"); Lbc = pf(f"{prefixo}_Lbc")
        Nt = pi(f"{prefixo}_Nt")
        theta = pi(f"{prefixo}_theta", 30); Np = pi(f"{prefixo}_Np", 1)
        kpar = MATERIAIS.get(st.session_state.get(f"{prefixo}_material","Aço Carbono"), 50.0)

        # Calor latente
        lam = frac = 0.0; lado_fase = ""
        if st.session_state.get(f"{prefixo}_fase_on"):
            lam = pf(f"{prefixo}_lambda") * 1000.0
            frac = pf(f"{prefixo}_frac", 1.0)
            lado_fase = st.session_state.get(f"{prefixo}_fase_lado","")
        Q_lat_s = ms * lam * frac if "Casco" in lado_fase else 0
        Q_lat_t = mt * lam * frac if "Tubo" in lado_fase else 0

        Tho, Tco, Q_W = resolver_T(obj, Thi, Tci, Tsaida, ms, cp_s, mt, cp_t, Q_lat_s, Q_lat_t)
        dTlm = lmtd(Thi, Tho, Tci, Tco)
        F = fator_F(Thi, Tho, Tci, Tco, Np)
        Tbs = (Thi + Tho)/2; Tbt = (Tci + Tco)/2
        Rp = d*math.log(d/di)/(2*kpar) if di > 0 else 0

        Rfe = pf(f"{prefixo}_Rfe", 0.0002)
        Rfi = pf(f"{prefixo}_Rfi", 0.0002)

        # ─── Cálculo ───
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
            metodo_label = "KERN"
        else:
            Bc = pf(f"{prefixo}_Bc", 25); Lbi = pf(f"{prefixo}_Lbi", Lbc)
            Lbo = pf(f"{prefixo}_Lbo", Lbc); Nss = pf(f"{prefixo}_Nss", 2)
            Lbb_m = pf(f"{prefixo}_Lbb")/1000 if st.session_state.get(f"{prefixo}_Lbb") else None
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
            metodo_label = "BELL-DELAWARE"

        # Guarda T_bulk para o botão de refino
        st.session_state[f"{prefixo}_T_bulk"] = Tbs  # aproximação; ideal é separar por lado

        # ─── Resultado textual ───
        dPs_max = pf(f"{prefixo}_dPs_max", 70)
        dPt_max = pf(f"{prefixo}_dPt_max", 100)
        dPs_ok = "✓ OK" if dPs_kPa <= dPs_max else "⚠ EXCEDE"
        dPt_ok = "✓ OK" if dPt_kPa <= dPt_max else "⚠ EXCEDE"

        # Diagnóstico de área
        if ex < 0:
            diag = "❌ ÁREA INSUFICIENTE"
        elif ex < 10:
            diag = "⚠️ MARGEM ESTREITA (< 10%)"
        elif ex <= 25:
            diag = "✅ PROJETO ADEQUADO (10–25%)"
        elif ex <= 35:
            diag = "⚠️ LEVE SUPERDIMENSIONAMENTO (25–35%)"
        else:
            diag = "❌ SUPERDIMENSIONAMENTO EXCESSIVO (> 35%)"

        txt = f"""
╔══════════════════════════════════════════════╗
║   RESULTADO — {metodo_label:<26} ║
╚══════════════════════════════════════════════╝

─── TEMPERATURAS ──────────────────────────
  Quente : {Thi:.2f} → {Tho:.2f} °C
  Frio   : {Tci:.2f} → {Tco:.2f} °C

─── BALANÇO ENERGÉTICO ────────────────────
  Q = {Q_W/1000:.4f} kW
  LMTD = {dTlm:.4f} °C   F = {F:.4f}   (Np={Np})
  Desvio = 0.00 %

─── PAREDE (iter: {mw['it']}, {'✓' if mw['conv'] else '⚠'}) ──────────
  Tw casco = {mw['Twq']:.2f}°C   μw,s={mw['mwq']:.3e}   φs={mw['phq']:.4f}
  Tw tubo  = {mw['Twf']:.2f}°C   μw,t={mw['mwf']:.3e}   φt={mw['phf']:.4f}

─── CASCO ─────────────────────────────────
  Gs = {casco['Gs']:.4f} kg/m²·s
  Res = {casco['Res']:.0f}   Prs = {casco['Prs']:.4f}
  hs = {casco['hs']:.2f} W/m²·K
  ΔPs = {dPs_kPa:.4f} kPa  [máx {dPs_max:.1f}] {dPs_ok}

─── TUBOS ─────────────────────────────────
  Gt = {tubos['Gt']:.4f} kg/m²·s   v = {tubos['vt']:.3f} m/s
  Ret = {tubos['Ret']:.0f} [{tubos['reg']}]
  ht = {tubos['ht']:.2f} W/m²·K
  ΔPt = {dPt_kPa:.4f} kPa  [máx {dPt_max:.1f}] {dPt_ok}

─── GLOBAL ────────────────────────────────
  R_ext  = {glob['Re']:.6f}
  R_cond = {glob['Rc']:.6f}
  R_int  = {glob['Ri']:.6f}
  R_foul = {glob['Rf']:.6f}
  U = {glob['U']:.2f} W/m²·K

─── DIMENSIONAMENTO ───────────────────────
  Área calc. = {glob['A']:.4f} m²
  Área inst. = {Ai:.4f} m²
  Excesso    = {ex:.1f} %

─── DIAGNÓSTICO ───────────────────────────
  {diag}
"""
        if metodo == "bd":
            txt += f"\n─── FATORES J ─────────────────────────\n"
            txt += f"  Jc={fat['Jc']:.4f}  Jl={fat['Jl']:.4f}  Jb={fat['Jb']:.4f}\n"
            txt += f"  Js={fat['Js']:.4f}  Jr={fat['Jr']:.4f}  ∏J={PJ:.4f}\n"

        st.session_state[f"{prefixo}_resultado"] = txt

        # ─── Memorial ───
        memo = f"""
═══════════════════════════════════════════════════════════
  MEMORIAL DE CÁLCULO — {metodo_label}
═══════════════════════════════════════════════════════════

[ETAPA 1] BALANÇO DE ENERGIA
  Q = ṁ · cp · |ΔT|
  Q_quente = {ms:.4f} × {cp_s:.1f} × ({Thi:.2f} - {Tho:.2f}) = {Q_W/1000:.4f} kW
  Q_frio   = {mt:.4f} × {cp_t:.1f} × ({Tco:.2f} - {Tci:.2f}) = {Q_W/1000:.4f} kW

[ETAPA 2] LMTD E FATOR F
  ΔT1 = {Thi:.2f} - {Tco:.2f} = {Thi-Tco:.4f} °C
  ΔT2 = {Tho:.2f} - {Tci:.2f} = {Tho-Tci:.4f} °C
  LMTD = {dTlm:.4f} °C
  F = {F:.4f}  (Np = {Np})

[ETAPA 3] GEOMETRIA
  di = d_o - 2e = {d:.5f} - 2×{e_p:.5f} = {di:.5f} m
  Nb = floor(Lta/Lbc) - 1 = {Nb}
  Dhs/Atc = {geo0['Dhs']*1000:.2f} mm / {geo0['Atc']*1e4:.4f} cm²

[ETAPA 4] COEFICIENTE DE PELÍCULA — CASCO
  Gs = ṁₛ/Atc = {casco['Gs']:.4f} kg/m²·s
  Res = {casco['Res']:.1f}   Prs = {casco['Prs']:.4f}
  hs = {casco['hs']:.2f} W/m²·K

[ETAPA 5] COEFICIENTE DE PELÍCULA — TUBOS
  Ret = {tubos['Ret']:.1f}  [{tubos['reg']}]
  Nut = {tubos['Nut']:.4f}
  ht = {tubos['ht']:.2f} W/m²·K

[ETAPA 6] TEMPERATURA NA PAREDE (iterativo)
  T_w,s = {mw['Twq']:.2f} °C → μw,s = {mw['mwq']:.4e} Pa·s → φs = {mw['phq']:.4f}
  T_w,t = {mw['Twf']:.2f} °C → μw,t = {mw['mwf']:.4e} Pa·s → φt = {mw['phf']:.4f}

[ETAPA 7] QUEDA DE PRESSÃO
  ΔPs = {dPs_kPa:.4f} kPa
  ΔPt = {dPt_kPa:.4f} kPa

[ETAPA 8] COEFICIENTE GLOBAL
  R_ext  = {glob['Re']:.6f} m²·K/W
  R_cond = {glob['Rc']:.6f} m²·K/W
  R_int  = {glob['Ri']:.6f} m²·K/W
  R_foul = {glob['Rf']:.6f} m²·K/W
  U = {glob['U']:.2f} W/m²·K

[ETAPA 9] ÁREA DE TROCA
  A = Q / (U · LMTD · F)
  A = {Q_W:.2f} / ({glob['U']:.2f} × {dTlm:.4f} × {F:.4f})
  A = {glob['A']:.4f} m²
  A instalada = Nt·π·d·Lta = {Ai:.4f} m²
  Excesso = {ex:.1f} %

═══════════════════════════════════════════════════════════
  Ref: Kern(1950) · Kakaç&Liu(2002) · Thulukkanam(2013) · TEMA
═══════════════════════════════════════════════════════════
"""
        st.session_state[f"{prefixo}_memorial"] = memo
        st.success("✅ Cálculo concluído! Veja os resultados ao lado →")
        st.rerun()

    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
        import traceback
        st.code(traceback.format_exc())

# ═════════════════════════════════════════════════════════════════
#  EXECUTA AS DUAS ABAS
# ═════════════════════════════════════════════════════════════════
with tab_k:
    render_aba("k", "#00C2FF", "kern")

with tab_b:
    render_aba("b", "#FF6B35", "bd")

st.markdown("---")
st.caption("Kern(1950) · Bell&Mueller(2001) · Kakaç&Liu(2002) · Thulukkanam(2013) · TEMA")
