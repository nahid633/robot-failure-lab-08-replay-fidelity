#!/usr/bin/env python3
"""Bounded fresh-process replay campaign with immutable input/source snapshots."""
import argparse, datetime, hashlib, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

MODES=['matched','header_clock','late_join']
FILES=['scans.csv','raw-scans.jsonl','published.csv','published-scans.jsonl','result.json','FAULT_START.json','effective-before.json','effective-after.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def hashes(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def execute(root,rows,stage,source):
    folder=root/stage;folder.mkdir(exist_ok=False);ledger=[]
    env=dict(os.environ,ROS_DOMAIN_ID='111',ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',ROS_LOCALHOST_ONLY='1')
    for n,(recording,mode) in enumerate(rows):
        trial=folder/f'{n+1:02d}-{recording.name}-{mode}';trial.mkdir()
        command=[sys.executable,str(source/'replay.py'),str(recording),str(root/'component'),mode,str(trial/'evidence')]
        request=dict(index=n+1,recording=str(recording.relative_to(root)),mode=mode,command=command,started_utc=utc(),timeout_s=30)
        save(trial/'request.json',request);start=time.monotonic()
        try:
            with (trial/'process.log').open('w') as log:
                proc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=30,env=env)
            request.update(exit_code=proc.returncode,status='completed' if proc.returncode==0 else 'process_failure')
        except subprocess.TimeoutExpired: request.update(exit_code=None,status='timeout')
        request.update(finished_utc=utc(),elapsed_wall_s=time.monotonic()-start)
        save(trial/'attempt.json',request);ledger.append(request)
        save(folder/'LEDGER.json',ledger)
        print(stage,n+1,mode,recording.name,request['status'],flush=True)
    return ledger

def main():
    a=argparse.ArgumentParser();a.add_argument('stage',choices=['prepare','development','freeze','main']);a.add_argument('root',type=Path);v=a.parse_args()
    root=v.root.resolve();kb=root.parent.parent;source=Path(__file__).resolve().parent
    lab05=kb/'artifacts/robot-failure-lab-05'
    if v.stage=='prepare':
        allrows=[]
        for block in range(1,4):
            for condition in ['fresh','missing','frozen','restamped']:
                name=f'block-{block}-{condition}';src=lab05/name
                if not (src/'result.json').exists():src=lab05/(name+'-attempt-2')
                dest=root/'inputs'/name;dest.mkdir(parents=True,exist_ok=False)
                for filename in FILES:shutil.copy2(src/filename,dest/filename)
                allrows.append(dict(id=name,source=str(src.relative_to(kb)),hashes=hashes(dest)))
        for c in ['fresh','missing','frozen','restamped']:
            src=lab05/'excluded-checks/verification-v3'/('block-0-'+c);dest=root/'development-inputs'/src.name
            dest.mkdir(parents=True,exist_ok=False)
            for filename in FILES:shutil.copy2(src/filename,dest/filename)
        for filename in ['params.yaml','packages.txt','PROTOCOL.json']:
            shutil.copy2(lab05/filename,root/('original-'+filename))
        context=root/'implementation-context';context.mkdir()
        shutil.copy2(kb/'code/vektor/src/replay.cpp',context/'vektor-replay.cpp')
        save(root/'INPUT-MANIFEST.json',allrows)
        save(root/'PRIOR-ARCHIVES.json',{str(p.relative_to(kb)):sha(p) for p in [kb/'artifacts/robot-failure-lab-05-code-evidence.zip',kb/'artifacts/robot-failure-lab-07-code-evidence.zip']})
        packages=subprocess.run(['dpkg-query','-W','-f=${Package}\t${Version}\n','ros-jazzy-rclpy','ros-jazzy-sensor-msgs','ros-jazzy-nav2-simple-commander','python3-numpy','python3-matplotlib'],capture_output=True,text=True)
        save(root/'ENVIRONMENT.json',dict(utc=utc(),python=sys.version,platform=platform.platform(),packages=packages.stdout,package_query_exit=packages.returncode,vektor_commit=subprocess.check_output(['git','-C',str(kb/'code/vektor'),'rev-parse','HEAD'],text=True).strip(),network='No ROS node/context initialized; callback method invoked via injected clock/publication ports. Domain/localhost vars defense in depth only.'))
    elif v.stage=='development':
        snapshot=root/'development-source';shutil.copytree(source,snapshot,ignore=shutil.ignore_patterns('__pycache__'))
        with (root/'development-tests.log').open('w') as f:
            test=subprocess.run([sys.executable,'-m','unittest','-v','test_replay'],cwd=snapshot,stdout=f,stderr=subprocess.STDOUT)
        assert test.returncode==0
        rows=[(root/'development-inputs'/('block-0-'+c),'matched') for c in ['fresh','missing','frozen','restamped']]
        ledger=execute(root,rows,'development',snapshot)
        checks=[json.loads(p.read_text()) for p in sorted((root/'development').glob('*/evidence/result.json'))]
        save(root/'DEVELOPMENT-GATE.json',dict(attempts=len(ledger),bounded_budget=6,tests_passed=True,matched_passed=sum(x['accepted'] for x in checks),gate_passed=len(checks)==4 and all(x['accepted'] for x in checks)))
    elif v.stage=='freeze':
        assert json.loads((root/'DEVELOPMENT-GATE.json').read_text())['gate_passed']
        assert not (root/'main').exists()
        shutil.copytree(source,root/'source',ignore=shutil.ignore_patterns('__pycache__'))
        order=[]
        for b in range(1,4):
            for c in ['fresh','missing','frozen','restamped']:
                modes=MODES[(b-1)%3:]+MODES[:(b-1)%3]
                order.extend(dict(recording=f'inputs/block-{b}-{c}',mode=m) for m in modes)
        save(root/'FROZEN-PROTOCOL.json',dict(frozen_utc=utc(),order=order,main_process_budget=36,timeout_per_process_s=30,no_retries=True,
            acceptance='For each replay, no callback exception; all expected branch/input-index LaserScan fields including header stamps exactly equal; no missing/extra packets; maximum logical publication time error <=0.050 simulated seconds.',
            timing='Matched uses recorded callback t. Header-clock uses sensor stamp while preserving original external fault activation order/time. Publication t injected at callback entry; original intra-callback clock advances cannot be reconstructed.',
            late_join='Start at first recorded callback at/after fault; no cached scan or prior callback state. Compare all original outputs from that input onward, even if replay raises. Local seq counter resets; content primary, original origin metadata retained separately.',
            scope='Actual archived Observer.scan implementation, with observer-only geometry branch disabled; no ROS transport/executor, controller, TF, physics or full navigation replay.',
            component_hashes=hashes(root/'component'),source_hashes=hashes(root/'source'),input_hashes=hashes(root/'inputs'),development_input_hashes=hashes(root/'development-inputs')))
    else:
        frozen=json.loads((root/'FROZEN-PROTOCOL.json').read_text())
        for name in ['component','source','inputs','development-inputs']:
            key={'component':'component_hashes','source':'source_hashes','inputs':'input_hashes','development-inputs':'development_input_hashes'}[name]
            assert hashes(root/name)==frozen[key],name
        rows=[(root/x['recording'],x['mode']) for x in frozen['order']]
        execute(root,rows,'main',root/'source')
if __name__=='__main__':main()
