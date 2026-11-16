import subprocess, sys, re, numpy as np
def net(load_r="1e9", load_c="1p", vdac="PULSE(0.2 2.4 20u 50n 50n 80u 200u)", tstop="200u", extra="", p=None):
    P=dict(Rb=330, Rb1=None, Rb2=None, Res=4.7, Resk=33, Rbyp="1k", Cf="47p", Rf="40.2k", Rg="10k", Rsh=0.22, Rrail=16, Rout="0.001", Cx="1n", Rq="1e12", Rdac="1", Cdac="1p", Rfx="1e12", Rfy="1e12", FB=0)
    if p: P.update(p)
    P['Rb1']=P['Rb1'] or P['Rb']; P['Rb2']=P['Rb2'] or P['Rb']
    return f"""* 0-12V 100mA output stage
.include stage.lib
.include models.lib
Vp vp 0 {P['Rrail']}
Vload vl 0 {P.get('Vload',0)}
Vn vn 0 -5
Vd dac0 0 {vdac}
Rdac dac0 dac {P['Rdac']}
Cdac dac 0 {P['Cdac']}
XU dac fbn vp vn oa opa
* source path
Rb1 oa b1 {P['Rb1']}
Q1 vp b1 e1 QBCP56
Res e1 e1b {P['Res']}
Qls b1 lsb e1b QBC847
Rfx e1 lsb {P['Rfx'] if P['FB'] else '0.001'}
Rfy vp lsb {P['Rfy'] if P['FB'] else '1e12'}
D1 e1b x DSCH
* sink path
Rb2 oa b2 {P['Rb2']}
Q2 {P.get('Q2c','0')} b2 e2 QBCP53
Resk x e2 {P['Resk']}
Qlk b2 e2 x QBC857
* bypass for small currents / deadband
Rbyp oa x {P['Rbyp']}
Cx x 0 {P['Cx']}
* shunt + output
Rq x vn {P['Rq']}
Rsh x xo {P['Rsh']}
Rout xo out {P['Rout']}
* feedback (DC from connector, HF from op-amp output)
Rf out fbn {P['Rf']}
Rg fbn 0 {P['Rg']}
Cf oa fbn {P['Cf']}
* load
RL out vl {load_r}
CL out 0 {load_c}
{extra}
.options method=gear reltol=1e-4
.tran 5n {tstop} 0 5n
.control
run
wrdata out.txt v(out) v(dac) i(Vp) v(oa) v(e1) v(x) v(b1) v(b2) i(Vload)
.endc
.end
"""
import os
def run(**kw):
    tag=str(os.getpid())
    open(f"t{tag}.cir","w").write(net(**kw).replace("wrdata out.txt", f"wrdata out{tag}.txt"))
    r=subprocess.run(["ngspice","-b",f"t{tag}.cir"],capture_output=True,text=True)
    if "error" in r.stdout.lower() and "out.txt" not in r.stdout:
        print(r.stdout[-2000:])
    a=np.loadtxt(f"out{tag}.txt")
    return a[:,0], a[:,1], a[:,3], a[:,7]
def settle(t,v,t0,t1,final,tol):
    m=(t>t0)&(t<t1); tt=t[m]; vv=v[m]
    bad=np.where(abs(vv-final)>tol)[0]
    return (tt[bad[-1]]-t0) if len(bad) else 0.0
if __name__=="__main__":
    for rl,cl in [("1e9","1p"),("120","1p"),("1e9","10n"),("120","100n"),("1e9","1u"),("1k","1n")]:
        t,v,d,oa=run(load_r=rl,load_c=cl)
        hi=2.4*5.02; lo=0.2*5.02
        vh=v[(t>95e-6)&(t<99e-6)].mean(); vl=v[(t>195e-6)].mean()
        su=settle(t,v,20e-6,100e-6,vh,0.012); sd=settle(t,v,100.05e-6,200e-6,vl,0.012)
        ov=(v[(t>20e-6)&(t<100e-6)].max()-vh)
        print(f"RL={rl:>4} CL={cl:>4}: high {vh:.4f} V low {vl:.4f} V | rise settle(1mV-ish 0.1%) {su*1e6:6.2f} us fall {sd*1e6:6.2f} us | overshoot {ov*1e3:6.1f} mV")
