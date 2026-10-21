"""Small standalone Matplotlib style for repository readers (no Codex dependency)."""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

SYSTEM, UNIT1, UNIT2, GRAY = '#000000', '#CC3311', '#0044BB', '#909090'
SQUARE_SIDE = 2.0


def use_style(style='paper', width='single'):
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],
        'font.size':8,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,
        'legend.fontsize':7.5,'mathtext.fontset':'stix','axes.linewidth':.6,
        'lines.linewidth':1,'svg.fonttype':'none','savefig.dpi':600})


def curve_axes(n, aspect='wide'):
    use_style()
    fig, ax = plt.subplots(figsize=(3.5,2.6),layout='constrained')
    ax.set_box_aspect(2/3)
    ax.tick_params(direction='in',top=True,right=True)
    ax.grid(alpha=.25,lw=.4)
    return fig,[ax]


def bode_axes():
    use_style()
    fig, axes = plt.subplots(2,1,sharex=True,figsize=(3.5,2.9),layout='constrained')
    for ax in axes:
        ax.set_xscale('log')
        ax.tick_params(direction='in',top=True,right=True)
        ax.grid(alpha=.25,lw=.4)
    return fig,axes


def clean_ylim(ax, data, zero_base=False, **kwargs):
    a = np.concatenate([np.ravel(x) for x in data])
    lo,hi = float(a.min()),float(a.max())
    ax.set_ylim(0 if zero_base else lo-.1*(hi-lo), hi+.15*(hi-lo))


def load_series(path):
    a = np.genfromtxt(path,delimiter=',',names=True)
    return {name:a[name] for name in a.dtype.names}


def save_fig(fig,path,style='paper'):
    fig.align_ylabels()
    fig.savefig(path,dpi=600)


def end_labels(ax):
    for line in ax.lines:
        if not line.get_label().startswith('_'):
            x,y = line.get_data()
            ax.annotate(line.get_label(),(x[-1],y[-1]),xytext=(3,0),
                        textcoords='offset points',va='center',color=line.get_color())
