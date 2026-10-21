#!/usr/bin/env python3
"""Post-experiment packet audit, all-cell report and static scientific figures."""
import argparse,base64,copy,csv,hashlib,json,struct,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sensor_msgs.msg import LaserScan
from rclpy.serialization import deserialize_message

def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def csvrows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def unpack(p):return deserialize_message(base64.b64decode(p['cdr']),LaserScan)
def fields(m):
    # Separate implementation from frozen comparator: exact packed stamp/frame/scalars/arrays.
    return (m.header.stamp.sec,m.header.stamp.nanosec,m.header.frame_id,
        tuple(struct.pack('<f',getattr(m,n)) for n in ['angle_min','angle_max','angle_increment','time_increment','scan_time','range_min','range_max']),
        tuple(struct.pack('<f',x) for x in m.ranges),tuple(struct.pack('<f',x) for x in m.intensities))

def main(root):
    protocol=load(root/'FROZEN-PROTOCOL.json');ledger=load(root/'main/LEDGER.json')
    assert len(ledger)==len(protocol['order'])==36
    assert all(x['status']=='completed' and x['exit_code']==0 for x in ledger)
    for directory,key in [('component','component_hashes'),('source','source_hashes'),('inputs','input_hashes'),('development-inputs','development_input_hashes')]:
        assert hashes(root/directory)==protocol[key],directory
    # All source invocations refer to frozen source and occur after freeze.
    assert all(x['started_utc']>protocol['frozen_utc'] for x in ledger)
    rows=[]; audits=[]
    for folder,scheduled,attempt in zip(sorted(p for p in (root/'main').iterdir() if p.is_dir()),protocol['order'],ledger):
        assert attempt['mode']==scheduled['mode'] and attempt['recording']==scheduled['recording']
        result=load(folder/'evidence/result.json');actual=lines(folder/'evidence/actual.jsonl');target=lines(folder/'evidence/expected.jsonl')
        recording=root/scheduled['recording'];original_rows=csvrows(recording/'published.csv');original_packets=lines(recording/'published-scans.jsonl')
        raw=lines(recording/'raw-scans.jsonl');fault=load(recording/'FAULT_START.json');scans=csvrows(recording/'scans.csv')
        # Independently reconstruct original targets from immutable published packets, not saved expected files.
        originals=[];current=None
        for meta,p in zip(original_rows,original_packets):
            if meta['branch']=='localization':current=int(meta['origin'])
            originals.append(dict(input_seq=current,branch=meta['branch'],t=float(meta['t']),cdr=p['cdr']))
        if result['mode']=='late_join':
            first=next(int(x['seq']) for x in scans if float(x['t'])>=fault['t'])
            originals=[x for x in originals if x['input_seq']>=first]
        assert originals==target
        keys=lambda rr:[(x['input_seq'],x['branch']) for x in rr]
        assert len(set(keys(actual)))==len(actual)
        assert keys(actual)==sorted(keys(actual),key=lambda k:(k[0],0 if k[1]=='localization' else 1))
        e=dict(zip(keys(originals),originals));a=dict(zip(keys(actual),actual));same=changed=0;times=[];byte_diff=0;stamp_delta=[]
        for k in e.keys()&a.keys():
            m=unpack(e[k]);n=unpack(a[k]);equal=fields(m)==fields(n)
            same+=int(equal);changed+=int(not equal);times.append(abs(e[k]['t']-a[k]['t']))
            byte_diff+=base64.b64decode(e[k]['cdr'])!=base64.b64decode(a[k]['cdr'])
            stamp_delta.append(abs((m.header.stamp.sec-n.header.stamp.sec)+(m.header.stamp.nanosec-n.header.stamp.nanosec)/1e9))
        missing=len(e.keys()-a.keys());extra=len(a.keys()-e.keys())
        assert same==result['field_exact_packets'] and changed+missing+extra==len(result['differences'])
        assert byte_diff==result['cdr_byte_differences_on_paired_packets']
        assert abs(max(times,default=0)-result['logical_publication_time_max_abs_error_s'])<1e-12
        # Independently check every original packet against the declared Lab05 scan-routing rule.
        canonical_originals=0
        for k,r in e.items():
            seq,branch=k;t=float(scans[seq]['t']);src=seq
            in_window=fault['t']<=t<fault['t']+2
            if branch=='obstacles' and in_window:
                assert result['condition']!='missing'
                if result['condition'] in ('frozen','restamped'):src=fault['cached_origin']
            m=unpack(raw[src])
            if branch=='obstacles' and in_window and result['condition']=='restamped':m.header.stamp=copy.deepcopy(unpack(raw[seq]).header.stamp)
            assert fields(m)==fields(unpack(r)),(folder.name,k)
            canonical_originals+=1
        accepted=result['callback_exception'] is None and same==len(e)==len(a) and max(times,default=1)<=.05
        assert accepted==result['accepted']
        row=dict(attempt=attempt['index'],recording=result['recording'],condition=result['condition'],mode=result['mode'],
            expected=len(e),actual=len(a),field_exact=same,changed=changed,missing=missing,extra=extra,
            match_fraction=result['field_match_fraction'],max_clock_error_ms=1000*max(times,default=0),
            p95_clock_error_ms=1000*float(np.percentile(times,95)) if times else None,
            max_stamp_error_s=max(stamp_delta,default=0),byte_diff=byte_diff,callback_exception=bool(result['callback_exception']),accepted=accepted)
        rows.append(row);audits.append(dict(attempt=folder.name,original_target_verified=True,independent_field_comparator=True,
            original_routing_packets_verified=canonical_originals,output_order_verified=True,metrics_verified=True))
    with (root/'ALL-REPLAYS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    modes=['matched','header_clock','late_join'];summary={}
    for mode in modes:
        r=[x for x in rows if x['mode']==mode]
        summary[mode]=dict(accepted=sum(x['accepted'] for x in r),executions=len(r),expected_packets=sum(x['expected'] for x in r),
            actual_packets=sum(x['actual'] for x in r),field_exact_packets=sum(x['field_exact'] for x in r),
            changed=sum(x['changed'] for x in r),missing=sum(x['missing'] for x in r),extra=sum(x['extra'] for x in r),
            callback_exceptions=sum(x['callback_exception'] for x in r),cdr_byte_differences=sum(x['byte_diff'] for x in r),
            max_logical_time_error_ms=max(x['max_clock_error_ms'] for x in r))
    (root/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    audits_root=dict(all_36_metrics_and_targets_pass=True,protocol_and_input_hashes_match=True,before_main_freeze_verified=True,
        all_process_starts_completed=True,all_output_orders_verified=True,cell_audits=audits)
    (root/'EVIDENCE-VALIDATION.json').write_text(json.dumps(audits_root,indent=2)+'\n')
    # Plot all 36 cells; row labels explicitly preserve source identity, no pooled navigation statistic.
    names=[f'block-{b}-{c}' for b in range(1,4) for c in ['fresh','missing','frozen','restamped']]
    fractions=np.array([[next(x['match_fraction'] for x in rows if x['recording']==name and x['mode']==m) for m in modes] for name in names])
    fig,(ax,tm)=plt.subplots(1,2,figsize=(12,7),gridspec_kw={'width_ratios':[1.2,1]},layout='constrained')
    im=ax.imshow(fractions,vmin=0,vmax=1,cmap='viridis',aspect='auto');ax.set_yticks(range(12),names)
    ax.set_xticks(range(3),['Matched\n12/12 accepted','Header clock\n6/12 accepted','Late join\n6/12 accepted']);ax.set_title('Exact message-field fraction against original target')
    for i in range(12):
        for j in range(3):
            row=next(x for x in rows if x['recording']==names[i] and x['mode']==modes[j])
            ax.text(j,i,('ERR' if row['callback_exception'] else f'{100*fractions[i,j]:.0f}%'),ha='center',va='center',color='white' if fractions[i,j]<.5 else 'black')
    fig.colorbar(im,ax=ax,label='Exact packets / expected packets',shrink=.7)
    for j,m in enumerate(modes):
        rr=[next(x for x in rows if x['recording']==name and x['mode']==m) for name in names]
        for i,x in enumerate(rr):
            tm.scatter(j+(i-5.5)*.012,x['max_clock_error_ms'],alpha=.7,
                color='firebrick' if x['callback_exception'] else ['tab:blue','tab:orange','tab:green'][j],
                marker='x' if x['callback_exception'] else 'o',label=m if i==0 else None)
    tm.axhline(50,color='firebrick',linestyle='--',label='Declared 50 ms limit');tm.set_xticks(range(3),['Matched','Header clock','Late join'])
    tm.set_ylabel('Max paired logical publication-time error (ms)');tm.set_title('Logical time only\nRed crosses = partial exception output')
    tm.legend(loc='upper right');tm.grid(axis='y',alpha=.2)
    fig.suptitle('Lab08: 36 component replays of 12 Lab05 recordings\nERR = missing-cache callback exception; no new navigation trials',fontsize=12)
    fig.savefig(root/'replay-comparison.png',dpi=170);plt.close(fig)
    # A preselected first-block restamped source: observed clock/provenance versus replay equality.
    recording=root/'inputs/block-1-restamped';fault=load(recording/'FAULT_START.json');pub=csvrows(recording/'published.csv')
    original=[r for r in pub if r['branch']=='obstacles' and fault['t']-.5<=float(r['t'])<=fault['t']+2.5]
    fig,(ax,bx)=plt.subplots(2,1,figsize=(10,6),sharex=True,layout='constrained')
    t=[float(r['t'])-fault['t'] for r in original]
    ax.plot(t,[float(r['t'])-float(r['origin_stamp']) for r in original],'.-',label='Recorded known origin age')
    ax.plot(t,[float(r['t'])-float(r['stamp']) for r in original],'o--',label='Recorded advertised header age')
    ax.axvspan(0,2,color='orange',alpha=.13,label='Declared fault window');ax.set_ylabel('Age (simulated s)');ax.legend(loc='upper left');ax.grid(alpha=.2)
    for mode,marker in [('matched','o'),('header_clock','x')]:
        folder=next(p for p in (root/'main').iterdir() if p.is_dir() and p.name.endswith('block-1-restamped-'+mode))
        actual=lines(folder/'evidence/actual.jsonl');target=lines(folder/'evidence/expected.jsonl');e={(r['input_seq'],r['branch']):r for r in target}
        aa=[r for r in actual if r['branch']=='obstacles' and fault['t']-.5<=e[(r['input_seq'],r['branch'])]['t']<=fault['t']+2.5]
        bx.plot([e[(r['input_seq'],r['branch'])]['t']-fault['t'] for r in aa],
            [1000*(r['t']-e[(r['input_seq'],r['branch'])]['t']) for r in aa],marker+'--',label=mode)
    bx.axvspan(0,2,color='orange',alpha=.13);bx.set_xlabel('Time relative to recorded fault activation (simulated s)');bx.set_ylabel('Replay − original logical time (ms)')
    bx.legend();bx.grid(alpha=.2);fig.suptitle('First block, restamped recording: preserving a misleading timestamp\nMatched replay reproduces the recorded fields; it does not make the observation fresh',fontsize=12)
    fig.savefig(root/'recorded-clock-provenance.png',dpi=170);plt.close(fig)
    table=['| # | Original recording | Mode | Exact / target | Changed | Missing / extra | Max time error (ms) | Result |','| --- | --- | --- | --- | --- | --- | --- | --- |']
    for x in rows:
        table.append(f"| {x['attempt']} | {x['recording']} | {x['mode']} | {x['field_exact']}/{x['expected']} | {x['changed']} | {x['missing']}/{x['extra']} | {x['max_clock_error_ms']:.3f} | {'callback exception' if x['callback_exception'] else ('pass' if x['accepted'] else 'mismatch')} |")
    text='''# Lab08: all replay outcomes

Executed October 21, 2026. Each row is one fresh Python process on a preserved Lab05 recording, not a new navigation trial. Four excluded development replays are separately retained under development/ and all passed. Seven comparator tests passed before main. All 36 main process starts completed; component exceptions are outcomes inside those completed processes, not successful replays.

The exact target is the originally captured LaserScan on each branch/input index; fields include frame, stamps, scalar settings, ranges and intensities. CDR padding bytes are reported separately. Logical time is injected at callback entry, so this is not a measured DDS or wall scheduling latency. The declared 50 ms limit is an interface tolerance.

'''+ '\n'.join(table)+'\n\n## Aggregate diagnostics\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n\n## Evidence and reproduction\n\nFROZEN-PROTOCOL.json binds order/source/input hashes before all main starts. Every cell retains request.json, attempt.json, process.log, evidence/result.json (all discrepancies/exception text), original expected packets, actual packets and injected clocks. INPUT-MANIFEST.json maps copied recordings to their immutable Lab05 paths. EVIDENCE-VALIDATION.json checks metrics independently against original targets and the original routing rule, plus output order and frozen hashes. ENVIRONMENT.json records Python/ROS packages and inspected Vektor commit. README.md describes reproduction.\n\nInterpretation and limits are in FINDINGS.md. Reusing historical data does not add independent trials to Lab05, and 36 component replays must not be pooled with 39 prior navigation trials or 56 Lab07 oracle evaluations. No physical hardware, ROS transport, controller, whole Nav2, new closed-loop simulation, Vektor integration or external reproduction was tested.\n'
    (root/'REPORT.md').write_text(text)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('root',type=Path);v=a.parse_args();main(v.root.resolve())
