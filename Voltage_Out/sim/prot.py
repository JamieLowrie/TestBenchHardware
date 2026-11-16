import numpy as np, sys, subprocess, os
from gen import net
BASE=dict(Res=4.7, Rfx="1k", Rfy="33k", FB=1, Rsh="0.001", Rout="10", Rq="10000", Cf="47p", Rdac="1k", Cdac="3.3n",
          Rb1="1500", Rb2="10000", Rbyp="10000", Q2c="vn", Resk="47")
def dc(rl, vdac, vload=0, **kw):
    p=dict(BASE); p.update(kw); p["Vload"]=vload
    tag=f"p{os.getpid()}"
    c=net(load_r=rl,load_c="1p",vdac=vdac,tstop="400u",p=p).replace("wrdata out.txt",f"wrdata {tag}.txt")
    open(f"{tag}.cir","w").write(c); subprocess.run(["ngspice","-b",f"{tag}.cir"],capture_output=True)
    a=np.loadtxt(f"{tag}.txt")[-1]
    out,ip,oa,e1,x,b1,b2=a[1],-a[5],a[7],a[9],a[11],a[13],a[15]
    P=lambda v,r: v*v/float(r)
    return dict(out=out, iload=(out-vload)/float(rl), ip=ip, pq1=(16-e1)*ip, oa=oa,
                iop=(oa-b1)/float(p["Rb1"])+(oa-b2)/float(p["Rb2"])+(oa-x)/float(p["Rbyp"]),
                prb1=P(oa-b1,p["Rb1"]), prb2=P(oa-b2,p["Rb2"]), prbyp=P(oa-x,p["Rbyp"]), prq=P(x+5,p["Rq"]),
                pq2=abs((x-0)*((x+5)/1e4*0+0)), x=x)
if __name__=="__main__":
    if len(sys.argv)>1: BASE["Rfy"]=sys.argv[1]
    print("source sweep, setpoint 12 V")
    for rl in ["1e9","1000","120","100","60","40","20","10","5","0.1"]:
        r=dc(rl,"2.39")
        print(f" RL={rl:>5}: Vout {r['out']:6.2f} Iload {r['iload']*1e3:6.1f} mA  P(Q301) {r['pq1']:.2f} W  Iopamp {r['iop']*1e3:5.1f} mA  P(Rb1) {r['prb1']*1e3:4.0f} mW P(Rbyp) {r['prbyp']*1e3:4.0f} mW")
    print("short to battery through 0.1 R, setpoint 0 / 6 / 12 V")
    for vb in [5, 12, 24, 32]:
        for vd in ["0.0", "1.2", "2.39"]:
            r=dc("0.1",vd,vload=vb)
            pq2=(r["x"]+5)*(-r["iload"])
            print(f" Vbat {vb:2d} set {float(vd)*5.02:5.2f}: I into pin {-r['iload']*1e3:6.1f} mA  P(Q302)~{pq2:.2f} W  Iopamp {r['iop']*1e3:6.1f} mA  P(Rb2) {r['prb2']*1e3:4.0f} mW P(Rbyp) {r['prbyp']*1e3:4.0f} mW P(Rq) {r['prq']*1e3:4.0f} mW  oa {r['oa']:.1f}")
    print("pull-up loads at 0 V setpoint")
    for vb,rl in [(5,"1000"),(5,"10000"),(12,"1000"),(5,"220")]:
        r=dc(rl,"0.0",vload=vb); print(f" {vb} V via {rl}: Vout {r['out']*1e3:.2f} mV  sink {-r['iload']*1e3:.2f} mA")
