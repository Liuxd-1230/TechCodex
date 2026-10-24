"""Original deterministic SVG circuit vocabulary with explicit four-terminal MOS symbols."""
from html import escape
from pathlib import Path

INK='#203b4a'; SIGNAL='#127b70'; BODY='#a46723'; MUTED='#5a7381'


class Canvas:
    def __init__(self,title,w=600,h=460):
        self.title,self.w,self.h,self.parts=title,w,h,[]

    def line(self,x1,y1,x2,y2,color=INK,dash=False):
        self.parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}"'+(' stroke-dasharray="5 5"' if dash else '')+'/>')

    def wire(self,*points,color=INK,dash=False):
        for a,b in zip(points,points[1:]):self.line(*a,*b,color=color,dash=dash)

    def text(self,x,y,s,size=19,color=INK,anchor='start'):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(s)}</text>')

    def node(self,x,y,color=INK):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{color}" stroke="none"/>')

    def arrow(self,a,b,color=SIGNAL,dash=False):
        import math
        self.line(*a,*b,color=color,dash=dash)
        dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy); ux,uy=dx/length,dy/length
        p=(b[0]-10*ux+4*uy,b[1]-10*uy-4*ux);q=(b[0]-10*ux-4*uy,b[1]-10*uy+4*ux)
        self.parts.append(f'<path d="M{p[0]} {p[1]}L{b[0]} {b[1]}L{q[0]} {q[1]}" stroke="{color}"/>')

    def ground(self,x,y,color=INK):
        self.line(x,y,x,y+8,color)
        for dy,half in ((8,13),(15,8),(22,3)):self.line(x-half,y+dy,x+half,y+dy,color)

    def resistor(self,x,y,label='',height=76):
        self.line(x,y,x,y+10)
        points=[(x,y+10)]
        for i in range(6):points.append((x+(-7 if i%2==0 else 7),y+15+i*(height-30)/6))
        points.extend([(x,y+height-10),(x,y+height)])
        self.wire(*points)
        if label:self.text(x+18,y+height/2+6,label)

    def cap(self,x,y,label=''):
        self.line(x,y,x,y+25);self.line(x-14,y+25,x+14,y+25)
        self.line(x-14,y+33,x+14,y+33);self.line(x,y+33,x,y+60)
        if label:self.text(x+21,y+35,label)

    def cap_between(self,a,b):
        import math
        dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy);ux,uy=dx/length,dy/length
        mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
        p=(mx-4*ux,my-4*uy);q=(mx+4*ux,my+4*uy)
        self.line(*a,*p);self.line(*q,*b)
        for x,y in (p,q):self.line(x-12*uy,y+12*ux,x+12*uy,y-12*ux)

    def current(self,x,y,label='',controlled=False,up=False):
        self.line(x,y,x,y+15)
        if controlled:self.parts.append(f'<path d="M{x} {y+15}l24 27l-24 27l-24 -27Z"/>')
        else:self.parts.append(f'<circle cx="{x}" cy="{y+42}" r="25"/>')
        self.arrow((x,y+(54 if up else 30)),(x,y+(30 if up else 54)),INK)
        self.line(x,y+69,x,y+84)
        if label:self.text(x+35,y+48,label)

    def mos(self,x,y,name='M1',pmos=False):
        # Broken channel + bulk junction arrow: B is not a wire shorting D to S.
        self.line(x-25,y-31,x-25,y+31)
        for lo,hi in ((-31,-12),(-6,6),(12,31)):self.line(x,y+lo,x,y+hi)
        self.wire((x,y-25),(x+30,y-25),(x+30,y-60))
        self.wire((x,y+25),(x+30,y+25),(x+30,y+60))
        self.line(x-75,y,x-25,y)
        self.line(x+95,y,x+17,y,BODY)
        self.arrow((x+2,y),(x+16,y),BODY) if pmos else self.arrow((x+17,y),(x+2,y),BODY)
        self.text(x-32,y-42,name+' '+('P' if pmos else 'N'),17)
        self.text(x+39,y-46,'S' if pmos else 'D',15)
        self.text(x+39,y+53,'D' if pmos else 'S',15)
        self.text(x-76,y-10,'G',15)
        self.text(x+84,y-11,'B',15,BODY)
        return {'g':(x-75,y),'d':(x+30,y+(60 if pmos else -60)),
                's':(x+30,y+(-60 if pmos else 60)),'b':(x+95,y)}

    def save(self,name,out,description='TechCodex original teaching schematic. D, G, S, B are explicitly distinguished. Colored arrows show perturbations, not wires.'):
        css='text{font-family:"Microsoft YaHei","Noto Sans CJK SC",Arial,sans-serif;stroke:none}path,circle{vector-effect:non-scaling-stroke}'
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img"><title>{escape(self.title)}</title><desc>{escape(description)}</desc><style>{css}</style><rect width="100%" height="100%" fill="white"/><g fill="none" stroke="{INK}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+''.join(self.parts)+'</g></svg>\n'
        Path(out).mkdir(parents=True,exist_ok=True)
        (Path(out)/(name+'.svg')).write_text(svg,encoding='utf-8',newline='\n')
