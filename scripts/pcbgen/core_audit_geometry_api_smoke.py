"""Pinned-native API contract only. No board saves, fills, DRC or task receipts."""
import hashlib,json,subprocess
from pathlib import Path
import pcbnew

def main():
 contract=json.loads(Path(__file__).with_name('core_audit_geometry_api_contract.json').read_bytes())
 version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
 if version!='10.0.6' or pcbnew.GetBuildVersion()!=version:raise ValueError('requires exact pinned10.0.6 bindings')
 if hashlib.sha256(Path(pcbnew.__file__).read_bytes()).hexdigest()!=contract['wrapper_sha256']:raise ValueError('pinned native wrapper changed')
 board=pcbnew.BOARD();assert len(list(board.Zones()))==0
 zone=pcbnew.ZONE(board);assert isinstance(zone.m_Uuid.AsString(),str)
 assert not hasattr(zone,'IsRuleArea') and zone.GetIsRuleArea() is False
 zone.SetIsRuleArea(True);assert zone.GetIsRuleArea() is True
 zone.SetIsRuleArea(False);zone.SetLayer(pcbnew.F_Cu)
 assert list(zone.GetLayerSet().Seq())==[pcbnew.F_Cu]
 assert isinstance(zone.GetNetname(),str)
 # Ephemeral in-memory test poly only; never load/alter an immutable input zone.
 poly=pcbnew.SHAPE_POLY_SET();zone.SetFilledPolysList(pcbnew.F_Cu,poly)
 actual=zone.GetFilledPolysList(pcbnew.F_Cu)
 assert actual.ArcCount()==0 and isinstance(actual.Format(),str) and actual.Format()==poly.Format()
 print(json.dumps(dict(status='PINNED_NATIVE_API_CONTRACT_PASS; NOT_GEOMETRY_BOOTSTRAP',version=version,image=contract['image'],wrapper_sha256=contract['wrapper_sha256'],methods=['GetIsRuleArea','GetLayerSet.Seq','GetNetname','GetFilledPolysList','ArcCount','Format'],layers=dict(F_Cu=pcbnew.F_Cu,B_Cu=pcbnew.B_Cu),completed_drc_tasks=0,refilled=False,saved=False,after_signature_bound=False),sort_keys=True))
if __name__=='__main__':main()
