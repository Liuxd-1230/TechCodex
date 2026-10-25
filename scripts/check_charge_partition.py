"""Independent finite differences, channel quadrature and current checks for 2.3.

All terminal vectors use (g,d,s,b); currents are positive into the device.
Only the explicitly stated long-channel inversion-charge model is evaluated.
"""
import numpy as np


def example_charge(v, c0, eta):
    q=c0*(v[0]-v[2])
    return np.array([q,-eta*q,-(1-eta)*q,0.])


def example_jacobian(c0, eta):
    return c0*np.array([[1,0,-1,0],[-eta,0,eta,0],
                       [eta-1,0,1-eta,0],[0,0,0,0]])


# Integrate a channel profile, without using the closed-form 2/3 or 4/15 results.
gauss,weights=np.polynomial.legendre.leggauss(64)
t=(gauss+1)/2
z=1-t*t
dz=weights*t  # z=1-t^2 removes the saturation-end square-root singularity.


def channel_charge(v, ca, threshold=.4):
    u=v[0]-v[2]-threshold
    if u<=0:
        raise ValueError('Strong inversion is required')
    drain=v[1]-v[2]
    # This drift-model expression also supports a small negative Vds near equilibrium.
    # Saturation freezes the profile; CLM, body and overlap charge are omitted.
    drop=min(drain,u)
    a=u*drop-drop*drop/2
    density=-ca*np.sqrt(u*u-2*a*z)
    qd=np.sum(dz*z*density)
    qs=np.sum(dz*(1-z)*density)
    qg=-np.sum(dz*density)
    return np.array([qg,qd,qs,0.])


def finite_jacobian(charge, v, h=2e-6):
    shifts=np.eye(4)*h
    return np.column_stack([(charge(v+d)-charge(v-d))/(2*h) for d in shifts])


def check_law(charge, v, expected, scale):
    numerical=finite_jacobian(charge,v)
    assert abs(np.sum(charge(v))/scale)<1e-12, 'total terminal charge'
    assert np.allclose(charge(v+3.1)/scale,charge(v)/scale,atol=1e-12), 'common potential shift'
    assert np.allclose(numerical/scale,expected/scale,rtol=2e-8,atol=2e-8), 'all 16 partial derivatives'
    assert np.max(abs(numerical.sum(axis=0)/scale))<2e-8, 'column sums'
    assert np.max(abs(numerical.sum(axis=1)/scale))<2e-8, 'row sums'


def current_check(charge, expected, scale):
    omega=2*np.pi*1000
    base=np.array([1.2,1.5,.1,0.])
    amplitude=np.array([.02,.03,.01,.01])
    phase=np.array([0.,.4,.7,1.])
    voltage=lambda time:base+amplitude*np.sin(omega*time+phase)
    derivative=lambda time:amplitude*omega*np.cos(omega*time+phase)
    for time in np.linspace(0,.00037,13):
        h=1e-10
        measured=(charge(voltage(time+h))-charge(voltage(time-h)))/(2*h)
        predicted=expected@derivative(time)
        assert np.allclose(measured/(scale*omega),predicted/(scale*omega),atol=2e-9)
        assert abs(sum(measured)/(scale*omega))<2e-9
    times=np.linspace(0,.00037,4097)
    integral=np.trapezoid(np.array([expected@derivative(time) for time in times]),times,axis=0)
    delta=charge(voltage(times[-1]))-charge(voltage(times[0]))
    assert np.allclose(integral/scale,delta/scale,rtol=1e-7,atol=1e-9), 'integrated displacement current'


def main():
    ca=1.5e-15  # Arbitrary capacitance scale, not GF180 device data.
    rng=np.random.default_rng(203)
    for eta in (0.,.2,.5,.9):
        charge=lambda v:example_charge(v,ca,eta)
        expected=example_jacobian(ca,eta)
        for _ in range(20):
            check_law(charge,rng.normal(size=4),expected,ca)
        current_check(charge,expected,ca)
        if eta:
            assert expected[0,1]==0 and expected[1,0]==-eta*ca
        else:
            assert np.array_equal(expected,expected.T), 'ordinary gate-source capacitor limit'
    charge=lambda v:channel_charge(v,ca)
    coefficients=np.array([2/3,-4/15,-2/5,0.])
    expected=ca*np.outer(coefficients,[1,0,-1,0])
    for _ in range(20):
        source=rng.uniform(-.5,.5);u=rng.uniform(.2,1)
        v=np.array([source+.4+u,source+u+.5,source,source-.1])
        assert np.allclose(charge(v)/(ca*u),coefficients,atol=1e-12), 'weighted channel integrals'
        check_law(charge,v,expected,ca)
    current_check(charge,expected,ca)
    assert expected[0,1]==0 and np.isclose(expected[1,0]/ca,-4/15)
    # Uniform channel at Vds=0: equal source/drain sharing and reciprocal Jacobian.
    v=np.array([1.,.1,.1,0.])
    equilibrium=ca*np.array([[1,-.5,-.5,0],[-.5,1/3,1/6,0],
                             [-.5,1/6,1/3,0],[0,0,0,0]])
    check_law(charge,v,equilibrium,ca)
    assert np.isclose(charge(v)[1],charge(v)[2],rtol=1e-12)
    assert np.allclose(equilibrium,equilibrium.T,rtol=0,atol=0)
    # A physical overlap capacitor adds a symmetric, charge-conserving stamp.
    overlap=.1*ca*np.outer([1,-1,0,0],[1,-1,0,0])
    total=expected+overlap
    assert np.allclose((total-total.T)/ca,(expected-expected.T)/ca,atol=1e-15)
    assert np.max(abs(total.sum(axis=0)/ca))<1e-14
    assert np.max(abs(total.sum(axis=1)/ca))<1e-14
    print('PASS: 80 counterexample biases, 20 saturated channel biases and the Vds=0 limit.')
    print('PASS: all 16 partials, charge/row/column constraints, nonreciprocity, dQ/dt and current integrals, reciprocal limits and overlap stamps.')


if __name__=='__main__':main()
