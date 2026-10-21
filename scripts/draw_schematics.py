"""Deterministic original SVGs, with the same node names as the SPICE decks."""
from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'模拟/图'
OUT.mkdir(parents=True,exist_ok=True)


def line(x1,y1,x2,y2):
    return f'<path d="M{x1} {y1} L{x2} {y2}"/>'


def text(x,y,s):
    return f'<text x="{x}" y="{y}" stroke="none">{escape(s)}</text>'


def ground(x,y):
    return line(x,y,x,y+8)+line(x-12,y+8,x+12,y+8)+line(x-8,y+14,x+8,y+14)+line(x-3,y+20,x+3,y+20)


def resistor(x,y,label):
    return line(x,y,x,y+10)+f'<path d="M{x} {y+10} l-7 6 l14 8 l-14 8 l14 8 l-7 6"/>'+line(x,y+46,x,y+56)+text(x+17,y+30,label)


def mos():
    return (line(245,170,245,230)+line(258,170,258,230)+line(258,175,280,175)
        +line(280,175,280,150)+line(258,225,280,225)+line(280,225,280,245)
        +line(258,200,315,200)+ground(315,200)+text(325,204,'B = 0')
        +text(190,183,'G')+text(285,168,'D')+text(285,243,'S')+text(325,255,'W/L = 10 µm / 1 µm'))


def write(name,body,description):
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="660" height="350" viewBox="0 0 660 350">
<title>{escape(description)}</title><desc>Original TechCodex circuit; labels follow the corresponding ngspice netlist.</desc>
<rect width="660" height="350" fill="white"/>
<g fill="none" stroke="#172b3a" stroke-width="2" stroke-linejoin="round">{body}</g>
</svg>'''
    # Keep text legible on GitHub and portable across Windows/Linux renderers.
    svg=svg.replace('<text ','<text fill="#172b3a" font-family="Arial, sans-serif" font-size="16" ')
    (OUT/(name+'.svg')).write_text(svg,encoding='utf-8')


body=mos()+line(100,200,245,200)+text(45,195,'Vg = 0.9 V')+line(280,60,280,150)+text(290,80,'Vd = 1.65 V')+ground(280,245)
body+=text(40,35,'V0: independently bias gate and drain')
write('v0-device',body,'V0 four-terminal NMOS characterization')

body=mos()+line(80,200,245,200)+text(40,190,'Vin: 0.9 V + vin')
body+=resistor(280,70,'RD = 39 kΩ')+line(280,126,280,150)+line(280,45,280,70)+text(245,33,'VDD = 3.3 V')
body+=line(280,145,485,145)+text(380,135,'out')+line(465,145,465,195)+line(450,195,480,195)+line(450,203,480,203)+ground(465,203)+text(495,200,'CL = 2 pF')
body+=resistor(280,245,'RS = 0 Ω / 1 kΩ')+ground(280,301)
write('v1-common-source',body,'V1 common-source amplifier and V1b source degeneration')

body=text(35,35,'Low-frequency model: source and bulk at AC ground')
body+=line(100,110,550,110)+text(110,98,'vout')
body+=resistor(145,110,'RD')+ground(145,166)
body+=resistor(330,110,'ro = 1/gds')+ground(330,166)
body+=line(520,110,520,130)+'<path d="M520 130 l20 30 l-20 30 l-20 -30 Z"/>'+line(520,142,520,178)+'<path d="M514 169 l6 9 l6 -9"/>'+ground(520,190)+text(555,165,'gm vin')
body+=text(70,280,'KCL: vout/RD + gds vout + gm vin = 0')
write('v1-small-signal',body,'Low-frequency common-source small-signal model')
