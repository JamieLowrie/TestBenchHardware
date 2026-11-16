import numpy as np, sys
from gen import run, settle
LOADS=[("1e9","1p"),("120","1p"),("1e9","10n"),("120","10n"),("1e9","100n"),("1000","1u")]
p=dict(Res=4.7, Rfx="1k", Rfy=sys.argv[1], FB=1, Rsh="0.001", Rout="10", Rq="10k", Cf=sys.argv[2], Rdac="2k", Cdac="3.3n",
       Rb1="1.5k", Rb2="10k", Rbyp=sys.argv[3], Q2c="vn", Resk="47")
for rl,cl in LOADS:
    for lo_,hi_ in [(0.2,2.39),(1.0,1.02)]:
        t,v,d,oa=run(load_r=rl,load_c=cl,p=p,tstop="1m",vdac=f"PULSE({lo_} {hi_} 20u 50n 50n 480u 1m)")
        hi=v[(t>490e-6)&(t<499e-6)].mean(); lo=v[(t>990e-6)].mean()
        tol=0.012 if hi_-lo_>1 else 0.001
        su=settle(t,v,20e-6,500e-6,hi,tol); sd=settle(t,v,500.05e-6,1000e-6,lo,tol)
        ov=v[(t>20e-6)&(t<500e-6)].max()-hi; un=lo-v[t>500e-6].min()
        print(f"RL={rl:>5} CL={cl:>4} step {lo_*5.02:.2f}->{hi_*5.02:.2f}: rise {su*1e6:6.1f}us fall {sd*1e6:6.1f}us over {ov*1e3:6.1f}mV under {un*1e3:6.1f}mV", flush=True)
