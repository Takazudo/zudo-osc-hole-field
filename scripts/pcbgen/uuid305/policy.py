"""Reviewed exact producer/oracle policy; callers cannot repin through admission."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
REVIEWED_POLICY_SHA256='e2685b547c7cd4a818ec1f86cb2f07b1b6d615a6535c4b8978ea809d7c93456a'
def check_policy(root):
 p=HERE/'oracle-policy.json'
 if hashlib.sha256(p.read_bytes()).hexdigest()!=REVIEWED_POLICY_SHA256:raise ValueError('reviewed oracle policy changed')
 policy=json.loads(p.read_text())
 for name,expected in policy['source_sha256'].items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise ValueError('reviewed producer/oracle bytes changed:'+name)
 return policy
