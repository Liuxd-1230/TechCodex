"""Static charge and port examples; analytical values, not GF180 measurements."""
from pathlib import Path
import numpy as np
from circuit_art import Canvas, INK, SIGNAL, MUTED, BODY
from check_teaching import solve

OUT = Path(__file__).resolve().parents[1] / '模拟/图'


def charge_increment():
    c = Canvas('同样增加栅压，为什么需要补充的电荷不同', 480, 680)
    c.text(22, 30, '多补多少电荷，才是电容的问题', 23)
    c.text(22, 58, '绿线与灰线之间：新增的电荷', 19, SIGNAL)
    for top, saturated in ((82, False), (362, True)):
        c.text(22, top, '饱和：漏端仍处于夹断边界以外' if saturated else 'VDS = 0：沟道电荷均匀', 21)
        bottom = top + 172
        shape = lambda u: np.sqrt(1-u) if saturated else np.ones_like(u)
        u = np.linspace(0, 1, 201)
        x = 76 + 352*u
        old = bottom - .4*shape(u)*300
        new = bottom - .44*shape(u)*300
        def polygon(xs, ys, fill):
            points = ' '.join(f'{a:.2f},{b:.2f}' for a,b in zip(xs, ys))
            c.parts.append(f'<polygon points="{points}" fill="{fill}" stroke="none"/>')
        polygon(np.r_[76, x, 428], np.r_[bottom, old, bottom], '#eff4f8')
        polygon(np.r_[x, x[::-1]], np.r_[old, new[::-1]], '#c4e3db')
        for ys,color in ((old, MUTED),(new,SIGNAL)):
            points = ' '.join(f'{a:.2f},{b:.2f}' for a,b in zip(x,ys))
            c.parts.append(f'<polyline points="{points}" stroke="{color}"/>')
        c.wire((76,top+22),(76,bottom),(428,bottom))
        c.text(82,top+27,'|Qi| / Cox',18)
        c.text(62,bottom+6,'0',18,anchor='end')
        c.text(76,bottom+25,'S · x = 0',18)
        c.text(428,bottom+25,'D · x = L',18,anchor='end')
        c.text(22,bottom+60,'ΔQg = ⅔ WLCox ΔVG' if saturated else 'ΔQg = WLCox ΔVG',22,SIGNAL)
    c.text(22,636,'VOV：0.40 → 0.44 V；栅压增加 40 mV。',19,MUTED)
    c.text(22,665,'纵轴单位 V；电荷为长沟道解析值。',19,MUTED)
    c.save('mos-charge-increment',OUT,
           '解析长沟道准静态模型，源体固定。上图漏源电压为零，下图漏压固定且在两次栅压下均保持饱和。栅过驱动从0.40增至0.44伏。绿色条带的面积乘以WCox得到新增栅反型电荷；分别为WLCox乘40毫伏与其三分之二。不包含耗尽、重叠及边缘电荷。')
    # Numerical integration is independent of the symbolic 2/3 coefficient.
    u = np.linspace(0,1,100001)
    assert np.isclose(np.trapezoid(np.sqrt(1-u),u),2/3,rtol=5e-8)
    assert np.isclose(np.trapezoid(np.ones_like(u),u),1)


def cg_termination():
    c = Canvas('同一共栅工作点，漏端终接改变输入电流',480,720)
    c.text(22,30,'源端同样抬高 1 mV，电流却不同',22)
    for shift, opened in ((55,False),(385,True)):
        c.parts.append(f'<g transform="translate(0 {shift})">')
        c.text(22,20,'漏端交流开路' if opened else '漏端交流短接',22)
        m=c.mos(210,145,'M')
        c.wire(m['d'],(240,65),(420,65))
        if opened:
            c.parts.append('<circle cx="420" cy="65" r="5" fill="white"/>')
        else:
            c.ground(420,65)
        c.text(270,48,'vo = +101 mV' if opened else 'vo = 0',20,SIGNAL)
        c.wire(m['g'],(70,145),(70,190));c.ground(70,190)
        c.text(22,126,'vg = 0',18)
        c.wire(m['b'],(390,145),(390,190),color=BODY);c.ground(390,190,BODY)
        c.text(325,232,'vb = 0',18,BODY)
        c.wire(m['s'],(240,250),(75,250));c.node(240,250)
        c.arrow((90,250),(145,250))
        c.text(22,278,'vi = +1 mV',20,SIGNAL)
        c.text(230,278,'ii = 0' if opened else 'ii = +1.01 µA',20,SIGNAL)
        c.text(22,310,'Rin → ∞' if opened else 'Rin = 0.990 kΩ',20)
        c.parts.append('</g>')
    c.save('cg-termination',OUT,
           '固定工作点的低频增量对照，gm加gmb等于1毫西门子，ro等于100千欧，栅体交流固定。上图漏端交流短接，源端注入1毫伏，输入电流1.01微安；下图只将漏端改为交流开路，漏端上升101毫伏，输入电流为零。直流偏置路径均在增量图之外。')
    gt,go,vi=1e-3,1e-5,1e-3
    for rd in (0,1e4,1e5):
        vo=(gt+go)*vi/(1/rd+go) if rd else 0
        ii=(gt+go)*vi-go*vo
        assert np.isclose(vi/ii,(1+go*rd)/(gt+go))
    assert np.isclose((gt+go)*vi-go*((gt+go)*vi/go),0,atol=1e-20)
    # Stamp the MOS terminals independently of the port expression.
    opened=solve(['d'],{'s':vi,'0':0},[('d','0','s','0',gt,0,go)])
    assert np.isclose(opened['d'],.101)
    assert np.isclose((gt+go)*vi-go*opened['d'],0,atol=1e-20)


def cascode_feedback():
    c=Canvas('共源共栅输出测试：中间节点使两种电流变化相抵',480,610)
    c.text(22,30,'输出抬高，支路电流为何只变一点',22)
    m=c.mos(185,180,'M2')
    c.wire(m['d'],(215,85),(432,85));c.node(215,85)
    c.text(432,65,'vo = +100 mV',21,SIGNAL,anchor='end')
    c.wire(m['g'],(55,180),(55,215));c.ground(55,215)
    c.text(22,152,'vg2 = 0',18)
    c.wire(m['b'],(365,180),(365,215),color=BODY);c.ground(365,215,BODY)
    c.text(340,267,'vb2 = 0',18,BODY)
    c.wire(m['s'],(215,280),(350,280));c.node(215,280)
    c.text(246,310,'vx = +0.980 mV',20,SIGNAL)
    c.line(215,280,215,325);c.resistor(215,325);c.ground(215,401)
    c.text(245,373,'ro1 = 100 kΩ',18)
    c.arrow((172,323),(172,382));c.text(22,345,'ix =',19,SIGNAL)
    c.text(22,374,'+9.80 nA',20,SIGNAL)
    c.text(22,467,'ro2 路径：+0.990 µA',21)
    c.text(22,501,'−gt2 vx：−0.980 µA',21,SIGNAL)
    c.text(22,538,'净变化仅 +0.00980 µA',22,SIGNAL)
    c.text(22,582,'Rcas = 10.2 MΩ；单管 ro1 仅 0.1 MΩ。',19)
    c.save('cascode-feedback',OUT,
           '已置零输入的两管共源共栅增量模型。M1只剩ro1，M2栅体交流接地。gt2为1毫西门子，ro1与ro2均100千欧。输出测试100毫伏使中间节点上升0.980392毫伏，M2输出电导项增加0.990196微安，跨导项减少0.980392微安，净向下电流9.80392纳安。')
    # Independent simultaneous KCL solve in unknowns vx and ix.
    gt,ro,vo=1e-3,1e5,.1
    vx,ix=np.linalg.solve([[1,-ro],[gt+1/ro,1]],[0,vo/ro])
    assert np.isclose(vo/ix,2*ro+gt*ro*ro)
    assert np.isclose(vx,.000980392156862745)
    assert np.isclose(ix,9.80392156862745e-9)
    assert np.isclose((vo-vx)/ro-gt*vx,ix)
    pair=[('x','0','0','0',gt,0,1/ro),('o','0','x','0',gt,0,1/ro)]
    stamped=solve(['x'],{'0':0,'o':vo},pair)
    assert np.isclose(stamped['x'],vx)


if __name__=='__main__':
    charge_increment();cg_termination();cascode_feedback()
    print('Generated 3 analytical charge/port figures; integral and KCL checks passed.')
