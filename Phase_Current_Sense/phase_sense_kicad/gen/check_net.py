import re,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from design import PARTS
from kiutils.utils import sexpr
t=sexpr.parse_sexp(open(sys.argv[1]).read())
nets=[x for x in t if x[0]=='nets'][0][1:]
got={}
for n in nets:
    name=[a for a in n if a[0]=='name'][0][1]
    for nd in n:
        if nd[0]=='node':
            ref=[a for a in nd if a[0]=='ref'][0][1]; pin=[a for a in nd if a[0]=='pin'][0][1]
            got[(ref,pin)]=name.lstrip('/')
err=0
for p in PARTS:
    for pin,net in p['pins'].items():
        g=got.get((p['ref'],pin))
        if net is None:
            if g and not g.startswith('unconnected'): print('NC pin connected',p['ref'],pin,g); err+=1
        elif g!=net: print('MISMATCH',p['ref'],pin,'want',net,'got',g); err+=1
print('pins checked',sum(len(p['pins']) for p in PARTS),'errors',err)
