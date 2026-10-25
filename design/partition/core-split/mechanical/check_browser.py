"""Bounded Chrome CLI check. Run through the available shared browser guard.

Only temporary copies are instrumented; generated application assets stay intact.
"""
import argparse
import gzip
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
GENERATED = HERE / 'generated'
TIMEOUT = 60


def discover_browser(explicit=None):
    configured = explicit or os.environ.get('CHROME_BIN')
    candidates = [configured] if configured else [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        str(Path.home() / 'Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
        'chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable',
    ]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise ValueError(f'Browser discovery failed: {candidates!r}. Set --browser or CHROME_BIN to an executable (not an app directory).')


def browser_command(browser, profile, screenshot, url, platform=sys.platform):
    flags = ['--headless', '--disable-background-networking', '--disable-component-update',
             '--no-proxy-server', '--no-first-run', '--no-default-browser-check',
             '--timeout=20000', '--allow-file-access-from-files', '--window-size=1500,1600']
    if platform.startswith('linux'):
        flags.append('--disable-dev-shm-usage')
    return [browser, *flags, f'--user-data-dir={profile}', f'--screenshot={screenshot}', '--dump-dom', url]


def bounded_run(command, stdout, stderr, timeout=TIMEOUT):
    # A session isolates this invocation's descendants from the user's browser.
    process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
    try:
        return process.wait(timeout=timeout)
    finally:
        # Also reap descendants after a normal CLI exit; never kill other profiles.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def run_view(browser, out, name, script, receipt):
    started = time.monotonic()
    entry = {'view': name, 'timeout_seconds': TIMEOUT}
    receipt['runs'].append(entry)
    with tempfile.TemporaryDirectory(prefix='osc263-') as temporary:
        temp = Path(temporary)
        source = (GENERATED / 'inspection.html').read_text()
        monitor = '''<script>window.browserErrors=[];
addEventListener('error',e=>browserErrors.push(e.message||'asset: '+(e.target.src||e.target.href)),true);
addEventListener('unhandledrejection',e=>browserErrors.push(String(e.reason)));
const originalError=console.error;console.error=(...a)=>{browserErrors.push(a.map(String).join(' '));originalError(...a)};
</script>'''
        source = source.replace('<title>', f'<base href="{GENERATED.as_uri()}/">{monitor}<title>', 1)
        source = source.replace('</html>', f'<script>{script}</script></html>')
        page = temp / 'test.html'
        page.write_text(source)
        command = browser_command(browser, temp / 'profile', out / f'{name}.png', page.as_uri())
        entry['command'] = command
        with (temp / 'dom.html').open('w') as stdout, (out / f'{name}.stderr.txt').open('w') as stderr:
            try:
                entry['exit_status'] = bounded_run(command, stdout, stderr)
            except subprocess.TimeoutExpired:
                entry['exit_status'] = 124
                entry['failure'] = '60-second browser deadline; inspect stderr for launch/permissions/profile errors'
        dom = (temp / 'dom.html').read_text()
        match = re.search(r'<pre id="browser-result" hidden="">(.*?)</pre>', dom, re.S)
        if match:
            entry['browser_result'] = json.loads(html.unescape(match.group(1)))
        entry['elapsed_seconds'] = round(time.monotonic() - started, 3)
        passed = (entry['exit_status'] == 0 and match and
                  entry['browser_result']['status'] == 'PASS' and (out / f'{name}.png').is_file())
        if not passed:
            with gzip.open(out / f'{name}.dom.html.gz', 'wt') as saved:
                saved.write(dom)
            raise RuntimeError(f'{name}: browser check failed; see {out} (stderr, receipt and compressed DOM)')
        print(f'PASS {name}: {entry["elapsed_seconds"]}s', flush=True)


def main():
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'interrupted by signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', help='Chrome/Chromium executable; otherwise CHROME_BIN or discovery')
    parser.add_argument('--output-dir', type=Path, required=True, help='New retained evidence directory (never overwritten)')
    parser.add_argument('--visuals', action='store_true', help='Capture other alternatives, faces and assembled/exploded views')
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    receipt = {'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'platform': sys.platform, 'invocation': sys.argv, 'guard_held': os.environ.get('PW_GUARD_HELD') == '1',
               'input_sha256': {}, 'runs': []}
    for path in [Path(__file__), HERE / 'browser_assertions.js', HERE / 'preview-template.html', HERE / 'build.py', *sorted(GENERATED.iterdir())]:
        if path.is_file():
            receipt['input_sha256'][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        browser = discover_browser(args.browser)
        receipt['browser'] = browser
        receipt['version'] = subprocess.check_output([browser, '--version'], text=True, timeout=10).strip()
        assertion = (HERE / 'browser_assertions.js').read_text()
        run_view(browser, out, 'three-compact', 'const capture={alternative:"three-compact",verify:true};\n'+assertion, receipt)
        if args.visuals:
            alternatives = json.loads((GENERATED / 'comparison.json').read_text())['alternatives']
            views = [(a['id'], {'alternative': a['id']}) for a in alternatives if a['id'] != 'three-compact']
            views += [('three-compact-back', {'alternative': 'three-compact', 'board': 'KB', 'face': 'B.Cu'}),
                      ('three-compact-kc', {'alternative': 'three-compact', 'board': 'KC', 'face': 'F.Cu'}),
                      ('three-compact-reset', {'alternative': 'three-compact', 'reset': True})]
            for alternative in ['two-deep', 'three-compact']:
                for mode in ['assembled', 'exploded']:
                    views.append((f'{alternative}-{mode}', {'alternative': alternative, 'svg': mode}))
            for name, capture in views:
                run_view(browser, out, name, 'const capture='+json.dumps(capture)+';\n'+assertion, receipt)
        receipt['status'] = 'PASS'
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        receipt.update(status='FAIL', failure=str(error))
        print(str(error), file=sys.stderr)
        return 1
    finally:
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    sys.exit(main())
