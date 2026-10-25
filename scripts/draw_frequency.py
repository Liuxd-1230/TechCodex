"""Original Chapter 6 dynamic-path diagrams using the shared four-terminal symbols."""
from pathlib import Path
from circuit_art import Canvas,SIGNAL,BODY,MUTED
from draw_mirrors import grounded
OUT=Path(__file__).resolve().parents[1]/'模拟/图'


def cs():
    c=Canvas('共源级的两个动态节点：Cgd 跨接输入与输出，源极与体端接地',680,440)
    m=c.mos(290,265,'M1');c.ground(*m['s']);grounded(c,m,305)
    c.line(35,265,90,265);c.wire((90,265),(98,255),(110,275),(122,255),(134,275),(146,255),(154,265),(215,265))
    c.text(103,240,'RS',17);c.text(25,295,'vin',19)
    c.line(190,265,190,120);c.cap_between((190,120),(320,120));c.line(320,120,320,205)
    c.text(237,98,'Cgd',19,SIGNAL)
    c.line(320,175,540,175);c.node(320,175);c.node(190,265)
    c.line(320,45,320,120);c.text(320,32,'VO',19,SIGNAL,anchor='middle')
    c.text(355,70,'RD / 电流源负载',18)
    c.line(190,265,190,295);c.cap(190,295,'Cgs');c.ground(190,355)
    c.cap(540,220,'CO');c.line(540,175,540,220);c.ground(540,280)
    c.text(175,285,'vg',18,SIGNAL);c.arrow((210,155),(285,155));c.text(380,140,'iC = sCgd(vg − vo)',18,SIGNAL)
    c.text(30,410,'CO 含输出结电容与 CL；负载电阻接交流地，图上方省略直流负载。',16,MUTED)
    c.save('frequency-cs',OUT)


def small():
    c=Canvas('共源级完整两节点小信号电路：所有电容均与方程逐项对应',680,390)
    c.text(20,40,'vin → RS → vg',20);c.text(455,40,'vo',20,SIGNAL)
    c.wire((25,90),(60,90),(70,80),(82,100),(94,80),(106,100),(118,80),(130,90),(170,90))
    c.text(75,65,'RS',18);c.node(170,90);c.line(170,90,170,140);c.cap(170,140,'Ci');c.ground(170,200)
    c.cap_between((170,90),(475,90));c.text(300,65,'Cf = Cgd',19,SIGNAL);c.node(475,90)
    c.line(475,90,610,90);c.line(610,90,610,140);c.cap(610,140,'Co');c.ground(610,200)
    c.line(475,90,475,140);c.resistor(475,140,'Ro');c.ground(475,216)
    c.current(350,140,'gm vg',True);c.ground(350,224)
    c.wire((475,115),(350,115),(350,140));c.node(475,115)
    c.text(25,320,'Ci = Cgs + 外接输入电容；Co = Cdb + CL。',18,MUTED)
    c.text(25,352,'输出受控源向下；Cf 的位移电流提供另一条输入到输出的路径。',17,MUTED)
    c.save('frequency-cs-small',OUT)
    file=OUT/'frequency-cs-small.svg'
    file.write_text(file.read_text(encoding='utf-8').replace('TechCodex original teaching schematic. D, G, S, B are explicitly distinguished. Colored arrows show perturbations, not wires.','Original two-node small-signal circuit: input through RS to gate node, Ci to ground, Cf between gate and output. Output has Ro and Co to ground, and a downward controlled current gm times vg.'),encoding='utf-8',newline='\n')


def output_port():
    c=Canvas('漏端测试中的两种栅端约束：固定电压与电容分压',680,630)
    for offset,floating in [(0,False),(310,True)]:
        c.text(26,offset+35,'② 栅前开路：电容分压驱动跨导' if floating else '① RS → 0：栅节点固定在交流地',22)
        c.wire((225,offset+170),(225,offset+110))
        c.cap_between((225,offset+110),(480,offset+110))
        c.text(310,offset+91,'Cf = Cgd',20,SIGNAL)
        c.wire((225,offset+170),(225,offset+190));c.cap(225,offset+190,'Ci')
        c.ground(225,offset+250);c.node(225,offset+170)
        c.wire((480,offset+110),(600,offset+110));c.node(480,offset+110)
        c.text(613,offset+117,'vt',21,SIGNAL)
        c.arrow((595,offset+67),(520,offset+67));c.text(550,offset+53,'it',19,SIGNAL)
        c.wire((480,offset+110),(480,offset+150))
        c.current(480,offset+150,'gm vg',controlled=True);c.ground(480,offset+234)
        c.text(245,offset+176,'vg = α vt' if floating else 'vg = 0',21,SIGNAL)
        c.text(55,offset+145,'RS → ∞' if floating else 'RS → 0',18,MUTED)
        c.ground(95,offset+170)
        if floating:
            c.line(95,offset+170,125,offset+170);c.line(155,offset+170,225,offset+170)
            for x in (125,155):
                c.parts.append(f'<circle cx="{x}" cy="{offset+170}" r="3" fill="white"/>')
        else:c.line(95,offset+170,225,offset+170)
        c.text(26,offset+295,'栅随漏动：同相漏流 gm α vt 形成等效电导。' if floating else '漏端给 Cf 充放电；跨导增量电流为零。',18,SIGNAL if floating else MUTED)
    c.line(26,310,654,310,color='#d5e0e8')
    c.save('frequency-cs-output-port',OUT,description='Original linear circuit comparison with the input generator set to zero. Each drain test port connects to Cf and a downward gm vg current source. Ci connects the gate to ground. Top: the gate is shorted to AC ground. Bottom: the source-resistance branch is open, allowing capacitive division vg = Cf/(Ci+Cf) times vt. Ro and Co are omitted here and remain parallel at the drain in the full circuit. The oxide is not a conducting connection.')


def paths():
    for name in ('sf','cg'):
        c=Canvas('源跟随器的跨端电容' if name=='sf' else '共栅级的跨端电容',640,460)
        m=c.mos(300,225,'M1');grounded(c,m,265)
        c.line(330,165,330,95);c.node(330,115)
        c.text(350,100,'VDD（交流地）' if name=='sf' else 'vo → RD → VDD',18)
        c.line(330,285,330,340);c.node(330,320)
        c.text(345,355,'vo → 偏置电流源' if name=='sf' else 'vi ← 信号源',18)
        c.line(140,225,225,225);c.node(180,225)
        c.text(25,230,'vg ← RS' if name=='sf' else 'VB（交流固定）',17)
        c.wire((180,225),(180,320));c.cap_between((180,320),(330,320));c.text(230,300,'Cgs',19,SIGNAL)
        c.line(180,225,180,115);c.cap_between((180,115),(330,115));c.text(230,92,'Cgd',19,SIGNAL)
        target=320 if name=='sf' else 115
        c.line(330,target,535,target);c.line(535,target,535,target+20);c.cap(535,target+20,'CL');c.ground(535,target+80)
        c.text(30,440,'图中只显式画 Cgs、Cgd、CL；结电容与负载输出阻抗在方程中保留。',16,MUTED)
        c.save('frequency-'+name,OUT)
    c=Canvas('共源共栅：下管 Cgd 跨接输入与内部节点 X',640,560)
    a=c.mos(300,385,'M1');b=c.mos(300,165,'M2')
    c.ground(*a['s']);grounded(c,a,425);grounded(c,b,205)
    c.line(330,225,330,325);c.node(330,275);c.text(350,280,'X',21,SIGNAL)
    c.wire((80,385),a['g']);c.text(40,365,'vg ← RS',18)
    c.wire((80,165),b['g']);c.text(40,145,'VB（交流固定）',18)
    c.line(180,385,180,275);c.cap_between((180,275),(330,275));c.text(225,250,'Cgd1',18,SIGNAL)
    c.line(330,45,330,105);c.node(330,60);c.text(350,42,'vo → RD → VDD',18)
    c.wire((330,60),(535,60),(535,90));c.cap(535,90,'CO');c.ground(535,150)
    c.text(30,520,'X 的总电容包含 Cdb1、Cgs2、Csb2；并非没有动态节点。',17,MUTED)
    c.save('frequency-cascode',OUT)


def ota():
    # Reuse the exact Chapter 5 original; add an explicit load and dynamic labels.
    from draw_mirrors import ota as original
    original()
    svg=(OUT/'mirror-ota.svg').read_text(encoding='utf-8')
    addition='<g fill="none" stroke="#127b70" stroke-width="1.8"><path d="M510 250H570V410M555 410H585M555 418H585M570 418V465M557 465H583M562 472H578M567 479H573"/></g><text x="590" y="424" fill="#127b70" font-size="19">CL</text>'
    svg=svg.replace('</svg>',addition+'</svg>').replace('TechCodex original teaching schematic.', 'X: diode-connected mirror node; O: high impedance output with CL; T: common source; B: real reference network in the companion figure. Quasi-static capacitances also couple these nodes. TechCodex original teaching schematic.')
    (OUT/'frequency-ota.svg').write_text(svg,encoding='utf-8',newline='\n')


if __name__=='__main__':cs();small();output_port();paths();ota()
