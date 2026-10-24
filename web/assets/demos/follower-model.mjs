/*
 * Fixed-bias small-signal model; drain and body are AC-grounded.
 * vi is a step about the unchanged DC bias. id is incremental current injected
 * into the output by the MOS; ib, il and ic are currents leaving it, so
 * id = ib + il + ic. GL is an incremental load and does not change the bias.
 */
export const END_TIME=600e-9;
const gm=1e-3,C=100e-12,gmb=.2e-3,gds=1e-5,gB=1e-5;

export const SCENARIOS=Object.freeze({
  ideal:Object.freeze({gmb:0,gds:0,gB:0,GL:0}),
  body:Object.freeze({gmb,gds,gB,GL:0}),
  load10k:Object.freeze({gmb,gds,gB,GL:1e-4}),
  load1k:Object.freeze({gmb,gds,gB,GL:1e-3})
});

export function parameters(key){
  const scenario=SCENARIOS[key];
  if(!scenario)throw new RangeError('Unknown source-follower scenario');
  const {gmb,gds,gB,GL}=scenario,go=gm+gmb+gds+gB+GL;
  return {gm,gmb,gds,gB,GL,C,go,gain:gm/go,tau:C/go,rout:1/(go-GL)};
}

export function response(time,input,key){
  if(!Number.isFinite(time)||time<0||time>END_TIME)throw new RangeError('Outside the teaching time axis');
  if(!Number.isFinite(input)||input<-.01||input>.01)throw new RangeError('Outside the teaching input range');
  const p=parameters(key),fraction=-Math.expm1(-time/p.tau),decay=Math.exp(-time/p.tau);
  const vo=p.gain*input*fraction,dvdt=gm/C*input*decay;
  const id=gm*(input-vo)-(p.gmb+p.gds)*vo,ib=p.gB*vo,il=p.GL*vo,ic=C*dvdt,q=C*vo;
  return {time,vi:input,vo,vgs:input-vo,id,ib,il,ic,q,target:p.gain*input,tau:p.tau,gain:p.gain,rout:p.rout,dvdt};
}
