"""Independent nodal and device-equation audit for Chapter 4 (not process data)."""
import numpy as np
from check_teaching import solve, close


def main():
    rng=np.random.default_rng(20261022)
    for _ in range(64):
        gm=rng.uniform(.0001,.002);gmb=gm*rng.uniform(0,.4)
        ro,rd,rt,rs=10**rng.uniform(3.7,6,4);go=1/ro
        devices=[('o1','g1','t','0',gm,gmb,go),('o2','g2','t','0',gm,gmb,go)]
        resistors=[('o1','0',rd),('o2','0',rd),('t','0',rt)]
        dm=solve(['o1','o2','t'],{'0':0,'g1':.5,'g2':-.5},devices,resistors)
        cm=solve(['o1','o2','t'],{'0':0,'g1':1,'g2':1},devices,resistors)
        add=-gm*rd/(1+go*rd)
        acc=-gm*rd/(1+2*(gm+gmb)*rt+go*(rd+2*rt))
        close(dm['o1']-dm['o2'],add);close(dm['o1'],add/2);close(dm['t'],0)
        close(cm['o1'],acc);close(cm['o1']-cm['o2'],0)
        # Load-only common-to-differential conversion, under its stated go=0 assumption.
        dr=.01*rd
        mismatch=[('o1','g1','t','0',gm,gmb,0),('o2','g2','t','0',gm,gmb,0)]
        unequal=solve(['o1','o2','t'],{'0':0,'g1':1,'g2':1},mismatch,
                      [('o1','0',rd+dr/2),('o2','0',rd-dr/2),('t','0',rt)])
        close(unequal['o1']-unequal['o2'],-gm*dr/(1+2*(gm+gmb)*rt))
        # Separate source resistors with a shared finite tail impedance.
        degdevices=[('o1','g1','s1','0',gm,gmb,go),('o2','g2','s2','0',gm,gmb,go)]
        deg=solve(['o1','o2','s1','s2','t'],{'0':0,'g1':.5,'g2':-.5},degdevices,
                  resistors+[('s1','t',rs),('s2','t',rs)])
        expected=-gm*rd/(1+(gm+gmb)*rs+go*(rd+rs))
        close(deg['o1']-deg['o2'],expected);close(deg['t'],0)
        deg_cm=solve(['o1','o2','s1','s2','t'],{'0':0,'g1':1,'g2':1},degdevices,
                     resistors+[('s1','t',rs),('s2','t',rs)])
        close(deg_cm['o1'],-gm*rd/(1+(gm+gmb)*(rs+2*rt)+go*(rd+rs+2*rt)))
        bridge=solve(['o1','o2','s1','s2'],{'0':0,'g1':.5,'g2':-.5},degdevices,
                     [('o1','0',rd),('o2','0',rd),('s1','s2',2*rs)])
        close(bridge['o1']-bridge['o2'],expected)
        # Independent square-law branch equations, including the cut-off boundary.
        beta=rng.uniform(.0003,.004);it=rng.uniform(20e-6,200e-6);vov=np.sqrt(it/beta)
        vid=rng.uniform(-.99,.99)*np.sqrt(2)*vov
        u=np.sqrt(vov*vov-vid*vid/4)
        i1=beta/2*(u+vid/2)**2;i2=beta/2*(u-vid/2)**2
        close(i1+i2,it);close(i1-i2,beta*vid*np.sqrt(it/beta-vid*vid/4))
        close(beta/2*(np.sqrt(2)*vov)**2,it)
        # Gilbert: build lower branch currents, then calculate upper gm separately.
        bu,bl=rng.uniform(.0003,.004,2);vc=rng.uniform(-.9,.9)*np.sqrt(2*it/bl)
        ul=np.sqrt(it/bl-vc*vc/4)
        ia=bl/2*(ul+vc/2)**2;ib=bl/2*(ul-vc/2)**2
        gua=np.sqrt(bu*ia);gub=np.sqrt(bu*ib)
        close(gua-gub,np.sqrt(bu*bl/2)*vc)
    print('PASS: 64 independent nodal/device cases; DM/CM, 2RT, mismatch conversion, degeneration, bridge and Gilbert signs/factors.')


if __name__=='__main__':main()
