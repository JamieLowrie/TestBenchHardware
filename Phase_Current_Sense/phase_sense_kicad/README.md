# 3-Channel Motor Phase Current + Voltage Sense — ACS37002 (KiCad 7 project), rev F — 4 layers

Open `phase_sense.kicad_pro` in KiCad 7, 8 or 9 (8/9 will offer to upgrade the files).

## What it is
- 3 × Allegro ACS37002LMABTR-066B3 (LCSC C3684355): ±66.7 A, 19.8 mV/A, 1.65 V = 0 A, 3.3 V supply
- 3 × phase-voltage dividers: 47k + 47k (C25819, two in series for voltage rating) / 2.7k (C13167) with 22 nF (C21122),
  tapped on the **motor side** of each sensor
- Each phase passes through two XFCN T44001 M4 solder terminals (LCSC C481447, 40 A, 4 legs): **IN (from drive) → sensor → OUT (to motor)**
- **4 layers**, board = CamdenBoss **CDIB/6/L2** lower PCB: 99.0 × 82.8 mm, 1 mm corner chamfers (from `CDIB-6ST-L2.STEP`)

## Layout — rev F
- The sensor circuit is pushed as far right as it goes. **The controller gets X < 53.6 mm** (dashed line on silk). Only J1
  and its little ground pad (X 48.4–55.3, Y 46–62.6) stick over the line, as the interface.
- **Top-right window (Y < 10.5), from the middle outwards: DC− (J8, X 64.0), C IN 73.5, B IN 83.0, A IN 94.2.**
- **Bottom-right window (Y > 72.3): C OUT 65.5, B OUT 80.0, A OUT 94.2.**
- Each phase is one strip, C | B | A from left to right: IN terminal → sensor pins 1–4 (IP+) → pins 5–8 (IP−) → OUT terminal.
- **Layer use:**
  - **F.Cu / B.Cu:** phase copper on both layers, via-stitched, plus the small parts and GND.
  - **In1.Cu:** the LV signal wiring. It crosses under the phase strips only in a via-free band (Y 51.0–58.2).
  - **In2.Cu:** GND only. It sits under the LV areas, the crossing band, J1 and a strip from DC− down to J1. It is kept out from under the
    phase copper, so the phase dv/dt doesn't couple into GND.
- The A IN copper splits around the H2 pillar screw. It keeps 4 mm clear on top (under the screw head) and 2.4 mm clear on B.Cu.
  That still leaves about 5 mm on F.Cu and about 8.5 mm on B.Cu past the screw.

## Current sign
Drive → motor current enters IP+, so it reads **positive**: `I = (adc − zero) × (3.3 / 4096) / 0.0198` → ≈ 40.7 mA/count.

## J1 – interface header (2.54 mm, 2×5) at X 51.0 / 53.54, Y 50.6–60.8
Wire these nets to the CH32V203 on your controller layout, or keep J1 as a test header. Pin 1 is the square pad (top-left);
odd pins in the left column, even pins in the right. The pinout is printed on the back.

| Pin | Signal | Notes |
|---|---|---|
| 1 | 3V3 | Same rail as MCU VDDA (the current output is ratiometric) |
| 2 | IA | Phase A current, RC-filtered (1 kΩ / 10 nF, fc ≈ 16 kHz) → ADC |
| 3 | IB | Phase B current → ADC |
| 4 | IC | Phase C current → ADC |
| 5 | VA | Phase A voltage (÷35.8, fc ≈ 2.8 kHz) → ADC |
| 6 | VB | Phase B voltage → ADC |
| 7 | VC | Phase C voltage → ADC |
| 8 | FAULT_N | Open-drain wired-OR of all three OCF pins, 10 k pull-up on board, active low at ~77 A |
| 9, 10 | GND | |

Voltage: `V = adc × (3.3 / 4096) × (96.7 / 2.7)` → ≈ 28.9 mV/count, 118 V full scale (100 V → 2.79 V).

## J8 – drive DC− link (required for VA/VB/VC)
Phase voltage is measured relative to the drive's DC−. Bolt J8 to the drive's DC− with a short wire.
**This ties board GND (and your CH32V203, USB and debugger ground) to the drive's DC−**, so the board is not isolated
from the motor supply. Max bus voltage 100 V.

## Box fit (CDIB/6/L2), all in board coordinates (X right, Y down from the top window)
- **H1 (6.995, 66.405) and H2 (91.995, 16.405)**: Ø3.6 mm holes onto the two pillars, fixed with **No.6 self-tapping screws**.
- Terminal legs are only in the two open wiring strips (5.7 mm of space below the board there).
- **Centre platform, Y 21.5–61.2: only 0.5 mm below the PCB.** Everything there is SMD except **J1. Cut its legs flush**, or
  fit a surface-mount header.
- Box centre posts (X 45.7–53.2 at both ends) leave 3.3 mm above the board. Only flat copper is under them.
- About 19.5 mm from the PCB top to the roof: T44001 (8.4 mm) + ring lug + M4 pan head fits. Use ≤ 8 mm M4 screws.

## Spacing / creepage
- Custom DRC rule (`phase_sense.kicad_dru`): **every phase net keeps ≥ 0.5 mm from every other net**. That covers LV tracks, GND and the
  other phases (IPC-2221 B4, solder-masked, ≤ 100 V, with margin). Phase-to-phase copper gaps are 0.8 mm. The GND pour
  respects the rule when it is filled.
- The divider chains deliberately bridge HV to LV (47k + 47k), and J8 ties GND to DC−, so the board is **not** galvanically isolated.
- The ACS37002 package itself keeps ~7 mm between its HV and LV pins (1097 Vrms basic insulation working voltage).

## Known limitations — read before ordering
- **Current:** each sensor's primary is 0.85 mΩ, so 60 A DC ≈ 3 W per chip, which is too much for SOIC-16 continuously.
  **~30 A RMS per phase is the practical continuous limit. Order 2 oz outer copper.** The narrowest spot is A IN past
  the H2 screw (about 5 mm on F.Cu plus 8.5 mm on B.Cu).
- **Field coupling:** each phase's own OUT copper runs down right beside its sensor, and the next phase is one strip away.
  The ACS37002 rejects uniform external fields, but check each channel once against a clamp meter. If it is off by more than ~1 %,
  store a per-channel gain in firmware.

## Ordering at JLCPCB
1. Upload `fab/gerbers_JLCPCB.zip`. **4 layers, 1.6 mm, 2 oz outer copper** (the inner layers can stay at 0.5 oz; they carry no phase current).
2. PCB Assembly, top side: upload `fab/BOM_JLCPCB.csv` + `fab/CPL_JLCPCB.csv`.
3. **Check U1–U3 rotation in JLC's placement preview**: the pin-1 dot must be top-left, toward the IN terminals.
   KiCad and JLC sometimes disagree on SOIC rotation; fix it in the preview if needed.
4. J2–J8 (T44001) are through-hole. Either use JLC THT assembly, or remove them from the BOM and hand-solder with a big iron
   (≥ 80 W). The pours sink a lot of heat.
5. J1 is not in the BOM. Fit it yourself and trim the legs flush (see box notes).

## Verification done
- Schematic netlist cross-checked against the design (129 pins, 0 errors).
- PCB DRC: 0 unconnected, 0 clearance, 0 courtyard errors, with the 0.5 mm phase rule active. The only remaining entries are
  "library not in configuration" warnings from the headless build machine.
- Every PCB pad net and footprint matches the schematic (0 mismatches).

`gen/` holds the Python scripts that generated everything (`run.sh` = place + autoroute + DRC, `fab.py` = outputs).
