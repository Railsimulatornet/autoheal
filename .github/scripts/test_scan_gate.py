"""Test fail-closed scan orchestration with a mocked Docker/Trivy command."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('scan-image.sh')
FAKE = r'''#!/usr/bin/env python3
import json,os,pathlib,sys
a=sys.argv[1:]
p=next(x for x in a if x.startswith('type=bind,src=') and x.endswith(',dst=/out'))
out=pathlib.Path(p[len('type=bind,src='):-len(',dst=/out')])
with open(os.environ['CALLS'],'a') as log: log.write(json.dumps(a)+'\n')
mode=os.environ['SCENARIO']; gate='--exit-code' in a; convert='convert' in a
if mode=='scan-error' and not gate and not convert: sys.exit(1)
if mode=='convert-error' and convert: sys.exit(1)
if mode!='missing-report' and not (mode=='missing-gate-report' and gate):
    path=out/pathlib.Path(a[a.index('--output')+1]).name
    data={'SchemaVersion':2,'Metadata':{'OS':{'Family':'alpine'}},'Results':[{'Type':'alpine'}]}
    if mode=='unknown-os': data['Metadata']={}
    path.write_text(json.dumps(data) if path.suffix=='.json' else 'test report\n')
if gate: sys.exit({'findings':42,'eol':43,'gate-error':1}.get(mode,0))
'''


class GateTests(unittest.TestCase):
    def case(self, mode, platform='linux/amd64'):
        with tempfile.TemporaryDirectory(prefix='autoheal gate ') as tmp:
            root=Path(tmp); (root/'image').mkdir()
            for f in ('index.json','oci-layout'): (root/'image'/f).write_text('{}')
            (root/'docker').write_text(FAKE); (root/'docker').chmod(0o755)
            env=dict(os.environ, PATH=str(root)+':'+os.environ['PATH'], SCENARIO=mode,
                     CALLS=str(root/'calls'), TRIVY_CACHE_DIR=str(root/'cache'))
            p=subprocess.run(['bash',str(SCRIPT),str(root/'image'),platform,str(root/'out')],
                             env=env,capture_output=True,text=True,timeout=30)
            calls=[json.loads(x) for x in (root/'calls').read_text().splitlines()] if (root/'calls').exists() else []
            return p,calls

    def test_clean_both_platforms(self):
        for platform in ('linux/amd64','linux/arm64'):
            p,calls=self.case('clean',platform)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(len(calls),4)
            self.assertNotIn('--ignore-unfixed',calls[0])
            self.assertIn('--exit-code',calls[-1])
            self.assertIn('--skip-db-update',calls[-1])
            self.assertIn(platform,calls[-1])
            self.assertTrue(all(not any('docker.sock' in x for x in c) for c in calls))

    def test_findings_block(self): self.assertEqual(self.case('findings')[0].returncode,42)
    def test_eol_blocks(self): self.assertEqual(self.case('eol')[0].returncode,43)
    def test_scan_failure_blocks(self): self.assertNotEqual(self.case('scan-error')[0].returncode,0)
    def test_conversion_failure_blocks(self): self.assertNotEqual(self.case('convert-error')[0].returncode,0)
    def test_gate_failure_blocks(self): self.assertNotEqual(self.case('gate-error')[0].returncode,0)
    def test_missing_report_blocks(self): self.assertNotEqual(self.case('missing-report')[0].returncode,0)
    def test_missing_gate_report_blocks(self): self.assertNotEqual(self.case('missing-gate-report')[0].returncode,0)
    def test_unknown_os_blocks(self): self.assertNotEqual(self.case('unknown-os')[0].returncode,0)
    def test_unknown_platform_blocks(self): self.assertNotEqual(self.case('clean','linux/386')[0].returncode,0)


if __name__=='__main__': unittest.main()
