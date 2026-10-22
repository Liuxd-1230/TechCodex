"""Selected explanatory figures from Chapter 5 archived native-SPICE data."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'模拟/实验/电流镜/data'
OUT=ROOT/'模拟/图'
plt.rcParams.update({'font.size':14,'axes.labelsize':14,'legend.fontsize':11,'xtick.labelsize':12,'ytick.labelsize':12,'svg.hashsalt':'TechCodex-ch5','font.family':'DejaVu Sans'})


def save(fig,name):
    fig.tight_layout()
    fig.savefig(OUT/(name+'.svg'),metadata={'Date':None})
    p=OUT/(name+'.svg');p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    fig.savefig(OUT/(name+'.png'),dpi=170);plt.close(fig)


def main():
    fig,ax=plt.subplots(2,1,figsize=(7,7),sharex=True)
    for name,label,color in [('short','Simple L=0.28 um','#777777'),('medium','Simple L=1 um','#126e63'),('long','Simple L=2 um','#2969a0'),('cascode','Cascode L=1 um','#a05b18')]:
        a=np.loadtxt(LAB/(name+'.csv'),delimiter=',',skiprows=1)
        ax[0].plot(a[:,0],a[:,1]*1e6,label=label,color=color)
        if name in ('medium','cascode'):
            margin=a[:,3]-a[:,4]
            if name=='cascode':margin=np.minimum(margin,a[:,0]-a[:,3]-a[:,5])
            ax[1].plot(a[:,0],margin,label=label,color=color)
    ax[0].axhspan(38,42,color='#126e63',alpha=.09,label='40 uA +/-5%')
    ax[0].set_ylabel('Output current (uA)');ax[0].legend(ncol=2)
    ax[1].axhline(0,color='#777',ls='--');ax[1].set_ylabel('Min. output-stack\nsaturation margin (V)');ax[1].set_xlabel('Output voltage (V)');ax[1].legend()
    for a in ax:a.grid(alpha=.15);a.axvspan(.4,2.6,color='#173c50',alpha=.035)
    save(fig,'mirror-compliance')
    q=json.loads((LAB/'metrics.json').read_text())['ota']
    a=np.loadtxt(LAB/'ota-large-signal.csv',delimiter=',',skiprows=1)
    fig,ax=plt.subplots(figsize=(7,4.5));ax.plot(a[:,0]*1000,a[:,1],color='#126e63',label='GF180 OTA, free output')
    ax.plot(a[:,0]*1000,q['output_V']+q['dm_gain']*a[:,0],color='#a05b18',ls='--',label='Tangent at zero')
    ax.set_ylim(0,3.3);ax.set_xlabel('Differential input (mV)');ax.set_ylabel('Output voltage (V)');ax.legend();ax.grid(alpha=.15)
    save(fig,'mirror-ota-transfer')


if __name__=='__main__':main()
