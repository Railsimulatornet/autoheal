"""Exercise the unmodified container scripts against a fake Docker CLI/socket."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest
import uuid

IMAGE = ''
PLATFORM = ''
MOCK_DOCKER = '''#!/bin/sh
set -eu
printf '%s\\n' "$*" >> /fixture/calls
case "$1" in
  info) exit 0 ;;
  ps)
    case "$*" in *"label=autoheal-fixture=true"*) ;; *) exit 2 ;; esac
    if [ "${MOCK_EMPTY:-false}" != true ]; then printf 'abc123\\n'; fi ;;
  inspect)
    case "$*" in
      *State.Health*) printf '%s|%s|/fixture-container\\n' "${MOCK_STATUS:-running}" "${MOCK_HEALTH:-unhealthy}" ;;
      *) printf '%s\\n' "${MOCK_TIMEOUT:-}" ;;
    esac ;;
  restart)
    printf '%s\\n' "$*" >> /fixture/restarts
    exit "${MOCK_RESTART_RC:-0}" ;;
  *) exit 2 ;;
esac
'''
MOCK_DATE = '''#!/bin/sh
if [ "$#" -eq 1 ] && [ "$1" = +%s ]; then
  printf '%s\\n' "$MOCK_NOW"
else
  exec /bin/date "$@"
fi
'''


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='autoheal-runtime-')
        self.root = Path(self.tmp.name)
        (self.root / 'bin').mkdir()
        (self.root / 'state').mkdir()
        for name, text in {'docker': MOCK_DOCKER, 'date': MOCK_DATE,
                           'sleep': '#!/bin/sh\nexit 99\n'}.items():
            p = self.root / 'bin' / name
            p.write_text(text)
            p.chmod(0o755)
        self.events = self.root / 'state' / 'fixture-container.events'
        self.now = int(time.time())
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.bind(str(self.root / 'daemon.sock'))

    def tearDown(self):
        self.socket.close()
        self.tmp.cleanup()

    def run_script(self, script='autoheal.sh', **overrides):
        env = {'PATH': '/fixture/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
               'AUTOHEAL_CONTAINER_LABEL': 'autoheal-fixture', 'AUTOHEAL_CONTAINER_LABEL_VALUE': 'true',
               'AUTOHEAL_START_PERIOD': '0', 'AUTOHEAL_INTERVAL': '1', 'AUTOHEAL_COOLDOWN': '300',
               'AUTOHEAL_MAX_RESTARTS': '3', 'AUTOHEAL_RESTART_WINDOW': '1800',
               'AUTOHEAL_DEFAULT_STOP_TIMEOUT': '10', 'AUTOHEAL_DRY_RUN': 'false',
               'AUTOHEAL_STATE_DIR': '/fixture/state', 'AUTOHEAL_HEARTBEAT_FILE': '/fixture/heartbeat',
               'DOCKER_SOCK': '/fixture/daemon.sock', 'MOCK_NOW': str(self.now)}
        env.update(overrides)
        name = 'autoheal-fixture-' + uuid.uuid4().hex
        command = ['docker', 'run', '--rm', '--name', name, '--network', 'none', '--read-only',
                   '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                   '--platform', PLATFORM, '--mount', f'type=bind,src={self.root},dst=/fixture']
        for key, value in env.items():
            command += ['--env', f'{key}={value}']
        command += ['--entrypoint', '/bin/sh', IMAGE, '/usr/local/bin/' + script]
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=30)
        finally:
            subprocess.run(['docker', 'rm', '-fv', name], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15, check=False)
        if script == 'autoheal.sh' and 'invalid' not in overrides.values() and overrides.get('AUTOHEAL_INTERVAL') != '0':
            # The mock sleep ends exactly one loop, without sleeping or a real restart.
            self.assertEqual(p.returncode, 99, p.stdout + p.stderr)
        return p

    def restarts(self):
        p = self.root / 'restarts'
        return p.read_text().splitlines() if p.exists() else []

    def test_healthy_not_restarted(self):
        self.run_script(MOCK_HEALTH='healthy')
        self.assertEqual(self.restarts(), [])

    def test_stopped_not_restarted(self):
        self.run_script(MOCK_STATUS='exited')
        self.assertEqual(self.restarts(), [])

    def test_no_healthcheck_not_restarted(self):
        self.run_script(MOCK_HEALTH='none')
        self.assertEqual(self.restarts(), [])

    def test_empty_selection(self):
        self.run_script(MOCK_EMPTY='true')
        self.assertEqual(self.restarts(), [])

    def test_dry_run(self):
        p = self.run_script(AUTOHEAL_DRY_RUN='true')
        self.assertIn('DRY-RUN', p.stdout)
        self.assertEqual(self.restarts(), [])
        self.assertEqual(self.events.read_text(), '')

    def test_restart_and_per_container_timeout(self):
        self.run_script(MOCK_TIMEOUT='17')
        self.assertEqual(self.restarts(), ['restart --timeout 17 abc123'])
        self.assertEqual(self.events.read_text().splitlines(), [str(self.now)])

    def test_invalid_timeout_uses_default(self):
        self.run_script(MOCK_TIMEOUT='not-a-number')
        self.assertEqual(self.restarts(), ['restart --timeout 10 abc123'])

    def test_cooldown_survives_new_process(self):
        self.run_script()
        p = self.run_script()
        self.assertIn('noch im Cooldown', p.stdout)
        self.assertEqual(len(self.restarts()), 1)

    def test_restart_limit(self):
        self.events.write_text(''.join(f'{self.now - n}\n' for n in (900, 800, 700)))
        p = self.run_script()
        self.assertIn('Restart-Limit erreicht', p.stdout)
        self.assertEqual(self.restarts(), [])

    def test_expired_events_pruned(self):
        self.events.write_text(f'{self.now - 2000}\n')
        self.run_script()
        self.assertEqual(self.events.read_text().splitlines(), [str(self.now)])

    def test_failed_restart_not_counted(self):
        self.run_script(MOCK_RESTART_RC='1')
        self.assertEqual(self.events.read_text(), '')

    def test_invalid_interval_rejected(self):
        self.assertEqual(self.run_script(AUTOHEAL_INTERVAL='invalid').returncode, 2)
        self.assertEqual(self.run_script(AUTOHEAL_INTERVAL='0').returncode, 2)

    def test_healthcheck(self):
        heartbeat = self.root / 'heartbeat'
        heartbeat.write_text('fixture')
        self.assertEqual(self.run_script(script='healthcheck.sh').returncode, 0)
        os.utime(heartbeat, (self.now - 120, self.now - 120))
        self.assertNotEqual(self.run_script(script='healthcheck.sh').returncode, 0)
        heartbeat.unlink()
        self.assertNotEqual(self.run_script(script='healthcheck.sh').returncode, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True)
    parser.add_argument('--platform', required=True, choices=['linux/amd64', 'linux/arm64'])
    args = parser.parse_args()
    IMAGE, PLATFORM = args.image, args.platform
    unittest.main(argv=['smoke_runtime.py'], verbosity=2)
