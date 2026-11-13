"""Exact P retained-oracle configuration, with no environment native override."""
import hashlib,os
from pathlib import Path
EXPECTED_IMAGE = "kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec"
EXPECTED_VERSION = "10.0.6"
EXPECTED_PIN_SHA256 = "769e2be0b61e7d92a6930684f13166b7dc098522008de3969cd30d6c4a363246"
EXPECTED_WRAPPER_SHA256 = "bc74f0ade82c29d64c44119ea435bc7bfd164fc06e9afff240a3cb2b44b272a0"

def configuration(root,environment=None):
 environment=os.environ if environment is None else environment
 if environment.get('KICAD_CLI_BIN'):raise ValueError('KICAD_CLI_BIN native override is forbidden for retained P evidence')
 root=Path(root);pin=root/'scripts/kicad/pin.env';wrapper=root/'scripts/kicad/run.sh'
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 if digest(pin)!=EXPECTED_PIN_SHA256 or digest(wrapper)!=EXPECTED_WRAPPER_SHA256:raise ValueError('Pinned oracle configuration/wrapper bytes changed')
 if "KICAD_IMAGE='"+EXPECTED_IMAGE+"'" not in pin.read_text().splitlines():raise ValueError('Unexpected pinned oracle image')
 return {'configured_image':EXPECTED_IMAGE,'pin_env_sha256':EXPECTED_PIN_SHA256,'run_sh_sha256':EXPECTED_WRAPPER_SHA256,'native_override_allowed':False,'expected_version':EXPECTED_VERSION}

def runtime(root,pcbnew_version,cli_version,environment=None):
 result=configuration(root,environment)
 if pcbnew_version.strip()!=EXPECTED_VERSION or cli_version.strip()!=EXPECTED_VERSION:raise ValueError('Exact10.0.6 pcbnew and CLI versions required')
 return dict(result,pcbnew_version=pcbnew_version.strip(),cli_version=cli_version.strip(),scope='Runtime version plus exact launcher configuration; container ownership/image inspection remains launch receipt responsibility')

if __name__ == '__main__':
 import argparse,json
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);args=parser.parse_args()
 print(json.dumps(configuration(args.root),indent=2))
