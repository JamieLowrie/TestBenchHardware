#!/bin/bash
set -e
cd "$(dirname "$0")/../pcbwork"
/usr/bin/python3 ../gen/make_pcb.py base.kicad_pcb 2>&1 | grep -v leak
/usr/bin/python3 ../gen/make_pcb.py dsnboard.kicad_pcb route.dsn 2>&1 | grep -v leak
for n in base final; do cp ../gen/phase_sense.kicad_dru $n.kicad_dru; cp ../out/phase_sense.kicad_pro $n.kicad_pro; done
rm -f route.ses
timeout 300 xvfb-run -a java -jar ../../tools/freerouting.jar -de route.dsn -do route.ses -mp 200 > fr.log 2>&1 || true
/usr/bin/python3 ../gen/route.py finish base.kicad_pcb route.ses final.kicad_pcb 2>&1 | grep -v leak
/usr/bin/python3 -c "
import pcbnew
b=pcbnew.LoadBoard('final.kicad_pcb')
pcbnew.WriteDRCReport(b,'drc.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)" 2>&1 | grep -v leak || true
grep -E 'Found' drc.rpt; grep -E '^\[' drc.rpt | sed 's/\].*/]/' | sort | uniq -c
