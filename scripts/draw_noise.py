"""Original noise paths, using shared explicit four-terminal MOS vocabulary."""
from pathlib import Path
from circuit_art import Canvas,INK,SIGNAL,BODY,MUTED
from draw_mirrors import grounded
OUT=Path(__file__).resolve().parents[1]/'模拟/图';BLUE='#315bc5'


def referral():
    c=Canvas('内部噪声经各自传递函数到输出，统一用信号端口增益折回输入',720,335)
    for x,y,w,h in [(260,55,155,60),(260,190,155,60),(540,110,140,80)]:
        c.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>')
    c.text(338,93,'Av(f)',22,anchor='middle');c.text(338,228,'Hk(f)',22,anchor='middle');c.text(610,143,'同一输出',18,anchor='middle');c.text(610,174,'Sv,o(f)',20,BLUE,anchor='middle')
    c.arrow((80,85),(250,85),INK);c.text(90,60,'信号 vi',20)
    c.arrow((80,220),(250,220),BLUE);c.text(90,195,'内部源 nk',20,BLUE)
    c.wire((415,85),(490,85),(490,150),(530,150));c.arrow((490,150),(535,150),INK)
    c.wire((415,220),(490,220),(490,150),color=BLUE);c.node(490,150)
    c.text(55,303,'输入参考：Sv,in(f) = Sv,o(f) / |Av(f)|²',22,SIGNAL)
    c.save('noise-referral',OUT)


def cg():
    c=Canvas('共栅沟道噪声为漏源之间的同一电流，源节点移动产生局部抵消',680,455)
    m=c.mos(255,205,'M1');grounded(c,m,250)
    c.wire(m['g'],(70,205),(70,235));c.ground(70,235);c.text(25,185,'G: AC ground',16)
    c.resistor(285,40,'RD');c.line(285,116,285,145);c.text(285,25,'VDD: AC ground',17,anchor='middle');c.node(285,130);c.text(308,142,'vo',20,SIGNAL)
    c.wire(m['s'],(285,340));c.node(285,340);c.text(305,370,'vx',20,SIGNAL)
    c.wire((40,340),(80,340),(90,330),(102,350),(114,330),(126,350),(138,330),(150,340),(285,340));c.text(96,309,'Rs',19);c.text(24,377,'vs',20)
    c.wire((285,130),(495,130),(495,165),color=BLUE);c.current(495,165,'in',up=False);c.wire((495,249),(495,340),(285,340),color=BLUE)
    c.text(365,410,'同一源：漏端 −in，源端 +in',18,BLUE,anchor='middle');c.text(30,442,'ro 忽略；体端接交流地，gm + gmb 同时参与源端反馈。',16,MUTED)
    c.save('noise-cg',OUT)


def cascode():
    c=Canvas('共源共栅的上管噪声沿漏源两端注入，中间节点反馈使输出贡献减小',680,550)
    a=c.mos(260,400,'M1');b=c.mos(260,160,'M2')
    c.ground(*a['s']);grounded(c,a,440);grounded(c,b,200)
    c.wire(a['g'],(55,400));c.text(35,373,'vi',20,SIGNAL)
    c.wire(b['g'],(75,160),(75,185));c.ground(75,185);c.text(25,137,'VB: AC ground',16)
    c.wire((290,220),(290,340));c.node(290,280);c.text(310,285,'vx',20,SIGNAL)
    c.line(290,100,290,60);c.node(290,70);c.text(310,55,'vo → load GD',18)
    c.wire((290,70),(500,70),(500,130),color=BLUE);c.current(500,130,'in2');c.wire((500,214),(500,280),(290,280),color=BLUE)
    c.text(385,318,'M2 的源端注入',17,BLUE);c.text(385,346,'推动 vx → 反馈到漏端',17,BLUE)
    c.text(30,523,'低频抑制因子：go1 / (gm2 + gmb2 + go2)；两管体端均交流接地。',17,MUTED)
    c.save('noise-cascode',OUT)


if __name__=='__main__':referral();cg();cascode()
