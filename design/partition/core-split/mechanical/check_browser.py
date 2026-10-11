"""Run through the shared browser guard; a timeout is not acceptance."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parent/'generated'
s=(root/'inspection.html').read_text().replace('<head>','<head>')
s=s.replace('<title>',f'<base href="{root.as_uri()}/"><title>',1)
s=s.replace('</html>', '''<script>
try {
if(report.alternatives.length!==5)throw Error('alternative count');
for(const a of report.alternatives){$('alternative').value=a.id;changeAlternative();let count=0;for(const b of a.boards){$('board').value=b.id;$('board').onchange();count+=$('trims').children.length;const button=$('trims').querySelector('button');button.click();if(!$('detail').textContent.includes(button.textContent))throw Error('selection');$('face').onchange();if($('detail').textContent!=='')throw Error('stale face');}if(count!==100)throw Error('inventory');}
$('alternative').value='three-compact';changeAlternative();$('trims').querySelector('button').click();document.body.dataset.browserTest='PASS: 5 alternatives, all 500 trimmer rows, selection and face reset';
}catch(e){document.body.dataset.browserTest='FAIL '+e.message;}
</script></html>''')
Path('/tmp/osc246-browser-test.html').write_text(s)
r=subprocess.run(['/usr/bin/chromium','--headless','--disable-background-networking','--disable-component-update','--no-proxy-server','--no-first-run','--disable-dev-shm-usage','--timeout=20000','--no-sandbox','--disable-gpu','--user-data-dir=/tmp/osc246-browser-profile3','--allow-file-access-from-files','--window-size=1500,1200','--screenshot=/tmp/osc246-preview.png','--dump-dom','file:///tmp/osc246-browser-test.html'],stdout=subprocess.PIPE,stderr=open('/tmp/osc246-chromium.log','w'),text=True,timeout=60)
Path('/tmp/osc246-browser-dom.html').write_text(r.stdout)
import re
v=re.search(r'data-browser-test="([^"]+)"',r.stdout)
print(v.group(1) if v else 'FAIL browser did not report')
assert r.returncode==0 and v and v.group(1).startswith('PASS')
