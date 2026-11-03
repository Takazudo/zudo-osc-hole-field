import json,datetime,os
from pathlib import Path
issued=datetime.datetime.fromisoformat('2026-10-16T19:10:51+00:00').timestamp()
value={'approved':True,'approved_by':'Takazudo (human owner, supplied approval transcript)',
'approval_reference':'source_thread_id=01a1183e-017b-75a9-bb91-a66aa5947004; messageSentinel_5f6f54e6704481918c63ae7a8b776191; 2026-10-16T19:10:51Z; approving exact proposal messageSentinel_95addfe6bec48191b92e04a6bd7bc7c7 at 2026-10-16T19:09:27Z',
'issued_at_unix':issued,'expires_at_unix':issued+86400,
'source_commit':'91403f4d78b72757187d8cfdbb4d2dc436a3cf72','verification_commit':'a57e02f6bfd770e55ebf448bc067e79fc6b08eb5',
'request_sha256':'a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1',
'run_id':'osc-stage18-native-001','run_path':'/home/takazudo/osc-stage18-native-001','native_export_opportunities':1,
'recorded_by':'Codex session 01a14620-af99-7435-90c6-ebcb3b6900e5; transcript transcription, not a human signature',
'approval_transcript':'OK。OSCはMoya判断でどんどん進めて。zfbもcodex及びx0xでやれることは進めてもらい、Mac検証が必要なときだけ声かけて'}
path=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-preflight/owner-approval.json')
with path.open('xb') as f:
    f.write((json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode());f.flush();os.fsync(f.fileno())
print(path.read_text())
