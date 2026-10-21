"""Plot committed real ngspice data; optional eeplot skill profile for editorial review.

Default: python scripts/plot__device_cs__paper.py
Optional: --eeplot-assets <path-to-skill-assets>. No external helper is needed by readers.
Charts use G1 characteristics / E1 parameter curves and D1 Bode layouts.
"""
import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser=argparse.ArgumentParser()
parser.add_argument('--eeplot-assets',type=Path)
args=parser.parse_args()
if args.eeplot_assets:
    sys.path.insert(0,str(args.eeplot_assets))
    import eeplot
else:
    import plot_style as eeplot

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'模拟/实验/data'
OUT=ROOT/'模拟/图'
OUT.mkdir(parents=True,exist_ok=True)
metrics=json.loads((DATA/'metrics.json').read_text(encoding='utf-8'))
eeplot.use_style('paper',width='single')
print('[pe-plots] type: G1/E1 and D1 — real device sweeps and CS frequency response')
print('[pe-plots] gallery: KIND=wide-curve / bode-stack -> passive-volume / loop-bode templates')


def load(name):
    a=eeplot.load_series(DATA/name)
    print(f'[pe-plots] loaded {name}: series={list(a)} N={len(next(iter(a.values())))} decimated=no')
    return a


def save(fig,name):
    eeplot.save_fig(fig,OUT/(name+'.png'),style='paper')
    fig.savefig(OUT/(name+'.svg'))
    svg=OUT/(name+'.svg')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',
                   encoding='utf-8',newline='\n')
    plt.close(fig)


fig,axs=eeplot.curve_axes(1,aspect='wide'); ax=axs[0]
a=load('transfer-L1.csv')
ax.semilogy(a['vgs_V'],a['id_A']*1e6,color=eeplot.SYSTEM)
ax.set(xlabel='$V_{GS}$ [V]',ylabel='$I_D$ [µA]',xlim=(.3,1.55),ylim=(.0001,2000))
ax.set_xticks([.4,.6,.8,1,1.2,1.4])
ax.grid(alpha=.25,lw=.4)
save(fig,'device-transfer')

fig,axs=eeplot.curve_axes(1,aspect='wide'); ax=axs[0]
for vg,color in zip((.8,.9,1.1,1.3),('#CC3311','#0044BB','#777777','#000000')):
    a=load(f'output-Vg{vg:g}.csv')
    # Complete data are preserved; labels occupy the empty right margin.
    ax.plot(a['vds_V'],a['id_A']*1e6,color=color,label=f'{vg:g} V')
ax.set(xlabel='$V_{DS}$ [V]',ylabel='$I_D$ [µA]',xlim=(0,4.1),ylim=(0,325))
ax.set_xticks([0,1,2,3,4]); ax.set_yticks([0,100,200,300])
eeplot.end_labels(ax)
ax.grid(alpha=.25,lw=.4)
save(fig,'device-output')

fig,axs=eeplot.curve_axes(1,aspect='wide'); ax=axs[0]
for length,color in zip((.28,1,2),('#CC3311','#0044BB','#000000')):
    a=load(f'transfer-L{length:g}.csv')
    ax.plot(a['vgs_V'],a['gm_S']/a['gds_S'],color=color,label=f'{length:g} µm')
ax.set(xlabel='$V_{GS}$ [V]',ylabel='$g_m/g_{ds}$ [1]',xlim=(.3,1.85),ylim=(0,650))
ax.set_xticks([.4,.6,.8,1,1.2,1.4,1.6,1.8]); ax.set_yticks([0,100,200,300,400,500,600])
eeplot.end_labels(ax)
ax.grid(alpha=.25,lw=.4)
save(fig,'device-intrinsic-gain')

fig,axs=eeplot.curve_axes(1,aspect='wide'); ax=axs[0]
a=load('transfer-L1.csv')
ax.plot(a['vgs_V'],a['gm_S']/a['id_A'],color=eeplot.SYSTEM)
ax.set(xlabel='$V_{GS}$ [V]',ylabel='$g_m/I_D$ [1/V]',xlim=(.3,1.55),ylim=(0,30))
ax.set_xticks([.4,.6,.8,1,1.2,1.4]); ax.set_yticks([0,5,10,15,20,25])
ax.grid(alpha=.25,lw=.4)
save(fig,'device-gmid')

fig,axs=eeplot.bode_axes(); axm,axp=axs
a=load('cs-Rs0-ac.csv')
f=a['frequency_Hz']; gain=a['gain_real']+1j*a['gain_imag']
gm=metrics['cs_Rs0']['gm_S']; gds=metrics['cs_Rs0']['gds_S']
ro=1/(1/39000+gds)
# First-order prediction deliberately omits device capacitances, retained in real simulation.
theory=metrics['cs_Rs0']['kcl_gain']/(1+1j*2*np.pi*f*ro*2e-12)
axm.semilogx(f,20*np.log10(abs(gain)),color=eeplot.SYSTEM,label='BSIM4')
axm.semilogx(f,20*np.log10(abs(theory)),'--',color=eeplot.UNIT1,label='$R_{out}C_L$')
# Subtract the DC inversion to expose only the additional dynamic phase lag.
axp.semilogx(f,np.unwrap(np.angle(-gain))*180/np.pi,color=eeplot.SYSTEM)
axp.semilogx(f,np.unwrap(np.angle(-theory))*180/np.pi,'--',color=eeplot.UNIT1)
axm.set(ylabel='Magnitude [dB]',ylim=(-40,30),yticks=[-40,-20,0,20])
axp.set(ylabel='Phase lag [deg]',xlabel='Frequency [Hz]',ylim=(-110,10),yticks=[-100,-80,-60,-40,-20,0])
axp.set_xlim(10,1e9)
if args.eeplot_assets:
    eeplot.place_label_box(axm)
else:
    axm.legend(loc='upper right',frameon=False)
save(fig,'cs-bode')
