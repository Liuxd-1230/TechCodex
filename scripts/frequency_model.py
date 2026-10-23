"""Explicit two-node CS model: grounded source/body, real constant gm/ro/C."""
import numpy as np

PARAMS = dict(gm=1e-3, rs=1e4, rout=5e4, ci=1e-12, co=1e-12, cf=.1e-12)


def coefficients(gm, rs, rout, ci, co, cf):
    gi, go = 1/rs, 1/rout
    return np.array([gi*go, gi*(co+cf)+go*(ci+cf)+gm*cf,
                     ci*co+cf*(ci+co)])


def response(f, **p):
    gm,rs,rout,ci,co,cf = (p[k] for k in ('gm','rs','rout','ci','co','cf'))
    s=2j*np.pi*np.asarray(f)
    d=coefficients(**p)
    return (s*cf-gm)/rs/(d[0]+s*d[1]+s*s*d[2])


def nodal(f, **p):
    s=2j*np.pi*f;gm,rs,rout,ci,co,cf=(p[k] for k in ('gm','rs','rout','ci','co','cf'))
    return np.linalg.solve([[1/rs+s*(ci+cf),-s*cf],[gm-s*cf,1/rout+s*(co+cf)]],[1/rs,0])


def poles(**p):
    return np.roots(coefficients(**p)[::-1])
