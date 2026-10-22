"""Original Chapter 5 schematics; explicit bulk nets and named bias connections."""
from pathlib import Path
from circuit_art import Canvas, SIGNAL, BODY, MUTED
from draw_differential import right_mos
OUT=Path(__file__).resolve().parents[1]/'模拟/图'


def grounded(c, device, body_y):
    c.line(*device['b'],device['b'][0],body_y,color=BODY)
    c.ground(device['b'][0],body_y,BODY)


def basic():
    c=Canvas('普通 NMOS 电流镜：参考端建立栅压，输出端需要自己的余量',620,450)
    a=c.mos(140,250,'M1'); b=c.mos(450,250,'M2')
    c.current(170,45,'IREF');c.line(170,129,170,190);c.node(170,170)
    c.wire(a['g'],(40,250),(40,170),(350,170),(350,250),b['g'])
    c.line(170,170,350,170);c.text(250,150,'VB',19,SIGNAL)
    c.line(480,70,480,190);c.node(480,70);c.text(495,75,'VO',19,SIGNAL)
    for m in (a,b):c.ground(*m['s']);grounded(c,m,290)
    c.arrow((535,105),(535,150));c.text(548,112,'IO',18,SIGNAL)
    c.text(115,28,'参考电流进入',18);c.text(40,395,'D1 与 G1 相连；两只 B 均独立接地。',18,MUTED)
    c.save('mirror-basic',OUT)


def cascode():
    c=Canvas('自偏置共源共栅电流镜：同构参考支路保护内部节点',620,610)
    devices=[]
    for x,low,up in ((140,'M1','M3'),(450,'M2','M4')):
        a=c.mos(x,440,low);b=c.mos(x,240,up);devices.extend((a,b))
        c.line(x+30,300,x+30,380);c.ground(*a['s']);grounded(c,a,480);grounded(c,b,280)
    c.current(170,25,'IREF');c.line(170,109,170,180)
    c.wire((65,240),(40,240),(40,145),(340,145),(340,240),(375,240));c.line(170,145,170,180);c.node(170,145)
    c.wire((65,440),(40,440),(40,350),(340,350),(340,440),(375,440));c.node(170,350)
    c.line(480,65,480,180);c.node(480,65);c.text(495,70,'VO',19,SIGNAL)
    c.node(480,350);c.text(495,355,'X',20,SIGNAL)
    c.text(250,125,'VC',18,SIGNAL);c.text(250,330,'VB',18,SIGNAL)
    c.text(38,575,'低压时先检查 M4：VO − VX ≥ VDSAT4。',18,MUTED)
    c.save('mirror-cascode',OUT)


def ota():
    c=Canvas('电流镜有源负载的五管 OTA 核心；参考网络单独绘出',620,700)
    a=c.mos(180,350,'M1');b=right_mos(c,420,350,'M2')
    p=c.mos(180,150,'M3',True);q=right_mos(c,420,150,'M4',True)
    c.line(210,75,390,75);c.line(210,75,210,90);c.line(390,75,390,90);c.text(300,70,'VDD',18,anchor='middle')
    for x in (210,390):c.line(x,210,x,290)
    # Route the mirror gate above the supply rail, without crossing drain wires.
    c.wire(p['g'],(60,150),(60,250),(210,250));c.node(210,250)
    c.wire((60,150),(60,35),(560,35),(560,150),q['g'])
    c.text(300,25,'镜像栅节点 X',18,SIGNAL,anchor='middle')
    for m in (p,q):
        c.line(*m['b'],m['b'][0],185,color=BODY);c.text(m['b'][0],207,'VDD',15,BODY,anchor='middle')
    for m in (a,b):grounded(c,m,390)
    c.wire((35,350),a['g']);c.text(32,330,'VI1',18)
    c.wire(b['g'],(570,350));c.text(535,330,'VI2',18)
    c.wire((390,250),(510,250));c.node(390,250);c.text(510,240,'VO',20,SIGNAL)
    c.text(180,270,'X',19,SIGNAL)
    for x in (210,390):c.line(x,410,x,450)
    c.line(210,450,390,450);c.node(300,450);c.text(310,440,'T',18,SIGNAL)
    t=c.mos(270,550,'MT');c.line(300,450,300,490);c.ground(*t['s']);grounded(c,t,590)
    c.wire((100,550),t['g']);c.text(55,525,'VB ← 参考支路',18,SIGNAL)
    c.arrow((445,90),(445,125));c.text(465,115,'I4',18,SIGNAL)
    c.arrow((445,275),(445,310));c.text(465,300,'I2',18,SIGNAL)
    c.text(35,680,'输出注入电流 = I4 − I2；M3、M4 的 B 接 VDD。',18,MUTED)
    c.save('mirror-ota',OUT)


def reference():
    c=Canvas('电阻参考支路与各级偏置：同名 VB 是电气连接',620,470)
    r=c.mos(140,300,'MR');c.resistor(170,60,'RREF');c.line(170,136,170,240);c.text(170,40,'VDD',18,anchor='middle')
    c.node(170,195);c.wire(r['g'],(40,300),(40,195),(170,195),(360,195));c.text(310,175,'VB',20,SIGNAL)
    c.ground(*r['s']);grounded(c,r,340)
    c.text(380,185,'→ 尾管 MT 的栅极',19);c.text(380,225,'→ 共源级电流源',19);c.text(380,265,'→ 源跟随器负载',19)
    c.text(35,425,'分配的是栅偏置；每个支路仍须检查 VDS 与体偏置。',18,MUTED)
    c.save('mirror-bias',OUT)


def small_signal():
    c=Canvas('共源共栅电流源的测试端口与内部节点 KCL',580,360)
    c.line(120,70,465,70);c.text(480,76,'vx',19,SIGNAL);c.node(430,70)
    c.line(120,70,120,100);c.current(120,100,'−(gm4+gmb4) vy',True)
    c.line(120,184,120,220);c.line(120,220,430,220);c.node(300,220);c.text(315,213,'vy',19,SIGNAL)
    c.line(430,70,430,100);c.resistor(430,100,'ro4');c.line(430,176,430,220)
    c.line(300,220,300,235);c.resistor(300,235,'ro2');c.ground(300,311)
    c.text(35,32,'偏置电压交流固定；受控源正方向向下。',18,MUTED)
    c.save('mirror-cascode-small',OUT)


def self_bias():
    c=Canvas('Beta 倍增器的偏置关系：非零电流解与零电流解',620,670)
    n1=c.mos(180,380,'N1');n2=right_mos(c,420,380,'N2')
    p1=c.mos(180,160,'P1',True);p2=right_mos(c,420,160,'P2',True)
    c.line(210,80,390,80);c.line(210,80,210,100);c.line(390,80,390,100);c.text(300,60,'VDD',19,anchor='middle')
    for x in (210,390):c.line(x,220,x,320)
    c.wire(n1['g'],(60,380),(60,280),(210,280));c.node(210,280);c.text(70,262,'VB',18,SIGNAL)
    c.wire(n2['g'],(560,380));c.text(530,360,'VB',18,SIGNAL)
    c.wire(p2['g'],(560,160),(560,260),(390,260));c.node(390,260);c.text(530,140,'VP',18,SIGNAL)
    c.wire(p1['g'],(60,160));c.text(35,140,'VP',18,SIGNAL)
    for m in (p1,p2):
        c.line(*m['b'],m['b'][0],195,color=BODY);c.text(m['b'][0],215,'VDD',14,BODY,anchor='middle')
    for m in (n1,n2):grounded(c,m,425)
    c.ground(*n1['s']);c.line(390,440,390,480);c.resistor(390,480,'R');c.ground(390,556)
    c.text(95,485,'β1 = β',18);c.text(420,470,'β2 = Kβ',18)
    c.text(35,625,'同名 VB、VP 是连线；P2 二极管连接，N1 二极管连接。',17,MUTED)
    c.text(35,652,'启动支路未画出：需要打破零电流解，再在正常偏置后退出。',17,MUTED)
    c.save('mirror-self-bias',OUT)


if __name__=='__main__':
    basic();cascode();ota();reference();small_signal();self_bias()
