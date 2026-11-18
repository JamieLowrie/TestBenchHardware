"""Project symbol library: ACS37002 (SOICW-16, MA package), laid out for left->right signal flow.
Left  : IP+ (1-4) top group, IP- (5-8) bottom group      (primary / HV side)
Top   : VCC
Right : VOC, VREF, VIOUT, OCF, GAIN_SEL_0, GAIN_SEL_1, GND  (secondary / LV side)"""

PINS = [  # number, name, type, x, y, angle   (library coords, y up; pin 'at' = connection point)
    ("1", "IP+", "passive", -12.7, 10.16, 0), ("2", "IP+", "passive", -12.7, 7.62, 0),
    ("3", "IP+", "passive", -12.7, 5.08, 0), ("4", "IP+", "passive", -12.7, 2.54, 0),
    ("5", "IP-", "passive", -12.7, -2.54, 0), ("6", "IP-", "passive", -12.7, -5.08, 0),
    ("7", "IP-", "passive", -12.7, -7.62, 0), ("8", "IP-", "passive", -12.7, -10.16, 0),
    ("10", "VCC", "power_in", 0, 15.24, 270),
    ("11", "VOC", "input", 12.7, 10.16, 180), ("13", "VREF", "output", 12.7, 7.62, 180),
    ("12", "VIOUT", "output", 12.7, 2.54, 180), ("9", "~{OCF}", "open_collector", 12.7, -2.54, 180),
    ("16", "GAIN_SEL_0", "input", 12.7, -5.08, 180), ("14", "GAIN_SEL_1", "input", 12.7, -7.62, 180),
    ("15", "GND", "power_in", 12.7, -10.16, 180),
]


def lib_text():
    body = ""
    for n, nm, t, x, y, a in PINS:
        body += (f'      (pin {t} line (at {x} {y} {a}) (length 2.54)\n'
                 f'        (name "{nm}" (effects (font (size 1.27 1.27))))\n'
                 f'        (number "{n}" (effects (font (size 1.27 1.27))))\n      )\n')
    return f'''(kicad_symbol_lib (version 20220914) (generator phase_sense_gen)
  (symbol "ACS37002xMA" (in_bom yes) (on_board yes)
    (property "Reference" "U" (at -10.16 15.24 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "ACS37002LMABTR-066B3" (at -10.16 -15.24 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm" (at 0 -17.78 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "https://www.allegromicro.com/-/media/files/datasheets/acs37002-datasheet.pdf" (at 0 -20.32 0) (effects (font (size 1.27 1.27)) hide))
    (property "Description" "Hall current sensor, 400 kHz, +/-66.7 A (GAIN_SEL=00), 3.3 V, SOICW-16" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "ACS37002xMA_0_1"
      (rectangle (start -10.16 12.7) (end 10.16 -12.7) (stroke (width 0.254) (type default)) (fill (type background)))
      (polyline (pts (xy -3.81 12.7) (xy -3.81 -12.7)) (stroke (width 0.1524) (type dash)) (fill (type none)))
      (text "HV" (at -6.35 -11.43 0) (effects (font (size 0.8 0.8))))
      (text "LV" (at -1.27 -11.43 0) (effects (font (size 0.8 0.8))))
    )
    (symbol "ACS37002xMA_1_1"
{body}    )
  )
)
'''


if __name__ == "__main__":
    import sys
    open(sys.argv[1], "w").write(lib_text())
