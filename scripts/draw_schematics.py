"""Generate original textbook diagrams and corrected lab schematics."""
from pathlib import Path
from circuit_art import Canvas, INK, SIGNAL, BODY, MUTED

OUT=Path(__file__).resolve().parents[1]/'模拟/图'


def sf_loading():
    """Matched low-frequency port circuits; a buffer changes the load seen upstream."""
    for buffered in (False,True):
        c=Canvas('增加缓冲级后的负载信号' if buffered else '高输出电阻直接驱动负载',360,300)
        c.text(20,27,'加一个源跟随器' if buffered else '直接接上负载',19)
        c.parts.append('<circle cx="28" cy="172" r="20"/>')
        c.text(28,179,'~',22,anchor='middle')
        c.wire((28,152),(28,104),(48,104))
        c.parts.append('<path d="M48 104h8l5 -6l8 12l8 -12l8 12l5 -6h12"/>')
        c.text(76,78,'100 kΩ',16,anchor='middle');c.line(102,104,132,104)
        c.line(28,192,28,220);c.ground(28,220)
        if buffered:
            c.parts.append('<path d="M144 72L200 104L144 136Z"/>')
            c.line(132,104,144,104);c.line(200,104,208,104)
            c.parts.append('<path d="M208 104h4l5 -6l8 12l8 -12l8 12l5 -6h10"/>')
            c.line(256,104,284,104)
            c.text(170,110,'0.8',16,anchor='middle');c.text(233,78,'1 kΩ',16,anchor='middle')
            c.text(132,164,'输入几乎不取电流',15,anchor='middle',color=MUTED)
            c.text(284,58,'72.73 mV',18,SIGNAL,anchor='middle')
        else:
            c.line(132,104,284,104);c.text(284,58,'9.09 mV',18,SIGNAL,anchor='middle')
        c.node(284,104);c.line(284,104,284,128);c.resistor(284,128,height=72)
        c.text(303,173,'10 kΩ',15);c.line(284,200,284,220);c.ground(284,220)
        c.text(20,266,'vth = 100 mV · 低频端口模型',15,MUTED)
        c.text(20,292,'负载保留 72.7% 的开路信号' if buffered else '负载只保留 9.1% 的开路信号',16,SIGNAL)
        description='同一百毫伏开路信号，一百千欧输出电阻，十千欧负载。'
        description+='加入开路增益零点八、输出电阻一千欧的缓冲级，负载信号为七十二点七三毫伏。' if buffered else '直接分压后，负载信号为九点零九毫伏。'
        c.save('sf-load-buffer' if buffered else 'sf-load-direct',OUT,description)


def sf_action():
    c=Canvas('源跟随器：输出回升减小栅源电压',600,490)
    m=c.mos(250,180)
    c.wire(m['d'],(280,55));c.text(280,35,'VDD',anchor='middle')
    c.wire((45,180),m['g']);c.text(45,160,'VI + vi')
    c.wire(m['s'],(280,280),(450,280));c.node(280,280);c.node(450,280)
    c.text(400,265,'VO + vo',color=SIGNAL)
    c.current(280,310,'IB');c.line(280,280,280,310);c.ground(280,394)
    c.resistor(450,310,'RL');c.line(450,280,450,310);c.ground(450,386)
    c.wire(m['b'],(390,180),(390,210),color=BODY);c.ground(390,210,BODY);c.text(420,199,'B = 0',17,BODY)
    c.arrow((75,220),(155,220));c.text(40,250,'vi ↑ → ID ↑',18,SIGNAL)
    c.arrow((200,280),(200,235),dash=True);c.text(35,315,'vo ↑ → vgs ↓',18,SIGNAL)
    c.text(40,455,'输入看栅端，输出看源端；体端独立接地。',18,MUTED)
    c.save('sf-action',OUT)


def sf_test():
    c=Canvas('源跟随器输出测试：保留受控源',600,460)
    c.wire((80,100),(515,100));c.text(80,80,'输出测试端：vx ↑',20,SIGNAL)
    c.arrow((55,100),(115,100));c.text(50,132,'ix',18,SIGNAL)
    for x,label in ((160,'gm vx'),(340,'gmb vx')):
        c.line(x,100,x,150);c.current(x,150,label,controlled=True);c.line(x,234,x,330)
    c.resistor(510,150,'');c.line(510,100,510,150);c.line(510,226,510,330)
    c.text(410,260,'ro ∥ rB',17)
    c.line(160,330,510,330);c.ground(340,330)
    c.text(45,385,'vi = 0，RL 已移开；原来的直流偏置仍在。',18,MUTED)
    c.text(45,420,'ix = (gm + gmb + gds + gB) vx',19,SIGNAL)
    c.save('sf-test',OUT)


def sf_equivalent():
    c=Canvas('源跟随器的诺顿与戴维南等效',600,680)
    c.text(40,35,'A  诺顿：把输入变成注入输出的电流',19,MUTED)
    c.wire((140,90),(470,90));c.wire((140,265),(470,265))
    c.current(140,125,'gm vi',controlled=True,up=True);c.line(140,90,140,125);c.line(140,209,140,265)
    c.resistor(335,125,'Rout');c.line(335,90,335,125);c.line(335,201,335,265)
    c.resistor(470,125,'RL');c.line(470,90,470,125);c.line(470,201,470,265);c.ground(335,265)
    c.text(470,73,'vo',19,SIGNAL)
    c.text(40,345,'B  戴维南：先看开路电压，再看负载分压',19,MUTED)
    c.parts.append('<g transform="translate(330 410) rotate(90)">')
    c.resistor(0,0,'');c.parts.append('</g>');c.text(265,390,'Rout',18)
    c.wire((120,410),(254,410));c.wire((330,410),(470,410))
    c.parts.append('<circle cx="120" cy="490" r="28"/>');c.line(120,410,120,462);c.line(120,518,120,590)
    c.text(120,482,'+',19,anchor='middle');c.text(120,508,'−',19,anchor='middle')
    c.text(35,650,'vth = gm Rout vi',18)
    c.resistor(470,450,'RL');c.line(470,410,470,450);c.line(470,526,470,590)
    c.line(120,590,470,590);c.ground(330,590);c.text(470,393,'vo',19,SIGNAL)
    c.save('sf-equivalent',OUT)


def laboratory():
    c=Canvas('V0 四端 NMOS 测试，B 与 S 分别接地',600,400)
    m=c.mos(245,180)
    c.wire((45,180),m['g']);c.text(40,155,'VG = 0.9 V')
    c.line(*m['d'],275,65);c.text(280,45,'VD = 1.65 V',anchor='middle')
    c.ground(*m['s']);c.wire(m['b'],(405,180),(405,260),color=BODY);c.ground(405,260,BODY)
    c.text(420,250,'B = 0',18,BODY);c.text(40,350,'W/L = 10 µm / 1 µm；D、S、B 不是同一节点。',18,MUTED)
    c.save('v0-device',OUT)
    c=Canvas('V1 电阻负载共源级，体端独立接地',600,520)
    m=c.mos(245,270)
    c.resistor(275,80,'RD = 39 kΩ');c.line(275,156,275,210);c.line(275,55,275,80);c.text(275,35,'VDD = 3.3 V',anchor='middle')
    c.wire((40,270),m['g']);c.text(40,247,'VI = 0.9 V + vi',17)
    c.wire((275,190),(460,190));c.node(275,190);c.text(440,175,'out',19,SIGNAL)
    c.cap(460,225,'CL = 2 pF');c.line(460,190,460,225);c.ground(460,285)
    c.resistor(275,350,'RS = 0 / 1 kΩ');c.line(275,330,275,350);c.ground(275,426)
    c.wire(m['b'],(400,270),(400,330),color=BODY);c.ground(400,330,BODY);c.text(420,317,'B = 0',17,BODY)
    c.save('v1-common-source',OUT)
    c=Canvas('共源级低频小信号模型',600,390)
    c.wire((90,80),(490,80));c.text(80,57,'vo',20,SIGNAL)
    c.resistor(120,130,'RD');c.line(120,80,120,130);c.line(120,206,120,300)
    c.resistor(315,130,'ro');c.line(315,80,315,130);c.line(315,206,315,300)
    c.current(490,130,'',controlled=True);c.line(490,80,490,130);c.line(490,214,490,300);c.text(440,245,'gm vi',18)
    c.line(120,300,490,300);c.ground(315,300);c.text(50,365,'S、B 均为交流地，因此 vgs = vi，vbs = 0。',18,MUTED)
    c.save('v1-small-signal',OUT)


def stage_basics():
    c=Canvas('共栅级的输入和输出端口',600,500)
    m=c.mos(250,240)
    c.resistor(280,65,'RD');c.line(280,141,280,180);c.text(280,40,'VDD',anchor='middle')
    c.wire((280,165),(470,165));c.node(280,165);c.text(445,147,'vo ↑',20,SIGNAL)
    c.wire((45,240),m['g']);c.text(40,218,'VB：交流固定',17)
    c.wire(m['s'],(280,360),(100,360));c.text(35,385,'VI + vi ↑',19,SIGNAL)
    c.wire(m['b'],(415,240),(415,290),color=BODY);c.ground(415,290,BODY)
    c.text(35,445,'源端抬高 → VGS、VBS 减小 → 漏流减小 → vo 升高',17,MUTED)
    c.save('cg-signal',OUT)
    c=Canvas('共源共栅：独立体端与中间节点',600,560)
    lower=c.mos(205,365,'M1');upper=c.mos(205,195,'M2')
    c.resistor(235,40,'负载');c.line(235,116,235,135);c.text(235,25,'VDD',17,anchor='middle')
    c.wire(upper['s'],lower['d']);c.node(235,280);c.text(255,287,'x',19,SIGNAL)
    c.wire((235,125),(480,125));c.node(235,125);c.text(440,107,'vo',20,SIGNAL)
    c.wire((35,195),upper['g']);c.text(35,175,'VB',18)
    c.wire((35,365),lower['g']);c.text(35,345,'VI + vi',18)
    c.ground(*lower['s'])
    c.wire(upper['b'],(425,195),(425,235),color=BODY);c.ground(425,235,BODY)
    c.wire(lower['b'],(425,365),(425,405),color=BODY);c.ground(425,405,BODY)
    c.text(35,490,'M2 的 B 固定，S 接中间节点 x。',18,BODY)
    c.text(35,525,'增加输出阻抗需要额外的电压余量。',18,MUTED)
    c.save('cascode',OUT)


def loads():
    c=Canvas('二极管连接与偏置固定的 PMOS 负载',600,650)
    for y,diode,title in ((170,True,'A  栅漏连接：输出一动，VSG 也变化'),(470,False,'B  栅压固定：输出主要通过 gds 改变电流')):
        c.text(30,y-125,title,18,MUTED)
        m=c.mos(245,y,'MP',pmos=True)
        c.line(*m['s'],275,y-95);c.text(275,y-105,'VDD',17,anchor='middle')
        c.wire(m['b'],(420,y),(420,y-95),color=BODY);c.text(435,y-74,'B → VDD',16,BODY)
        c.line(420,y-95,275,y-95,BODY)
        c.wire(m['d'],(275,y+90),(470,y+90));c.node(275,y+90);c.text(460,y+74,'vo',19,SIGNAL)
        if diode:c.wire(m['g'],(120,y),(120,y+90),(275,y+90));c.node(275,y+90)
        else:c.wire((70,y),m['g']);c.text(45,y-15,'VB 固定',17)
    c.save('cs-loads',OUT)


def cs_load_comparison():
    """Generate three independent full-circuit views of the frozen CS load cases."""
    cases=(
        ('resistor','电阻负载共源级增量电路','RD=10 kΩ','vo=−9.09 mV','RD +0.909 µA；go,n −0.091 µA',
         '电阻负载从 VDD 接到输出，NMOS 的 S、B 接地。输出增量为 −9.09 mV；RD 注入 +0.909 µA，NMOS 输出电导项抵消 0.091 µA。'),
        ('diode','二极管连接 PMOS 负载共源级增量电路','二极管 PMOS','vo=−1.923 mV','MP +0.981 µA；go,n −0.019 µA',
         'PMOS 的 S、B 接 VDD，G、D 接输出；NMOS 的 S、B 接地。输出增量为 −1.923 mV；PMOS 增量电流注入 +0.981 µA，NMOS 输出电导项抵消 0.019 µA。'),
        ('current','固定栅 PMOS 负载共源级增量电路','固定栅 PMOS','vo=−50.0 mV','MP +0.500 µA；go,n −0.500 µA',
         'PMOS 的 S、B 接 VDD，栅压 VB 固定，D 接输出；NMOS 的 S、B 接地。输出增量为 −50.0 mV；PMOS 注入 +0.500 µA，NMOS 输出电导项抵消 0.500 µA。'),
    )
    for kind,title,load,result,recovery,description in cases:
        c=Canvas(title,360,420)
        c.text(18,27,load+' · 共源级',18)
        c.line(95,50,265,50);c.text(180,43,'VDD',16,anchor='middle')
        if kind=='resistor':
            c.resistor(180,50,load,height=76)
            c.line(180,126,180,188)
        else:
            p=c.mos(150,115,'MP',pmos=True)
            c.line(*p['s'],180,50)
            c.line(*p['b'],265,115,color=BODY);c.line(265,115,265,50,color=BODY);c.line(265,50,180,50,color=BODY)
            c.text(270,140,'VDD',16,BODY)
            if kind=='diode':
                c.wire(p['g'],(38,115),(38,188),(180,188));c.node(180,188)
                c.text(20,100,load,16,MUTED)
            else:
                c.wire((20,115),p['g']);c.text(20,98,'VB 固定',16,SIGNAL)
        n=c.mos(150,260,'MN')
        if kind!='resistor':c.wire(p['d'],(180,188),n['d'])
        else:c.line(180,188,*n['d'])
        c.node(180,188);c.text(193,182,'vo',17,SIGNAL)
        c.wire((20,260),n['g']);c.text(20,242,'vi',16,SIGNAL)
        c.ground(*n['s']);c.line(*n['b'],n['b'][0],315,color=BODY);c.ground(n['b'][0],315,BODY)
        c.text(18,365,result,17,SIGNAL)
        c.text(18,398,recovery,16,MUTED)
        c.save('cs-load-'+kind,OUT,description)


def device():
    c=Canvas('NMOS 的概念截面：栅电场改变反型电荷',600,390)
    c.parts.append('<rect x="45" y="180" width="510" height="150" fill="#eef3f6" stroke="#6e8895"/><rect x="90" y="180" width="85" height="52" fill="#d1e9e4"/><rect x="425" y="180" width="85" height="52" fill="#d1e9e4"/>')
    c.line(175,167,425,167,BODY);c.line(175,177,425,177,BODY)
    c.parts.append('<rect x="175" y="133" width="250" height="25" fill="#d8e3eb"/>')
    c.text(300,112,'G：栅极',20,anchor='middle');c.line(300,118,300,133)
    c.text(100,153,'S',20);c.line(120,160,120,180);c.text(470,153,'D',20);c.line(470,160,470,180)
    c.text(300,288,'p 型体区 / B',20,anchor='middle');c.text(125,215,'n+',18);c.text(450,215,'n+',18)
    for x in (220,300,380):c.arrow((x,235),(x,188),SIGNAL)
    c.text(300,257,'栅压控制表面电子电荷',17,SIGNAL,anchor='middle')
    c.text(300,365,'概念截面，未按真实工艺比例绘制。',17,MUTED,anchor='middle')
    c.save('mos-section',OUT)
    c=Canvas('低频 MOS 小信号模型的两个控制电压',600,440)
    c.wire((160,85),(495,85));c.text(155,60,'D',20)
    c.wire((160,345),(495,345));c.text(155,375,'S：各控制电压的参考端',18)
    c.current(165,155,'gm vgs',controlled=True);c.line(165,85,165,155);c.line(165,239,165,345)
    c.current(350,155,'',controlled=True);c.line(350,85,350,155);c.line(350,239,350,345);c.text(302,275,'gmb vbs',18)
    c.resistor(495,155,'ro');c.line(495,85,495,155);c.line(495,231,495,345)
    c.text(25,115,'G',18);c.line(25,125,80,125);c.text(25,285,'B',18,BODY);c.line(25,295,80,295,BODY)
    c.text(25,415,'低频时 ig ≈ ib ≈ 0；受控源由 vgs、vbs 驱动。',17,MUTED)
    c.save('mos-model',OUT)


def more_stages():
    c=Canvas('共源级：从栅端输入，从漏端观察',600,410)
    m=c.mos(245,230)
    c.text(275,32,'VDD',anchor='middle');c.line(275,48,275,65);c.resistor(275,65,'RD');c.line(275,141,275,170)
    c.wire((275,155),(460,155));c.node(275,155);c.text(435,135,'vo ↓',20,SIGNAL)
    c.wire((35,230),m['g']);c.text(35,208,'VI + vi ↑',19,SIGNAL)
    c.ground(*m['s']);c.wire(m['b'],(420,230),(420,290),color=BODY);c.ground(420,290,BODY)
    c.text(430,278,'B = 0',17,BODY);c.text(35,375,'栅压升高 → 漏流增加 → RD 压降增加',18,MUTED)
    c.save('cs-principle',OUT)
    c=Canvas('互补输入共源结构：两个跨导共同作用',600,490)
    n=c.mos(220,335,'MN');p=c.mos(220,165,'MP',pmos=True)
    c.wire(p['d'],n['d']);c.node(250,250);c.wire((250,250),(480,250));c.text(455,232,'vo',20,SIGNAL)
    c.wire(n['g'],(90,335),(90,165),p['g']);c.wire((35,250),(90,250));c.node(90,250);c.text(35,230,'vi',20,SIGNAL)
    c.wire(p['s'],(250,55));c.text(250,35,'VDD',anchor='middle');c.ground(*n['s'])
    c.wire(p['b'],(425,165),(425,55),(250,55),color=BODY)
    c.wire(n['b'],(425,335),(425,395),color=BODY);c.ground(425,395,BODY)
    c.text(35,455,'vi ↑：NMOS 多吸电流，PMOS 少供电流。',18,MUTED)
    c.save('inverter-stage',OUT)
    c=Canvas('折叠共源共栅的电流分配',600,560)
    n=c.mos(110,335,'MN');p=c.mos(350,290,'PF',pmos=True)
    c.current(140,100,'IB');c.line(140,60,140,100);c.line(140,184,140,230)
    c.wire(n['d'],(140,230),p['s']);c.node(140,230);c.text(235,214,'x：IB = I1 + IF',18,SIGNAL)
    c.text(140,35,'VDD',anchor='middle');c.text(400,254,'IF',18,SIGNAL)
    c.wire((15,335),n['g']);c.text(15,312,'vi',19,SIGNAL);c.ground(*n['s'])
    c.wire(n['b'],(245,335),(245,385),color=BODY);c.ground(245,385,BODY)
    c.wire(p['b'],(515,290),(515,60),(140,60),color=BODY)
    c.wire((225,290),p['g']);c.text(225,270,'VB',18)
    c.wire(p['d'],(380,390),(520,390));c.node(380,390);c.text(495,372,'vo',19,SIGNAL)
    c.current(380,420,'I0');c.line(380,390,380,420);c.ground(380,504)
    c.text(45,505,'I1',18,SIGNAL);c.arrow((80,425),(80,465),SIGNAL)
    c.save('folded-cascode',OUT)


def capacitances():
    c=Canvas('MOS 电容涉及的四个端口',600,460)
    g,d,s,b=(75,220),(320,55),(320,385),(530,220)
    for a,z in ((g,d),(g,s),(g,b),(d,b),(s,b)):c.cap_between(a,z)
    for (x,y),label in ((g,'G'),(d,'D'),(s,'S'),(b,'B')):c.node(x,y,BODY if label=='B' else INK)
    c.text(40,225,'G',22);c.text(320,30,'D',22,anchor='middle');c.text(320,423,'S',22,anchor='middle');c.text(549,225,'B',22,BODY)
    for x,y,label in ((160,110,'Cgd'),(150,345,'Cgs'),(265,198,'Cgb'),(438,120,'Cdb'),(445,340,'Csb')):c.text(x,y,label,19)
    c.text(300,450,'端口位置示意；完整紧凑模型使用电荷偏导矩阵。',16,MUTED,anchor='middle')
    c.save('mos-capacitances',OUT)


if __name__=='__main__':
    sf_loading();sf_action();sf_test();sf_equivalent();laboratory();stage_basics();loads();cs_load_comparison();device();more_stages();capacitances()
    print('Generated original teaching schematics with explicit bulk terminals.')
