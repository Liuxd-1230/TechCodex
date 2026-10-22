"""Original Chapter 4 schematics: current paths, symmetry, headroom and routing."""
from pathlib import Path
from circuit_art import Canvas, INK, SIGNAL, BODY, MUTED

OUT=Path(__file__).resolve().parents[1]/'模拟/图'


def right_mos(c,x,y,name,pmos=False):
    """Right-facing NMOS; labels stay upright and the bulk lead stays separate."""
    c.line(x+25,y-31,x+25,y+31)
    for lo,hi in ((-31,-12),(-6,6),(12,31)):c.line(x,y+lo,x,y+hi)
    c.wire((x,y-25),(x-30,y-25),(x-30,y-60))
    c.wire((x,y+25),(x-30,y+25),(x-30,y+60))
    c.line(x+25,y,x+75,y);c.line(x-95,y,x-17,y,BODY)
    c.arrow((x-2,y),(x-17,y),BODY) if pmos else c.arrow((x-17,y),(x-2,y),BODY)
    c.text(x+1,y-43,name+(' P' if pmos else ' N'),17);c.text(x-49,y-46,'S' if pmos else 'D',15)
    c.text(x-49,y+53,'D' if pmos else 'S',15);c.text(x+55,y-10,'G',15)
    c.text(x-94,y-11,'B',15,BODY)
    return {'g':(x+75,y),'d':(x-30,y+(60 if pmos else -60)),
            's':(x-30,y+(-60 if pmos else 60)),'b':(x-95,y)}


def pair(kind='ideal'):
    deg=kind=='degenerated';real=kind=='mos';bridge=kind=='bridge'
    c=Canvas('差分对：两支路共享尾电流，体端独立接地',600,680 if deg else 650)
    a=c.mos(180,270,'M1');b=right_mos(c,420,270,'M2')
    c.line(210,55,390,55);c.text(300,35,'VDD',anchor='middle')
    for x in (210,390):
        c.line(x,55,x,75);c.resistor(x,75);c.line(x,151,x,210);c.node(x,185)
    c.text(125,120,'RD',18);c.text(445,120,'RD',18)
    c.wire((45,270),a['g']);c.text(35,245,'VI1',18)
    c.wire(b['g'],(555,270));c.text(520,245,'VI2',18)
    c.wire((75,185),(210,185));c.text(40,168,'VO1',18,SIGNAL)
    c.wire((390,185),(525,185));c.text(510,168,'VO2',18,SIGNAL)
    for terminal,x in ((a['b'],275),(b['b'],325)):
        c.wire(terminal,(x,300),color=BODY);c.ground(x,300,BODY)
    y=450 if deg else 390
    if bridge:
        for m,x in ((a,210),(b,390)):
            c.line(x,330,x,440);c.current(x,440,'I0');c.ground(x,524);c.node(x,365)
        c.line(210,365,262,365);c.line(338,365,390,365)
        c.parts.append('<g transform="translate(262 365) rotate(-90)">')
        c.resistor(0,0);c.parts.append('</g>');c.text(300,345,'2RS',18,anchor='middle')
        c.text(40,610,'两个独立的源端偏置；只有电阻跨接 S1、S2。',18,MUTED)
        c.save('diff-bridge',OUT)
        return
    for x in (210,390):
        if deg:
            c.line(x,330,x,345);c.resistor(x,345,'RS');c.line(x,421,x,y)
        else:c.line(x,330,x,y)
    c.line(210,y,390,y);c.node(300,y);c.text(310,y-10,'T',18,SIGNAL)
    if real:
        t=c.mos(270,485,'MT');c.line(300,y,300,425);c.ground(*t['s'])
        c.wire((110,485),t['g']);c.text(65,465,'VB 固定',18)
        c.wire(t['b'],(420,485),(420,525),color=BODY);c.ground(420,525,BODY)
        c.text(40,605,'下限：MT 需要 VDS 余量。',18,MUTED)
        c.text(40,634,'上限：M1、M2 的漏端不能低于各自饱和边界。',17,MUTED)
    else:
        c.line(300,y,300,y+30);c.current(300,y+30,'IT');c.ground(300,y+114)
        c.text(40,y+170,'B 均接地；只有两只 S 通过尾节点相连。',18,MUTED)
        if not deg:
            c.arrow((168,94),(168,143));c.text(108,91,'I1',18,SIGNAL)
            c.arrow((432,94),(432,143));c.text(451,91,'I2',18,SIGNAL)
            c.text(40,610,'VI1 ↑ → I1 ↑、T ↑ → VGS2 ↓ → I2 ↓',18,SIGNAL)
    c.save({'ideal':'diff-pair','mos':'diff-tail','degenerated':'diff-degeneration'}[kind],OUT)


def half(common=False):
    c=Canvas('共模半电路中的尾阻抗为 2RT' if common else '差模半电路：尾节点增量为零',600,470 if common else 390)
    c.text(35,34,'共模：两边流过同向增量电流' if common else '差模：交换左右后，激励变号',20,SIGNAL)
    m=c.mos(265,205,'M1')
    c.resistor(295,65,'RD');c.line(295,141,295,145)
    c.line(295,65,460,65);c.ground(460,65);c.text(445,52,'交流地',17)
    c.wire((35,205),m['g']);c.text(35,185,'vic' if common else '+vid / 2',19)
    c.wire((295,145),(485,145));c.text(450,125,'vo1',19,SIGNAL);c.node(295,145)
    c.wire(m['b'],(410,205),(410,245),color=BODY);c.ground(410,245,BODY)
    if common:
        c.line(295,265,295,285);c.resistor(295,285,'2RT');c.ground(295,361)
        c.text(325,282,'vt',18,SIGNAL);c.arrow((245,295),(245,342));c.text(215,323,'ix',18,SIGNAL)
        c.text(35,428,'真实尾电阻：vt = RT (ix + ix)。',18,MUTED)
    else:
        c.ground(295,265);c.text(335,293,'vt = 0',18,SIGNAL)
        c.text(35,350,'差模下 RT 不承受增量压差；不要求 RT → ∞。',18,MUTED)
    c.save('diff-common-half' if common else 'diff-odd-half',OUT)


def loads():
    c=Canvas('同样的 PMOS 负载，不同的栅连接决定增量电导',600,430)
    for x,title,diode in ((120,'A  二极管连接',True),(390,'B  固定栅偏置',False)):
        c.text(x-80,35,title,19)
        m=c.mos(x,190,'MP',pmos=True)
        c.wire(m['s'],(x+30,80));c.text(x+30,66,'VDD',18,anchor='middle')
        c.wire(m['b'],(x+100,190),(x+100,80),(x+30,80),color=BODY)
        c.wire(m['d'],(x+30,310));c.node(x+30,280);c.text(x+45,309,'VO',18,SIGNAL)
        if diode:
            c.wire(m['g'],(x-80,190),(x-80,280),(x+30,280));c.node(x+30,280)
        else:
            c.wire((x-90,190),m['g']);c.text(x-90,169,'VBP',18)
        c.text(x-80,370,'VSG 随 VO 改变' if diode else 'VSG 不随 VO 改变',18,SIGNAL)
    c.text(40,410,'只画一侧上拉负载；输入差分对仍在下方。',18,MUTED)
    c.save('diff-loads',OUT)


def pmos_pair():
    c=Canvas('PMOS 输入差分对：尾源在上方，体端接 VDD',600,650)
    a=c.mos(180,330,'M1',pmos=True);b=right_mos(c,420,330,'M2',True)
    t=c.mos(270,135,'MT',pmos=True)
    c.wire(t['s'],(300,55))
    c.wire((300,55),(545,55),(545,135),t['b'],color=BODY)
    c.wire(a['b'],(275,370),(325,370),b['b'],color=BODY)
    c.node(300,370,BODY);c.line(300,370,300,395,BODY)
    c.text(300,418,'VDD',17,BODY,anchor='middle')
    c.text(300,35,'VDD',19,anchor='middle')
    c.wire(t['d'],(300,210));c.line(210,210,390,210);c.node(300,210)
    c.text(300,235,'S 公共源端',17,SIGNAL,anchor='middle')
    c.wire(a['s'],(210,210));c.wire(b['s'],(390,210))
    c.wire((45,135),t['g']);c.text(40,113,'VBP',18)
    c.wire((40,330),a['g']);c.text(35,310,'VI1',18)
    c.wire(b['g'],(560,330));c.text(525,310,'VI2',18)
    for x in (210,390):
        c.line(x,390,x,450);c.resistor(x,450,'RD');c.ground(x,526);c.node(x,425)
    c.line(75,425,210,425);c.text(40,408,'VO1',18,SIGNAL)
    c.line(390,425,525,425);c.text(510,408,'VO2',18,SIGNAL)
    c.text(40,605,'VI1 ↑ → VSG1 ↓ → I1 ↓ → VO1 ↓',18,SIGNAL)
    c.save('diff-pmos',OUT)


def gilbert():
    c=Canvas('Gilbert 单元：两对电流以相反极性汇入输出',600,800)
    c.text(32,32,'同名 OL / OR 为同一网络；省去交叉长导线。',18,MUTED)
    for x,name in ((180,'OL'),(420,'OR')):
        c.text(x,65,'VDD',18,anchor='middle');c.resistor(x,85,'RD')
        c.line(x,161,x,185);c.node(x,185);c.text(x-15,210,name,19,SIGNAL)
    for x,title,names in ((40,'上差分对 A：M1、M2',('OL','OR')),(330,'上差分对 B：M3、M4',('OR','OL'))):
        c.parts.append(f'<rect x="{x}" y="290" width="230" height="130" rx="4" stroke="{MUTED}" fill="#f5f8fa"/>')
        c.text(x+115,320,title,17,anchor='middle')
        c.text(x+115,353,'G左 = VSIG+，G右 = VSIG−',15,anchor='middle')
        c.text(x+115,385,'匹配 NMOS，B 均接地',16,MUTED,anchor='middle')
        for offset,name in ((40,names[0]),(190,names[1])):
            c.line(x+offset,258,x+offset,290);c.text(x+offset,246,name,18,SIGNAL,anchor='middle')
        c.line(x+115,420,x+115,445)
    a=c.mos(125,505,'M5');b=right_mos(c,475,505,'M6')
    c.wire((155,445),a['d']);c.text(170,440,'IA',18,SIGNAL)
    c.wire((445,445),b['d']);c.text(460,440,'IB',18,SIGNAL)
    c.wire((25,505),a['g']);c.text(22,480,'VC+',18)
    c.wire(b['g'],(575,505));c.text(535,480,'VC−',18)
    for terminal,x in ((a['b'],220),(b['b'],380)):
        c.wire(terminal,(x,540),color=BODY);c.ground(x,540,BODY)
    c.wire(a['s'],(155,600),(445,600),b['s']);c.node(300,600)
    c.line(300,600,300,620);c.current(300,620,'IT');c.ground(300,704)
    c.text(30,760,'OL 收到 A左 + B右；OR 收到 A右 + B左。',18,SIGNAL)
    c.save('diff-gilbert',OUT)


if __name__=='__main__':
    for kind in ('ideal','mos','degenerated','bridge'):pair(kind)
    half();half(True);loads();pmos_pair();gilbert()
    print('Generated 9 original Chapter 4 circuit diagrams.')
