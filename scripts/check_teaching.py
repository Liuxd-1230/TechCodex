"""Independently stamp low-frequency MOS nodal equations to audit textbook formulas.

This is an algebra check, not a physical-process simulation or teaching dataset.
"""
import numpy as np


def solve(nodes,fixed,mos,resistors=(),currents=None):
    index={name:i for i,name in enumerate(nodes)}
    a=np.zeros((len(nodes),len(nodes)));b=np.zeros(len(nodes))
    def stamp(row,column,value):
        if row not in index:return
        if column in index:a[index[row],index[column]]+=value
        else:b[index[row]]-=value*fixed.get(column,0)
    for d,g,s,bulk,gm,gmb,go in mos:
        # Current from D to S. Stamp both terminal KCL equations independently.
        for terminal,value in ((g,gm),(bulk,gmb),(d,go),(s,-gm-gmb-go)):
            stamp(d,terminal,value);stamp(s,terminal,-value)
    for n1,n2,r in resistors:
        conductance=1/r
        for row,column,value in ((n1,n1,conductance),(n2,n2,conductance),(n1,n2,-conductance),(n2,n1,-conductance)):
            stamp(row,column,value)
    for name,value in (currents or {}).items():b[index[name]]+=value
    values=np.linalg.solve(a,b)
    return dict(fixed)|dict(zip(nodes,values))


def close(a,b):
    if not np.isclose(a,b,rtol=2e-8,atol=1e-10):raise AssertionError((a,b))


def main():
    rng=np.random.default_rng(20261021)
    for _ in range(64):
        gm1,gm2=rng.uniform(.0001,.002,2)
        gmb1,gmb2=rng.uniform(.05,.35,2)*[gm1,gm2]
        ro1,ro2=10**rng.uniform(4.3,6.3,2);g1,g2=1/ro1,1/ro2
        rl,rs,rb=10**rng.uniform(2,6,3)
        # Source follower: actual MOS D and B fixed; bias resistance and external RL distinct.
        sf=solve(['s'],{'g':1,'0':0},[('0','g','s','0',gm1,gmb1,g1)], [('s','0',rb),('s','0',rl)])
        rth=1/(gm1+gmb1+g1+1/rb)
        close(sf['s'],gm1*rth*rl/(rth+rl))
        # Common-gate gain and source input current, with finite drain termination.
        cg=solve(['d'],{'s':1,'0':0},[('d','0','s','0',gm1,gmb1,g1)],[('d','0',rl)])
        current_in=(gm1+gmb1+g1)-g1*cg['d']
        close(cg['d'],(gm1+gmb1+g1)/(1/rl+g1))
        close(1/current_in,(ro1+rl)/(1+(gm1+gmb1)*ro1))
        # Degenerated CS includes moving S and grounded B.
        cs=solve(['d','s'],{'g':1,'0':0},[('d','g','s','0',gm1,gmb1,g1)], [('d','0',rl),('s','0',rs)])
        close(cs['d'],-gm1*rl/(1+(gm1+gmb1)*rs+g1*(rl+rs)))
        # Cascode: compare the full two-node solution to Norton Gm * loaded Rout.
        pair=[('x','g','0','0',gm1,gmb1,g1),('o','0','x','0',gm2,gmb2,g2)]
        loaded=solve(['x','o'],{'g':1,'0':0},pair,[('o','0',rl)])
        rcas=ro1+ro2+(gm2+gmb2)*ro1*ro2
        effective_gm=gm1*(gm2+gmb2+g2)/(gm2+gmb2+g1+g2)
        close(loaded['o'],-effective_gm/(1/rcas+1/rl))
        output_test=solve(['x','o'],{'g':0,'0':0},pair,currents={'o':1})
        close(output_test['o'],rcas)
    print('PASS: 64 parameter sets; SF/CG/degenerated-CS/cascode equations match independent nodal stamps.')


if __name__=='__main__':main()
