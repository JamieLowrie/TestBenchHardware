#!/bin/bash
# re-run the autorouter with several pass limits on the current DSN; keep the first fully connected, DRC-clean result
cd "$(dirname "$0")/../pcbwork"
for mp in ${MPS:-30 45 75 90 120}; do
  rm -f route.ses t.kicad_pcb t.rpt
  timeout 300 xvfb-run -a java -jar ../../tools/freerouting.jar -de route.dsn -do route.ses -mp $mp > fr_$mp.log 2>&1 || true
  [ -f route.ses ] || { echo "mp $mp: no ses"; continue; }
  cp final.kicad_dru t.kicad_dru 2>/dev/null; cp final.kicad_pro t.kicad_pro 2>/dev/null
  /usr/bin/python3 ../gen/route.py finish base.kicad_pcb route.ses t.kicad_pcb > /dev/null 2>&1
  /usr/bin/python3 -c "
import pcbnew
b=pcbnew.LoadBoard('t.kicad_pcb'); pcbnew.WriteDRCReport(b,'t.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)" > /dev/null 2>&1
  u=$(grep -c '^\[unconnected_items\]' t.rpt); e=$(grep -E '^\[' t.rpt | grep -vc 'lib_footprint_issues')
  echo "mp $mp: unconnected $u, other issues $e"
  if [ "$e" = "0" ]; then cp t.kicad_pcb final.kicad_pcb; cp t.rpt drc.rpt; cp route.ses route_ok.ses; echo "kept mp $mp"; exit 0; fi
done
exit 1
