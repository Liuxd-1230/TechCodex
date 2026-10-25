"""Verify 6.2 drain-port elimination against independent stamps and native ngspice."""
from pathlib import Path
import numpy as np
from frequency_model import coefficients, poles, nodal
from check_frequency import stamp_network
ROOT=Path(__file__).resolve().parents[1]


def check_output_port(f, gm, rs, rout, ci, co, cf):
    s=2j*np.pi*f;gi=1/rs;go=1/rout;ct=ci+cf
    # A separate device stamp fixes the drain at 1 V and zeros the input generator.
    vg=stamp_network(['g'],[('o','g','0','0',gm,0,go)],
                     [('g','0',gi+s*ci),('g','o',s*cf)],{'o':1,'0':0})[0]
    measured=go+s*co+s*cf*(1-vg)+gm*vg
    eliminated=go+s*co+s*cf*(gi+gm+s*ci)/(gi+s*ct)
    determinant=np.polynomial.polynomial.polyval(s,coefficients(gm,rs,rout,ci,co,cf))/(gi+s*ct)
    assert np.isclose(measured,eliminated,rtol=1e-10,atol=1e-20)
    assert np.isclose(measured,determinant,rtol=1e-10,atol=1e-20)
    gate_signal,output_signal=nodal(f,gm=gm,rs=rs,rout=rout,ci=ci,co=co,cf=cf)
    assert np.isclose(output_signal/gate_signal,(s*cf-gm)/(go+s*(co+cf)),rtol=1e-10)
    # Exact floating-gate limit: a capacitor divider and a transconductance current.
    floating=stamp_network(['g'],[],[('g','0',s*ci),('g','o',s*cf)],{'o':1,'0':0})[0]
    assert np.isclose(floating,cf/ct,rtol=1e-12)
    assert np.isclose(gm*floating+s*cf*(1-floating),gm*cf/ct+s*ci*cf/ct,rtol=1e-12)


def native_output_port():
    from run import run_deck
    deck=(ROOT/'模拟/实验/频率响应/decks/analytic-output-port.cir').read_text(encoding='utf-8')
    values=[1,1e4,1e6,1e9]
    data=run_deck('ch06/analytic-output-port',deck,
                  ['port-1','port-10k','port-1Meg','port-1G'])
    max_error=0
    for rs,a in zip(values,data):
        s=2j*np.pi*a[:,0];gi=1/rs;gm=1e-3;go=1/5e4;ci=co=1e-12;cf=1e-13;ct=ci+cf
        expected_gate=s*cf/(gi+s*ct)
        expected_y=go+s*co+s*cf*(gi+gm+s*ci)/(gi+s*ct)
        gate=a[:,1]+1j*a[:,2];current=a[:,3]+1j*a[:,4]
        error=float(np.max(abs(current-expected_y)/abs(expected_y)))
        max_error=max(max_error,error)
        assert np.allclose(gate,expected_gate,rtol=1e-8,atol=1e-20)
        assert error<1e-8
        assert np.isclose(current[0],go,rtol=4e-4)
    # The numerical example in 6.2: large finite Rs retains both natural modes.
    ps=sorted(-poles(gm=gm,rs=1e6,rout=1/go,ci=ci,co=co,cf=cf)/(2*np.pi))
    estimate=(go+gm*cf/ct)/(2*np.pi*(co+ci*cf/ct))
    assert np.allclose(ps,[25898.91328725,16300745.66555635],rtol=1e-10)
    assert abs(estimate/ps[1]-1)<.008
    print(f'PASS: native drain-port AC at 4 source resistances; maximum complex-current relative error {max_error:.3g}.')


def main():
    rng=np.random.default_rng(614)
    for _ in range(120):
        gm=10**rng.uniform(-4,-2);rs=10**rng.uniform(0,9);rout=10**rng.uniform(3,6)
        ci,co,cf=10**rng.uniform(-14,-11,3)
        check_output_port(10**rng.uniform(-2,9),gm,rs,rout,ci,co,cf)
    for gm,cf in [(0,1e-13),(1e-3,0)]:
        check_output_port(1e6,gm,1e4,5e4,1e-12,1e-12,cf)
    native_output_port()
    print('PASS: 120 independent drain-port stamps, floating-gate division, determinant identity and both finite-Rs modes.')


if __name__=='__main__':main()
