#!/usr/bin/env python3
"""Execute the archived Lab05 scan callback, without constructing any ROS node.

Only scan callback, stamp(), and payload_hash() come from the original component.
Clock and publication are explicit injected interfaces; no rclpy.init or DDS.
"""
import argparse, base64, copy, csv, hashlib, importlib.util, json, struct, sys, threading, time, traceback
from pathlib import Path
import numpy as np
from rclpy.serialization import deserialize_message, serialize_message
from sensor_msgs.msg import LaserScan

def readcsv(path):
    with path.open(newline='') as f: return list(csv.DictReader(f))

def packets(path):
    return [json.loads(x) for x in path.read_text().splitlines()]

def decode(row): return deserialize_message(base64.b64decode(row['cdr']), LaserScan)

def canonical(m):
    """Independent exact field comparator, including stamp; ignore CDR padding."""
    header=(m.header.frame_id, m.header.stamp.sec, m.header.stamp.nanosec)
    scalars=struct.pack('<7f',m.angle_min,m.angle_max,m.angle_increment,m.time_increment,m.scan_time,m.range_min,m.range_max)
    return header, scalars, m.ranges.tobytes(), m.intensities.tobytes()

def signature(m):
    h,s,r,i=canonical(m)
    return hashlib.sha256(json.dumps(h).encode()+s+struct.pack('<II',len(r),len(i))+r+i).hexdigest()

def compare(expected, actual):
    e={(r['input_seq'],r['branch']):r for r in expected}
    a={(r['input_seq'],r['branch']):r for r in actual}
    if len(e)!=len(expected) or len(a)!=len(actual): raise ValueError('duplicate event key')
    differences=[]; timing=[]; byte_diff=0; matched=0; max_stamp_delta=0.
    for key in sorted(e.keys()|a.keys()):
        x=e.get(key); y=a.get(key)
        if x is None or y is None:
            differences.append(dict(input_seq=key[0],branch=key[1],kind='extra' if x is None else 'missing'))
            continue
        mx=decode(x); my=decode(y)
        timing.append(abs(x['t']-y['t']))
        max_stamp_delta=max(max_stamp_delta,abs((mx.header.stamp.sec-my.header.stamp.sec)+(mx.header.stamp.nanosec-my.header.stamp.nanosec)/1e9))
        if canonical(mx)==canonical(my): matched+=1
        else: differences.append(dict(input_seq=key[0],branch=key[1],kind='fields',expected=signature(mx),actual=signature(my)))
        if base64.b64decode(x['cdr'])!=base64.b64decode(y['cdr']): byte_diff+=1
    return dict(expected_packets=len(e),actual_packets=len(a),field_exact_packets=matched,
                field_match_fraction=matched/len(e) if e else None,differences=differences,
                cdr_byte_differences_on_paired_packets=byte_diff,
                max_header_stamp_error_s=max_stamp_delta,
                logical_publication_time_max_abs_error_s=max(timing,default=None),
                logical_publication_time_p95_abs_error_s=float(np.percentile(timing,95)) if timing else None)

def run(recording, component, mode, output):
    output.mkdir(parents=True,exist_ok=False)
    began=time.monotonic()
    sys.path.insert(0,str(component))
    spec=importlib.util.spec_from_file_location('archived_lab05_trial',component/'trial.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    scanrows=readcsv(recording/'scans.csv'); raw=packets(recording/'raw-scans.jsonl')
    pubrows=readcsv(recording/'published.csv'); published=packets(recording/'published-scans.jsonl')
    result=json.loads((recording/'result.json').read_text()); fault=json.loads((recording/'FAULT_START.json').read_text())
    assert len(scanrows)==len(raw) and len(pubrows)==len(published)
    expected=[]; current=None
    for row,p in zip(pubrows,published):
        assert int(row['seq'])==p['seq']
        if row['branch']=='localization': current=int(row['origin'])
        assert current is not None
        expected.append(dict(input_seq=current,branch=row['branch'],t=float(row['t']),cdr=p['cdr']))
    class Port:
        stamp=staticmethod(original.Observer.stamp)
        def __init__(self):
            self.lock=threading.RLock(); self.condition=result['condition'];self.window=None
            self.cached=None;self.last_scan=None;self.appearance=None
            self.data={'world':[],'scans':[]};self.raw=[];self.actual=[];self.clock=0.;self.current=0
        def now(self):return self.clock
        def publish(self,branch,msg,origin,origin_stamp,digest):
            self.actual.append(dict(input_seq=self.current,branch=branch,t=self.now(),origin=origin,
                origin_stamp=origin_stamp,payload_hash=digest,cdr=base64.b64encode(serialize_message(msg)).decode()))
    p=Port(); initialized=False;error=None;cache_audit=None;input_audit=[]
    try:
        for row,packet in zip(scanrows,raw):
            seq=int(row['seq']); assert seq==packet['seq']
            receipt=float(row['t']);m=decode(packet)
            assert abs(p.stamp(m)-float(row['stamp']))<1e-8
            assert original.payload_hash(m)==row['payload_hash']
            if mode=='late_join' and receipt<fault['t']: continue
            p.current=seq
            if not initialized and receipt>=fault['t']:
                p.window=fault['t'];p.cached=copy.deepcopy(p.last_scan);initialized=True
                cache_audit=dict(expected_origin=fault['cached_origin'],actual_origin=None if p.cached is None else p.cached[1],
                    expected_hash=fault['cached_hash'],actual_hash=None if p.cached is None else p.cached[2])
                if mode!='late_join': assert cache_audit['actual_origin']==cache_audit['expected_origin'] and cache_audit['actual_hash']==cache_audit['expected_hash']
            p.clock=float(row['stamp']) if mode=='header_clock' else receipt
            input_audit.append(dict(input_seq=seq,callback_time=receipt,replay_clock=p.clock,stamp=float(row['stamp'])))
            original.Observer.scan(p,m)
    except Exception:
        error=traceback.format_exc()
    if mode=='late_join':
        selected={r['input_seq'] for r in input_audit}
        # Compare entire declared suffix, even when the first callback raises.
        first=min(selected) if selected else len(raw)
        expected=[r for r in expected if r['input_seq']>=first]
    metrics=compare(expected,p.actual)
    metrics.update(mode=mode,recording=recording.name,condition=result['condition'],
        callback_exception=error,cache_audit=cache_audit,input_callbacks_attempted=len(input_audit),
        runtime_wall_s=time.monotonic()-began,network_started=False,clock_semantics='injected logical callback clock; no /clock publisher')
    metrics['accepted']=error is None and not metrics['differences'] and metrics['logical_publication_time_max_abs_error_s'] is not None and metrics['logical_publication_time_max_abs_error_s']<=.05
    for name,rows in [('actual',p.actual),('expected',expected),('input-timing',input_audit)]:
        with (output/(name+'.jsonl')).open('w') as f:
            for row in rows:f.write(json.dumps(row)+'\n')
    (output/'result.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(json.dumps({k:v for k,v in metrics.items() if k not in ('differences','callback_exception')}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('recording',type=Path);a.add_argument('component',type=Path)
    a.add_argument('mode',choices=['matched','header_clock','late_join']);a.add_argument('output',type=Path)
    v=a.parse_args();run(v.recording,v.component,v.mode,v.output)
