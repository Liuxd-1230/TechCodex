"""Independent linear-network audit of cascode and mirror-load OTA formulas."""
import numpy as np
from check_teaching import solve


def main():
    rng=np.random.default_rng(20261022)
    for _ in range(96):
        g,p=rng.uniform(.0001,.001,2)
        h=.25*g
        n,e,t=10**rng.uniform(-7,-5,3)
        k=g+h+n
        mos=[('x','i1','t','0',g,h,n),('o','i2','t','0',g,h,n),
             ('x','x','0','0',p,0,e),('o','x','0','0',p,0,e),('t','0','0','0',g,0,t)]
        denominator=2*k*(p+e)+t*(p+n+e)
        for mode,inputs in [('dm',(.5,-.5)),('cm',(1,1))]:
            r=solve(['x','o','t'],{'0':0,'i1':inputs[0],'i2':inputs[1]},mos)
            prediction= (g/(n+e)*(1-(k*e+t*(n+e)/2)/denominator) if mode=='dm' else -g*t/denominator)
            assert np.isclose(r['o'],prediction,rtol=1e-9)
            if mode=='cm':assert np.isclose(r['o'],r['x'])
        cas=solve(['x','o'],{'0':0},[('x','0','0','0',g,0,n),('o','0','x','0',p,h,e)],currents={'o':1})
        assert np.isclose(cas['o'],1/n+1/e+(p+h)/(n*e))
    print('PASS: 96 independent nodal cases: cascode Rout, OTA differential/common-mode gains, mirror-node response.')


if __name__=='__main__':main()
