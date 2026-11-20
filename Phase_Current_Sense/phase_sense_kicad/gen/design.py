"""Single source of truth for parts and nets (schematic + PCB both read this)."""
import uuid

NS = uuid.UUID("6c1f8f0e-2d7c-4a54-9a4e-0a5e5e1f0001")
def uid(s):
    return str(uuid.uuid5(NS, s))

FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_R0402 = "Resistor_SMD:R_0402_1005Metric"
FP_U = "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm"
FP_LUG = "phase_sense:XFCN_T44001_M4_Terminal"
FP_HDR = "Connector_PinHeader_2.54mm:PinHeader_2x07_P2.54mm_Vertical"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_MH = "phase_sense:CDIB_Pillar_No6_Screw"

LCSC = {
    "ACS": "C3684355", "100n": "C14663", "10n": "C57112", "10k": "C25804",
    "33k": "C4216", "1k": "C21190", "10u": "C19702", "T44001": "C481447", "47k": "C25819", "2k7": "C13167", "22n": "C21122", "0R0402": "C17168", "10k0402": "C25744", "AO3401A": "C15127",
}

# part: ref, lib_id, value, footprint, lcsc, {pin: net}  (net None => no-connect)
PARTS = []
def add(ref, lib, val, fp, lcsc, pins, desc="", dnp=False):
    PARTS.append(dict(ref=ref, lib=lib, value=val, fp=fp, lcsc=lcsc, pins=pins, uuid=uid(ref), desc=desc, dnp=dnp))

CH = ["A", "B", "C"]
for k, X in enumerate(CH, start=1):
    # drive side (IN) -> IP+ (pins 1-4), motor side (OUT) -> IP- (pins 5-8): drive->motor current reads POSITIVE
    pins = {str(n): f"P{X}_IN" for n in (1, 2, 3, 4)}
    pins.update({str(n): f"P{X}_OUT" for n in (5, 6, 7, 8)})
    pins.update({"9": "FAULT_N", "10": "+3.3VA", "11": f"VOC_{X}", "12": f"VIOUT_{X}",
                 "13": None, "14": "GS1", "15": "GND", "16": "GS0"})
    add(f"U{k}", "phase_sense:ACS37002xMA", "ACS37002LMABTR-066B3", FP_U, LCSC["ACS"], pins,
        f"Phase {X} current sensor")
    add(f"C{k}1", "Device:C", "100n", FP_C, LCSC["100n"], {"1": "+3.3VA", "2": "GND"}, "VCC bypass")
    add(f"R{k}1", "Device:R", "33k", FP_R, LCSC["33k"], {"1": "+3.3VA", "2": f"VOC_{X}"}, "VOC divider top")
    add(f"R{k}2", "Device:R", "10k", FP_R, LCSC["10k"], {"1": f"VOC_{X}", "2": "GND"}, "VOC divider bottom")
    add(f"C{k}2", "Device:C", "100n", FP_C, LCSC["100n"], {"1": f"VOC_{X}", "2": "GND"}, "VOC filter")
    add(f"R{k}3", "Device:R", "1k", FP_R, LCSC["1k"], {"1": f"VIOUT_{X}", "2": f"I{X}"}, "ADC RC filter R")
    add(f"C{k}3", "Device:C", "10n", FP_C, LCSC["10n"], {"1": f"I{X}", "2": "GND"}, "ADC RC filter C")
    add(f"R{k}4", "Device:R", "47k", FP_R, LCSC["47k"], {"1": f"P{X}_OUT", "2": f"VMID_{X}"}, "Phase V divider top 1 (motor side)")
    add(f"R{k}5", "Device:R", "47k", FP_R, LCSC["47k"], {"1": f"VMID_{X}", "2": f"V{X}"}, "Phase V divider top 2")
    add(f"R{k}6", "Device:R", "2.7k", FP_R, LCSC["2k7"], {"1": f"V{X}", "2": "GND"}, "Phase V divider bottom")
    add(f"C{k}4", "Device:C", "22n", FP_C, LCSC["22n"], {"1": f"V{X}", "2": "GND"}, "Phase V filter (~2.8 kHz)")
    # GAIN_SEL_0/1 of all three sensors are bussed (GS0 / GS1) and driven by the MCU through R3 / R4.
    #   GAIN_SEL_1 GAIN_SEL_0 : 00 19.8 mV/A +/-66.7 A | 01 16.5 +/-80 | 10 13.2 +/-100 | 11 9.9 +/-133.3
    add(f"J{2*k}", "Connector_Generic:Conn_01x01", "T44001", FP_LUG, LCSC["T44001"], {"1": f"P{X}_IN"}, f"Phase {X} IN, M4 terminal")
    add(f"J{2*k+1}", "Connector_Generic:Conn_01x01", "T44001", FP_LUG, LCSC["T44001"], {"1": f"P{X}_OUT"}, f"Phase {X} OUT, M4 terminal")

add("R1", "Device:R", "10k", FP_R, LCSC["10k"], {"1": "+3.3VA", "2": "FAULT_N"}, "OCF wired-OR pull-up (sensor rail)")
add("C1", "Device:C", "10u", FP_C, LCSC["10u"], {"1": "+3.3VA", "2": "GND"}, "Bulk, sensor rail")
add("Q1", "Device:Q_PMOS_GSD", "AO3401A", FP_SOT23, LCSC["AO3401A"], {"1": "SNS_OFF", "2": "+3V3", "3": "+3.3VA"},
    "Sensor power switch (re-latches GAIN_SEL)")
add("R2", "Device:R", "10k", FP_R, LCSC["10k"], {"1": "SNS_OFF", "2": "GND"}, "Q1 gate pull-down: sensors ON by default")
add("R3", "Device:R", "10k", FP_R, LCSC["10k"], {"1": "GS0_MCU", "2": "GS0"}, "GAIN_SEL_0 series (limits back-feed while sensors are off)")
add("R4", "Device:R", "10k", FP_R, LCSC["10k"], {"1": "GS1_MCU", "2": "GS1"}, "GAIN_SEL_1 series")
add("J1", "Connector_Generic:Conn_01x14", "TO_MCU", FP_HDR, "",
    {"1": "+3V3", "2": "IA", "3": "IB", "4": "IC", "5": "VA", "6": "VB", "7": "VC", "8": "FAULT_N", "9": "GND", "10": "GND",
     "11": "GS0_MCU", "12": "GS1_MCU", "13": "SNS_OFF", "14": "GND"},
    "To CH32V203 board")
add("J8", "Connector_Generic:Conn_01x01", "T44001", FP_LUG, LCSC["T44001"], {"1": "GND"}, "Drive DC- reference link, M4 terminal")
add("H1", "Mechanical:MountingHole", "No6 screw", FP_MH, "", {}, "")
add("H2", "Mechanical:MountingHole", "No6 screw", FP_MH, "", {}, "")

NETS = sorted({n for p in PARTS for n in p["pins"].values() if n})
