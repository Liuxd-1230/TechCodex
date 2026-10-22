"""Two teaching figures from committed native-ngspice measurements; no smoothing."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'模拟/实验/差分对/data'
OUT=ROOT/'模拟/图'
INK='#203b4a';GREEN='#127b70';ORANGE='#a46723';GRAY='#6e7e87'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.labelsize':14,
    'legend.fontsize':12,'axes.spines.top':False,'axes.spines.right':False,
    'axes.labelcolor':INK,'text.color':INK,'axes.edgecolor':INK,'svg.fonttype':'none',
    'svg.hashsalt':'TechCodex-Ch04','lines.linewidth':2})


def load(name):
    return np.genfromtxt(DATA/(name+'.csv'),delimiter=',',names=True)


def finish(fig,name):
    for ax in fig.axes:
        ax.grid(alpha=.16);ax.tick_params(labelsize=12)
    fig.savefig(OUT/(name+'.svg'),metadata={'Date':None})
    svg=OUT/(name+'.svg')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',
                   encoding='utf-8',newline='\n')
    fig.savefig(OUT/(name+'.png'),dpi=180)
    plt.close(fig)


def main():
    m=json.loads((DATA/'metrics.json').read_text())
    a=load('ideal-steering-sweep');v=a['input_V'];i1=a['i1_A'];i2=a['i2_A'];q=m['ideal']
    fig,axs=plt.subplots(2,1,figsize=(5.6,5.3),layout='constrained',sharex=True)
    axs[0].plot(v,i1*1e6,label='$I_1$',color=GREEN)
    axs[0].plot(v,i2*1e6,label='$I_2$',color=INK)
    axs[0].set(ylabel='Branch current [µA]',ylim=(-3,86))
    axs[0].legend(ncol=2,loc='upper center',frameon=False)
    fitted_gm=-q['gains']['dm']['diff']/20000
    beta=fitted_gm**2/80e-6;vov=80e-6/fitted_gm;bound=np.sqrt(2)*vov
    analytic=np.sign(v)*80e-6
    inside=np.abs(v)<=bound
    analytic[inside]=beta*v[inside]*np.sqrt(vov*vov-v[inside]**2/4)
    axs[1].plot(v,(i1-i2)*1e6,color=GREEN,label='GF180MCU')
    axs[1].plot(v,analytic*1e6,'--',color=ORANGE,label='Square law (slope matched)')
    axs[1].plot(v[fitted_gm*abs(v)<90e-6],fitted_gm*v[fitted_gm*abs(v)<90e-6]*1e6,':',color=GRAY,label='Local tangent')
    axs[1].set(xlabel='$V_{I1}-V_{I2}$ [V]',ylabel='$I_1-I_2$ [µA]',ylim=(-95,95),xlim=(-.65,.65))
    axs[1].legend(loc='upper left',frameon=False)
    finish(fig,'diff-steering')

    a=load('ideal-common-sweep');b=load('mos-common-sweep');valid=m['mos_valid_cm_grid_V']
    fig,axs=plt.subplots(2,1,figsize=(5.6,5.2),layout='constrained',sharex=True)
    # The sum of source-terminal currents measures the actual tail port.
    axs[0].plot(a['input_V'],(a['is1_A']+a['is2_A'])*1e6,'--',color=GRAY,label='Ideal tail (unlimited compliance)')
    axs[0].plot(b['input_V'],(b['is1_A']+b['is2_A'])*1e6,color=GREEN,label='Fixed-gate MOS tail')
    axs[0].plot([1.4],[80],'o',color=INK,ms=4)
    axs[0].annotate('Same bias at 1.4 V',(1.4,80),xytext=(1.5,47),fontsize=12,arrowprops={'arrowstyle':'-','color':INK})
    axs[0].set(ylabel='Tail current [µA]',ylim=(0,1.12*np.max(b['is1_A']+b['is2_A'])*1e6))
    axs[0].legend(loc='upper left',frameon=False)
    axs[1].plot(b['input_V'],b['tail_V']-b['vdsat_tail_V'],color=GREEN,label='Tail MOS margin')
    input_margin=b['o1_V']-b['tail_V']-b['vdsat1_V']
    axs[1].plot(b['input_V'],input_margin,color=INK,label='Input MOS margin')
    axs[1].axhline(0,color=GRAY,lw=.8)
    axs[1].set(xlabel='Input common-mode voltage [V]',ylabel='$V_{DS}-V_{DSAT}$ [V]',xlim=(.75,3.3),ylim=(-.25,1.05*input_margin.max()))
    axs[1].legend(loc='upper center',frameon=False)
    for ax in axs:
        ax.axvspan(.75,valid[0],color=ORANGE,alpha=.1)
        ax.axvspan(valid[1],3.3,color=ORANGE,alpha=.1)
    finish(fig,'diff-common-sweep')
    print('Generated 2 figures: measured branch steering and controlled tail comparison; dashed square law is analytical.')


if __name__=='__main__':main()
