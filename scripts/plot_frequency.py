"""Few explanatory plots; original complex AC samples remain in the lab."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from frequency_model import PARAMS, response
ROOT=Path(__file__).resolve().parents[1];LAB=ROOT/'模拟/实验/频率响应/data';OUT=ROOT/'模拟/图'
plt.rcParams.update({'font.size':13,'legend.fontsize':10,'font.family':'DejaVu Sans','svg.hashsalt':'TechCodex-ch6'})
GREEN='#126e63';AMBER='#a05b18';BLUE='#2969a0'


def save(fig,name):
    fig.tight_layout();fig.savefig(OUT/(name+'.svg'),metadata={'Date':None})
    path=OUT/(name+'.svg');path.write_text('\n'.join(x.rstrip() for x in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    fig.savefig(OUT/(name+'.png'),dpi=170);plt.close(fig)


def read(name):
    a=np.loadtxt(LAB/(name+'-ac.csv'),delimiter=',',skiprows=1);return a[:,0],a[:,1]+1j*a[:,2]


def main():
    f=np.logspace(4,10,700);s=2j*np.pi*f;p=PARAMS;A=p['gm']*p['rout']
    mi=p['ci']+p['cf']*(1+A);mo=p['co']+p['cf']*(1+1/A)
    curves=[('Full two-node, Cgd = 0.1 pF',response(f,**p),GREEN,'-'),('Cgd = 0',response(f,**dict(p,cf=0)),BLUE,'-'),('Fixed-gain Miller approximation',-A/((1+s*p['rs']*mi)*(1+s*p['rout']*mo)),AMBER,'--')]
    fig,axs=plt.subplots(2,1,figsize=(7.3,6.7),sharex=True)
    for label,h,color,style in curves:
        axs[0].semilogx(f,20*np.log10(abs(h)),color=color,ls=style,label=label)
        axs[1].semilogx(f,np.unwrap(np.angle(h/h[0]))*180/np.pi,color=color,ls=style)
    axs[0].set_ylim(-85,40);axs[0].set_ylabel('Voltage gain (dB)');axs[0].legend()
    axs[1].set_ylabel('Additional phase (deg)');axs[1].set_xlabel('Frequency (Hz)');axs[1].set_yticks([0,-90,-180,-270])
    for ax in axs:ax.grid(alpha=.18);ax.set_xlim(1e4,1e10)
    save(fig,'frequency-miller-response')
    fig,axs=plt.subplots(2,1,figsize=(7.3,6.7),sharex=True)
    for name,label,color in [('ota-1p','GF180: CL = 1 pF',GREEN),('ota-5p','GF180: CL = 5 pF',AMBER)]:
        f,h=read(name);axs[0].semilogx(f,20*np.log10(abs(h)),color=color,label=label)
        axs[1].semilogx(f,np.unwrap(np.angle(h))*180/np.pi,color=color)
    a=np.loadtxt(LAB/'ota-1p-op.csv',delimiter=',',skiprows=1,ndmin=2)[0]
    gm=a[6];go=a[12]+a[20]
    f=np.logspace(3,9,500);h=gm/(go+2j*np.pi*f*1e-12)
    axs[0].semilogx(f,20*np.log10(abs(h)),color=BLUE,ls='--',label='gm / (go2 + go4 + s CL), 1 pF')
    axs[1].semilogx(f,np.unwrap(np.angle(h))*180/np.pi,color=BLUE,ls='--')
    axs[0].set_ylabel('VO / VID (dB)');axs[0].legend();axs[0].axhline(0,color='#999',lw=.7);axs[0].set_ylim(-35,50)
    axs[1].set_ylabel('Phase VO / VID (deg)');axs[1].set_xlabel('Frequency (Hz)')
    for ax in axs:ax.grid(alpha=.18);ax.set_xlim(1e3,1e9)
    save(fig,'frequency-ota-load')
    fig,axs=plt.subplots(2,1,figsize=(7.3,6.2),sharex=True)
    for suffix,ax,title in [('',axs[0],'RS = 10 kohm; CL = 1 pF (output dominated)'),('-input-limited',axs[1],'RS = 1 Mohm; CL = 0.05 pF (input loading matters)')]:
        for name,label,color in [('cs','Common source',GREEN),('cascode','Cascode',AMBER)]:
            f,h=read(name+suffix);ax.semilogx(f,20*np.log10(abs(h)/abs(h[0])),label=label,color=color)
        ax.set_title(title,fontsize=11);ax.set_ylabel('Relative gain (dB)');ax.set_ylim(-20,1);ax.axhline(-3.0103,color='#999',lw=.8,ls='--');ax.grid(alpha=.18);ax.legend();ax.set_xlim(1e5,1e8)
    axs[1].set_xlabel('Frequency (Hz)');save(fig,'frequency-cascode-contrast')


if __name__=='__main__':main()
