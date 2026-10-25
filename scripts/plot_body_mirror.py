"""Two teaching examples: archived GF180 evidence and separate analytic phasors.

Run with the repository's scientific Python environment. No simulation or fitting.
"""
from pathlib import Path
from html import escape
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from circuit_art import Canvas, SIGNAL, BODY, MUTED, INK

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'模拟/图'
DATA=ROOT/'模拟/实验/data'
AC=ROOT/'模拟/实验/频率响应/data'
BLUE='#315bc5'


def read_evidence():
    body=np.loadtxt(DATA/'body.csv',delimiter=',',skiprows=1)
    output=np.loadtxt(DATA/'output-Vg0.9.csv',delimiter=',',skiprows=1)
    ac=np.loadtxt(AC/'ota-1p-ac.csv',delimiter=',',skiprows=1)
    assert body.shape==(81,5) and output.shape==(331,3) and ac.shape==(801,9)
    return body,output,ac


def verify(body,output,ac):
    assert np.all(np.diff(body[:,4])>0) and np.all(np.diff(body[:,1])<0)
    # Differentiate the stored terminal sweep independently of the model gmb.
    slope=np.gradient(body[:,1],body[:,0],edge_order=2)
    np.testing.assert_allclose(-slope[1:-1],body[1:-1,3],rtol=6e-4)
    q=165
    fd=(output[q+1,1]-output[q-1,1])/(output[q+1,0]-output[q-1,0])
    np.testing.assert_allclose(fd,output[q,2],rtol=2e-6)
    # Solve the two original node equations, independently of the factored H.
    for r in np.r_[0,np.logspace(-3,3,61)]:
        s=1j*r;gn,gp,cx,go,co=2.,1.,1.,.1,2.
        vx,vo=np.linalg.solve([[gp+s*cx,0],[gp,go+s*co]],[-gn/2,gn/2])
        mirror=1/(1+1j*r)
        np.testing.assert_allclose(-gp*vx,mirror,rtol=1e-12)
        h=gn/go*(1+s/2)/((1+s)*(1+s*co/go))
        np.testing.assert_allclose(vo,h,rtol=1e-12)
    # Printed phasor values and the separate hypothetical DIBL example.
    np.testing.assert_allclose(abs(1+1/(1+1j)),np.sqrt(2.5))
    np.testing.assert_allclose(abs(1+1/(1+10j)),np.sqrt(104/101))
    np.testing.assert_allclose(np.exp(.02*.5/.04),1.2840254166877414)
    # Archived voltage response at exactly the frequency discussed in the text.
    one=ac[np.flatnonzero(ac[:,0]==1e6)[0]]
    np.testing.assert_allclose(abs(one[3]+1j*one[4]),1.784195,rtol=1e-6)
    record=json.loads((AC/'nodal.json').read_text(encoding='utf-8'))
    g=np.array(record['G_S']);cap=np.array(record['C_F']);cap[1,1]+=1e-12
    b0=np.array(record['input_0_S']);b1=np.array(record['input_1_F'])
    rows=ac[ac[:,0]<=30e6]
    for row in rows:
        s=2j*np.pi*row[0]
        stamped=np.linalg.solve(g+s*cap,b0+s*b1)
        archived=np.array([row[3]+1j*row[4],row[1]+1j*row[2],row[5]+1j*row[6],row[7]+1j*row[8]])
        np.testing.assert_allclose(stamped,archived,rtol=1e-7,atol=1e-10)
    print(f'PASS: body-current derivative, output slope, 62 analytic solutions; archived X/O/T/B agree with nodal reconstruction at {len(rows)} frequencies.')


def save(fig,name,description):
    path=OUT/(name+'.svg')
    fig.savefig(path,metadata={'Date':None},facecolor='white')
    svg=path.read_text(encoding='utf-8');end=svg.index('>',svg.index('<svg'))
    svg=svg[:end]+f' role="img" aria-labelledby="{name}-title {name}-desc"'+svg[end:]
    end=svg.index('>',svg.index('<svg'))+1
    svg=svg[:end]+f'<title id="{name}-title">{escape(description)}</title><desc id="{name}-desc">归档 GF180MCU 仿真，typical、27 °C；坐标单位与正文图注对应。</desc>'+svg[end:]
    path.write_text(svg,encoding='utf-8',newline='\n')
    plt.close(fig)


def body_port():
    c=Canvas('体效应扫描：移动源端，保持栅源和漏源电压',480,390)
    c.text(22,30,'只改变源体偏置，其他相对电压不变',22)
    m=c.mos(220,190,'M1')
    c.wire(m['d'],(250,78));c.text(250,61,'D：VS + 1.65 V',20,anchor='middle')
    c.wire((30,190),m['g']);c.text(22,155,'G：VS + 0.90 V',20)
    c.wire(m['s'],(250,300));c.node(250,300)
    c.text(250,331,'S：VS = 0 → 0.8 V',21,SIGNAL,anchor='middle')
    c.wire(m['b'],(420,190),(420,245),color=BODY);c.ground(420,245,BODY)
    c.text(355,290,'B = 0',20,BODY)
    c.arrow((285,90),(285,125));c.text(306,119,'ID',20,SIGNAL)
    c.text(22,375,'VGS = 0.90 V；VDS = 1.65 V；VSB = VS。',19,MUTED)
    c.save('device-body-port',OUT,
           'V0体效应归档测试的四个端口。B接地，S从0扫描至0.8伏，G等于S加0.9伏，D等于S加1.65伏。栅源和漏源电压保持固定；不是固定栅极对地电压的源跟随器测试。')


def evidence_plots(body,output,ac):
    plt.rcParams.update({'font.family':'sans-serif',
        'font.sans-serif':['Microsoft YaHei','Noto Sans CJK SC','DejaVu Sans'],
        'font.size':13,'axes.labelsize':13,'xtick.labelsize':11,'ytick.labelsize':11,
        'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
        'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':MUTED,
        'lines.linewidth':1.8,'svg.hashsalt':'TechCodex-body-mirror','svg.fonttype':'path'})
    fig,axs=plt.subplots(2,1,figsize=(4.4,5.4),layout='constrained',sharex=True)
    for ax,y,label,color in ((axs[0],body[:,4],'模型 VTH / V',BLUE),
                             (axs[1],body[:,1]*1e6,'ID / µA',SIGNAL)):
        ax.plot(body[:,0],y,color=color)
        ax.scatter(body[[0,40,80],0],y[[0,40,80]],s=22,color=color,zorder=3)
        ax.set(ylabel=label,xlim=(0,.8));ax.grid(alpha=.18)
    axs[0].set_ylim(.65,1.02)
    axs[0].text(.04,.87,'0.688 → 0.946 V',transform=axs[0].transAxes,color=BLUE,fontsize=12)
    axs[1].set_ylim(0,47)
    axs[1].text(.31,.79,'40.64 → 1.20 µA',transform=axs[1].transAxes,color=SIGNAL,fontsize=12)
    axs[1].set(xlabel='VSB / V',xticks=[0,.2,.4,.6,.8])
    save(fig,'device-body-evidence','固定VGS与VDS的体效应扫描：VSB增大，模型VTH升高，ID减小。')

    fig,ax=plt.subplots(figsize=(4.4,3.7),layout='constrained')
    ax.plot(output[:,0],output[:,1]*1e6,color=SIGNAL,label='GF180 归档输出曲线')
    v,i,g=output[165];local=np.array([1.15,2.15])
    ax.plot(local,(i+g*(local-v))*1e6,'--',color=BLUE,label='工作点局部切线')
    ax.scatter([v],[i*1e6],s=30,color=BLUE,zorder=3)
    ax.text(.04,.94,f'gds = {g*1e6:.3f} µS\nro = {1/g/1e6:.2f} MΩ',
            transform=ax.transAxes,va='top',fontsize=12,color=BLUE)
    ax.set(xlabel='VDS / V',ylabel='ID / µA',xlim=(.8,2.6),ylim=(39.7,41.6))
    ax.grid(alpha=.18);ax.legend(loc='lower right',frameon=False,fontsize=10)
    save(fig,'device-output-slope','VGS为0.9伏的真实输出曲线与VDS为1.65伏时的局部切线。')

    f=ac[:,0];vx=ac[:,3]+1j*ac[:,4];vo=ac[:,1]+1j*ac[:,2]
    fig,axs=plt.subplots(2,1,figsize=(4.4,5.6),layout='constrained',sharex=True)
    axs[0].semilogx(f,abs(vx),color=SIGNAL)
    axs[0].set(ylabel='|vx / vid| / (V/V)',ylim=(0,2.1))
    for label,z,color in (('−vx / vid（去掉反相）',-vx,SIGNAL),('vo / vid',vo,BLUE)):
        axs[1].semilogx(f,np.unwrap(np.angle(z))*180/np.pi,color=color,label=label)
    axs[1].set(ylabel='相对 vid 的相位 / °',xlabel='频率 / Hz',ylim=(-140,40),yticks=[-135,-90,-45,0])
    axs[1].legend(frameon=False,fontsize=10,loc='lower left')
    for ax in axs:
        ax.set_xlim(1,1e9);ax.set_xticks([1,1e3,1e6,1e9],['1','1k','1M','1G']);ax.grid(alpha=.18)
    save(fig,'frequency-mirror-nodes','真实五管OTA的镜像节点X幅度，以及去掉反相后的X与输出O相对输入的相位。')


def analytic_phasors():
    c=Canvas('直接电流与镜像电流按相量相加',480,660)
    c.text(22,30,'镜像开始滞后，两路怎样相加',23)
    c.text(22,61,'直接 M2：1',20,SIGNAL);c.text(216,61,'镜像 M4：1 / (1 + jωτX)',18,BLUE)
    c.text(22,96,'低频：1 + 1 = 2，两项同相。',21)
    for top,r in ((134,1),(366,10)):
        h=1/(1+1j*r);total=1+h
        c.text(22,top,f'ωτX = {r} · 镜像落后 {abs(np.angle(h,deg=True)):.1f}°',21)
        origin=np.array([82.,top+60]);scale=145.
        direct=origin+[scale,0];end=direct+scale*np.array([h.real,-h.imag])
        c.line(82,top+17,82,top+154,color='#d5e0e8')
        c.line(60,top+60,405,top+60,color='#d5e0e8')
        c.text(403,top+49,'Re',17,MUTED);c.text(34,top+29,'Im',17,MUTED)
        c.arrow(tuple(origin),tuple(direct),SIGNAL)
        c.arrow(tuple(direct),tuple(end),BLUE)
        c.arrow(tuple(origin),tuple(end),INK,dash=True)
        c.text(153,top+45,'直接',18,SIGNAL)
        c.text(318,top+112,f'镜像 {abs(h):.3f}',19,BLUE)
        c.text(22,top+188,f'合成：{abs(total):.3f} ∠ {np.angle(total,deg=True):.1f}°',22)
    c.text(22,604,'以 I0 = gn vid / 2 为单位；黑虚线为合成。',19,MUTED)
    c.text(22,637,'输出电压 = 合成电流 / (Go + sCo)。',19,MUTED)
    c.save('frequency-mirror-phasors',OUT,
           '独立于工艺的简化模型。理想尾源，固定gm，只保留镜像节点对地电容。直接路径相量归一为1，蓝色镜像箭头接在直接箭头末端；黑色虚线从原点指向矢量和。在角频率乘镜像时间常数为1和10时，合成分别约1.581角负18.4度与1.015角负5.6度。尚未乘输出节点阻抗。')


if __name__=='__main__':
    data=read_evidence();verify(*data)
    body_port();evidence_plots(*data);analytic_phasors()
    print('Generated five static SVGs; GF180 and analytic sources remain separate.')
