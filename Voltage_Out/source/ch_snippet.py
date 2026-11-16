frame(15.24, 111.76, 405.13, 254.0, CH_TITLE)
# decoupling, placed at the pins on the PCB
vt("C304", 25.4, 127.0, "+16V", "GND"); vt("C305", 38.1, 127.0, "-5V", "GND")
TEXTS.append((22.86, 149.86, "C304/C305 at U302", 1.27))
put("R301", 80.01, 193.04, sym="R_H")
stublab("DAC_X", pin("R301", "1"), -2.54)
W(pin("R301", "2"), (93.98, 193.04))
vt("C303", 88.9, 193.04, None, "GND")
TEXTS.append((40.64, 213.36, "From U602 VOUTX.  R301/C303: 6.6 us filter, keeps the\nloop out of current limit on full-scale steps into 10 nF", 1.27))
# op-amp + gain network
put("U302", 101.6, 190.5)
stubpw("+16V", pin("U302", "5"), 0, -2.54)
stubpw("-5V", pin("U302", "2"), 0, 2.54)
W(pin("U302", "4"), (91.44, 187.96), (91.44, 167.64))
put("R302", 87.63, 172.72, sym="R_H"); stublab("OUT", pin("R302", "1"), -2.54)
put("R303", 87.63, 182.88, sym="R_H"); stubpw("GND", pin("R303", "1"), -2.54)
put("C306", 95.25, 167.64, sym="C_H")
xb = 111.76
W(pin("C306", "2"), (xb, 167.64))
W(pin("U302", "1"), (xb, 190.5))
W((xb, 167.64), (xb, 205.74))
TEXTS.append((40.64, 172.72, "Feedback taken at\nthe terminal, after\nR314", 1.27))
# source transistor + current limit
put("R307", 120.65, 167.64, sym="R_H")
W((xb, 167.64), pin("R307", "1"))
put("Q301", 139.7, 167.64)
W(pin("R307", "2"), pin("Q301", "1"))
stubpw("+16V", pin("Q301", "2"), 0, -2.54)
put("Q305", 127.0, 173.99)
W(pin("Q305", "3"), (124.46, 167.64))
vcap("R308", 142.24, 173.99)
W(pin("Q301", "3"), pin("R308", "1"))
put("R315", 137.16, 173.99, sym="R_H")
W(pin("Q305", "1"), pin("R315", "1")); W(pin("R315", "2"), pin("R308", "1"))
W(pin("Q305", "1"), (132.08, 180.34), (134.62, 180.34)); lab("LIM_B", (134.62, 180.34))
vt("R316", 124.46, 137.16, "+16V", "LIM_B")
put("D301", 142.24, 186.69)
W(pin("R308", "2"), pin("D301", "2"))
W(pin("Q305", "2"), (124.46, 182.88), pin("D301", "2"))
# bypass resistor, X node, sink transistor
yx = 190.5
put("R311", 120.65, yx, sym="R_H")
W((xb, yx), pin("R311", "1"))
W(pin("R311", "2"), (199.39, yx))
vcap("R310", 142.24, 191.77)
W(pin("D301", "1"), pin("R310", "1"))
put("Q306", 132.08, 199.39)
W(pin("Q306", "2"), (129.54, yx))
W(pin("Q306", "1"), pin("R310", "2"))
put("Q302", 139.7, 205.74)
W(pin("R310", "2"), pin("Q302", "3"))
pw("-5V", pin("Q302", "2"))
put("R309", 120.65, 205.74, sym="R_H")
W((xb, 205.74), pin("R309", "1"))
W(pin("R309", "2"), pin("Q302", "1"))
W(pin("Q306", "3"), (129.54, 205.74))
vt("C307", 152.4, yx, None, "GND")
vt("R312", 162.56, yx, None, "-5V")
lab("OUT_INT", (167.64, yx))
put("R314", 203.2, yx, sym="R_H")
put("J301", 241.3, yx)
W(pin("R314", "2"), pin("J301", "1")); lab("OUT", (209.55, yx))
vt("D302", 218.44, yx, None, "GND")
stubpw("GND", pin("J301", "2"), -2.54)
TEXTS.append((149.86, 160.02, "Q305/R308/R315/R316: fold-back limit, 120 mA near full output,\n~25 mA into a short (Q301 < 0.5 W anywhere).  D301 blocks a short to battery", 1.27))
TEXTS.append((149.86, 220.98, "Q306/R310: sink limit ~15 mA (Q302 ~0.5 W with the pin at 32 V, continuous)\nR312 keeps a few hundred uA through Q301 near 0 V\nR311 carries small signals across the crossover", 1.27))
TEXTS.append((214.63, 207.01, "ESD / load dump", 1.27))
TEXTS.append((233.68, 182.88, "To ECU input", 1.27))
if SHOW_HOW:
    TEXTS.append((256.54, 175.26,
      "HOW IT WORKS\n"
      "U302 compares Vout x 10k/50.2k with the DAC voltage and drives\n"
      "the push-pull pair. Q301 (BCP56) sources from +16 V through D301;\n"
      "Q302 (BCP53) sinks to -5 V so a pulled-up ECU input reads 0.000 V.\n"
      "C306 47 pF + R314 10 R isolate cable / ECU capacitance from the loop.\n\n"
      "FAULTS (all handled in hardware, no firmware needed)\n"
      "Short to GND: fold-back limits to ~25 mA, 0.2 W, continuous.\n"
      "Short to battery up to 32 V: D301 blocks, sink limited, continuous.\n"
      "Overload: current folds back with Vce, Q301 stays under 0.5 W.\n"
      "Transients / ESD: D302.  Resistors that see a fault are 1206.", 1.27))
