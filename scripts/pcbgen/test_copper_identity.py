import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import copper_identity as ci
from scripts.pcbgen.copper_identity import (reject_new_uuid_collisions,retention,require_unique,copper_objects,duplicate_groups,
    inventory,check,drop_copper_blocks,propose_normalization,apply_manifest,verify_normalization,load_board_text,board_bytes,digest)

ROOT=Path(__file__).resolve().parents[2]
K_BOARD=ROOT/'boards/osc-core/osc-core.kicad_pcb'
K_SHA='7251dd933af810b7c659c9b90c6f6d9ba32d55ea432b0414c26c8b26b6b4be42'
K_GROUPS={'5d905700-2dea-5407-bfdb-7d54a9887d2f':'via','6ad7a8ef-06c4-5daf-8c20-536f50fb0495':'segment',
          '7a9f1a78-0122-5c1a-807d-edd14509239d':'segment','7bc22643-4022-5e36-b5d2-8117e4041966':'segment',
          '8ed29fa2-46b9-5922-8b00-41d148dd7308':'segment','9dd204e2-36b2-5742-bd54-f78d414e5f80':'segment'}
U=['00000000-0000-4000-8000-%012d'%i for i in range(10)]


def seg(uid,net='A',layer='F.Cu',x=0,width=0.2):
    return (f'\t(segment\n\t\t(start {x} 0)\n\t\t(end {x} 1)\n\t\t(width {width})\n\t\t(layer "{layer}")\n'
            f'\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n')


def via(uid,net='A',x=1):
    return f'\t(via\n\t\t(at {x} 1)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n'


def board(*items):
    return '(kicad_pcb\n\t(version 20250000)\n\t(gr_text "k\xe9ep (quoted) parens" (uuid "'+U[9]+'"))\n'+''.join(items)+')\n'


class CopperIdentityTests(unittest.TestCase):
    def test_retention_counts_distinct_geometry_with_same_uuid(self):
        a={'uuid':'duplicate','net':'AGND','xy':[1,2]};b={**a,'xy':[3,4]}
        before={'tracks':[a,b],'vias':[]};after={'tracks':[b,a],'vias':[]}
        r=retention(before,after)
        self.assertEqual((r['before'],r['identical'],r['before_unique_uuids']),(2,2,1))
        self.assertEqual(r['changed_existing_uuids'],[])
        r=retention(before,{'tracks':[b],'vias':[]})
        self.assertEqual(r['removed_objects'],1);self.assertEqual(r['changed_existing_uuids'],['duplicate'])

    def test_new_ids_cannot_alias_existing_or_each_other(self):
        for existing,rows in ((['a'],[{'uuid':'a'}]),([],[{'uuid':'a'},{'uuid':'a'}])):
            with self.assertRaises(ValueError):reject_new_uuid_collisions(existing,rows)
        reject_new_uuid_collisions(['a','a'],[{'uuid':'b'}])  # unchanged legacy copper stays


class InventoryTests(unittest.TestCase):
    def test_segment_via_and_cross_kind_duplicates_are_reported_with_geometry_and_byte_spans(self):
        text=board(seg(U[0],x=0),seg(U[0],x=2,width=0.3),via(U[1]),via(U[1],x=5),seg(U[2]),via(U[2],x=7),seg(U[3]))
        inv=inventory(text,'synthetic')
        self.assertEqual((inv['counts'],inv['objects'],inv['unique_uuids']),({'segment':4,'via':3},7,4))
        groups={g['uuid']:g for g in inv['duplicate_groups']}
        self.assertEqual(list(groups),sorted([U[0],U[1],U[2]]))
        self.assertEqual(groups[U[0]]['kinds'],['segment']);self.assertEqual(groups[U[1]]['kinds'],['via'])
        self.assertEqual(groups[U[2]]['kinds'],['segment','via'])
        first,second=groups[U[0]]['occurrences']
        self.assertEqual((first['index'],second['index']),(0,1))
        self.assertEqual(first['geometry'],{'start':[0.0,0.0],'end':[0.0,1.0],'width':0.2})
        self.assertEqual(second['geometry'],{'start':[2.0,0.0],'end':[2.0,1.0],'width':0.3})
        self.assertEqual(groups[U[1]]['occurrences'][1]['geometry'],{'at':[5.0,1.0],'size':0.6,'drill':0.3})
        self.assertEqual(groups[U[1]]['occurrences'][0]['layers'],['F.Cu','B.Cu'])
        # Spans are byte offsets into the latin-1 view and the digest is of exactly those bytes.
        raw=board_bytes(text);a,b=first['span']
        self.assertEqual(raw[a:b].decode('latin-1'),seg(U[0],x=0).strip('\t\n'))
        self.assertEqual(first['block_sha256'],digest(raw[a:b].decode('latin-1')))
        self.assertEqual(inventory(text),inventory(text))

    def test_arcs_count_as_copper(self):
        arc='\t(arc\n\t\t(start 0 0)\n\t\t(mid 1 1)\n\t\t(end 2 0)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "A")\n\t\t(uuid "'+U[4]+'")\n\t)\n'
        inv=inventory(board(arc,seg(U[4])))
        self.assertEqual(inv['counts'],{'arc':1,'segment':1});self.assertEqual(inv['duplicate_groups'][0]['kinds'],['arc','segment'])

    def test_require_unique_refuses_only_selected_ambiguous_ids(self):
        groups={U[0]:[1,2],U[1]:[3]}
        require_unique(groups,[U[1]],'x');require_unique(groups,[],'x');require_unique(groups,['missing'],'x')
        with self.assertRaisesRegex(ValueError,'repair cut.*ambiguous.*'+U[0]):require_unique(groups,[U[1],U[0]],'repair cut')

    def test_check_binds_by_path_and_exact_group_bytes_not_by_whole_board_bytes(self):
        path='boards/x/x.kicad_pcb';text=board(seg(U[0]),seg(U[0],x=2),seg(U[1]))
        inv=inventory(text,path);entry=ci.allowlist_entry(path,inv['sha256'],inv['duplicate_groups'])
        self.assertEqual(entry['recorded_board_sha256'],digest(text))
        allowlist={'boards':[entry]}
        self.assertEqual(check(text,allowlist,path)['violations'],[])
        self.assertEqual(check(text,{'boards':[]},path)['violations'][0]['reason'],'duplicate copper UUID not in the legacy allowlist for this board path')
        self.assertEqual(len(check(text,allowlist,'boards/y/y.kicad_pcb')['violations']),1)
        # Bytes outside the group may change (an additive adoption): the entry still binds.
        elsewhere=board(seg(U[0]),seg(U[0],x=2),seg(U[1],width=0.3),seg(U[4],x=9)).replace('20250000','20250001')
        self.assertNotEqual(digest(elsewhere),digest(text));self.assertEqual(check(elsewhere,allowlist,path)['violations'],[])
        # A changed occurrence inside the group fails, as does a new group or a vanished group.
        changed=text.replace('(width 0.2)','(width 0.3)',1)
        self.assertEqual(check(changed,allowlist,path)['violations'][0]['reason'],'allowlisted duplicate group bytes changed')
        extra=board(seg(U[0]),seg(U[0],x=2),seg(U[1]),seg(U[1],x=3))
        self.assertEqual([v['uuid'] for v in check(extra,allowlist,path)['violations']],[U[1]])
        gone=board(seg(U[0]),seg(U[1]))
        self.assertEqual(check(gone,allowlist,path)['violations'][0]['reason'],'allowlisted duplicate group is absent from the board')
        third=board(seg(U[0]),seg(U[0],x=2),seg(U[0],x=3),seg(U[1]))
        self.assertEqual(check(third,allowlist,path)['violations'][0]['reason'],'allowlisted duplicate group bytes changed')

    def test_canonical_k_board_carries_exactly_the_six_known_legacy_groups(self):
        text=load_board_text(K_BOARD);inv=inventory(text,'boards/osc-core/osc-core.kicad_pcb')
        self.assertEqual(inv['sha256'],K_SHA)
        self.assertEqual({g['uuid']:g['kinds'][0] for g in inv['duplicate_groups']},K_GROUPS)
        for g in inv['duplicate_groups']:
            self.assertEqual(g['count'],2);self.assertEqual(g['nets'],['AGND']);self.assertEqual(len(g['kinds']),1)
            self.assertNotEqual(g['occurrences'][0]['geometry'],g['occurrences'][1]['geometry'])
        self.assertEqual(sum(1 for g in inv['duplicate_groups'] if g['kinds']==['via']),1)

    def test_every_tracked_board_passes_the_committed_legacy_allowlist(self):
        allowlist=ci.load_allowlist();boards=ci.canonical_boards()
        self.assertIn(K_BOARD,boards)
        results={b.relative_to(ROOT).as_posix():check(load_board_text(b),allowlist,b.relative_to(ROOT)) for b in boards}
        self.assertEqual({k:r['violations'] for k,r in results.items() if r['violations']},{})
        self.assertEqual({k:r['duplicate_groups'] for k,r in results.items() if r['duplicate_groups']},{'boards/osc-core/osc-core.kicad_pcb':6})
        entry=[e for e in allowlist['boards'] if e['path']=='boards/osc-core/osc-core.kicad_pcb']
        self.assertEqual(len(entry),1);self.assertEqual({g['uuid'] for g in entry[0]['groups']},set(K_GROUPS))
        self.assertEqual(entry[0]['recorded_board_sha256'],K_SHA)
        self.assertTrue(all(b.is_file() and b.suffix=='.kicad_pcb' and len(b.relative_to(ROOT).parts)==3 for b in boards))

    def test_check_cli_exits_nonzero_for_an_unlisted_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'dup.kicad_pcb';p.write_bytes(board_bytes(board(seg(U[0]),seg(U[0],x=2))))
            run=lambda *a:subprocess.run([sys.executable,'-m','scripts.pcbgen.copper_identity',*a],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(run('check',str(p)).returncode,1)
            self.assertEqual(run('check',str(K_BOARD)).returncode,0)
            inv=json.loads(run('inventory',str(p)).stdout)
            self.assertIsInstance(inv,list);self.assertEqual(len(inv[0]['duplicate_groups']),1)
            both=json.loads(run('inventory',str(p),str(p)).stdout);self.assertEqual(len(both),2)


class RemovalAmbiguityTests(unittest.TestCase):
    def test_text_removal_refuses_ambiguous_and_missing_ids_before_dropping(self):
        text=board(seg(U[0]),seg(U[0],x=2),seg(U[1]),via(U[2]))
        self.assertEqual(drop_copper_blocks(text,[]),text)
        out=drop_copper_blocks(text,[U[1],U[2]])
        self.assertEqual(len(copper_objects(out)),2);self.assertEqual(out.count(U[0]),2)
        with self.assertRaisesRegex(ValueError,'grid_apply removal.*ambiguous.*'+U[0]):drop_copper_blocks(text,[U[0],U[1]],'grid_apply removal')
        with self.assertRaisesRegex(ValueError,'not found: 1/2'):drop_copper_blocks(text,[U[1],U[5]])
        self.assertEqual(out.count(U[0]),2)

    def test_shard_merge_refuses_a_removal_of_a_duplicate_id(self):
        from scripts.pcbgen.route_shards import merge_text
        base=board(seg(U[0]),seg(U[0],x=2),seg(U[1],'B'))
        d={'base_sha256':'x','removed':[{'uuid':U[0],'net':'A'}],'added':[],'nets':['A']}
        with self.assertRaisesRegex(ValueError,'shard merge removal.*ambiguous'):merge_text(base,[d])
        ok={'base_sha256':'x','removed':[{'uuid':U[1],'net':'B'}],'added':[],'nets':['B']}
        self.assertEqual(merge_text(base,[ok]).count(U[0]),2)
        # The guard uses the lightweight span grouper, so a block without a net token is still merged.
        netless=board(seg(U[1],'B').replace('\t\t(net "B")\n',''),seg(U[2],'C'))
        self.assertNotIn(U[2],merge_text(netless,[{'base_sha256':'x','removed':[{'uuid':U[2],'net':'C'}],'added':[],'nets':['C']}]))
        from scripts.pcbgen.route_shards import copper_blocks
        with self.assertRaisesRegex(ValueError,'unique copper view.*ambiguous'):copper_blocks(base)
        self.assertEqual(set(copper_blocks(board(seg(U[1],'B')))),{U[1]})

    def test_stage_removed_uuids_refuses_a_removed_duplicate_occurrence(self):
        from scripts.pcbgen.audit_added_mask import stage_removed_uuids,reviewed_copper_removals,StageRemovals
        before=board(seg(U[0]),seg(U[0],x=2),seg(U[1]),via(U[2]))
        self.assertEqual(list(stage_removed_uuids(before,board(seg(U[0]),seg(U[0],x=2),via(U[2])))),[U[1]])
        with self.assertRaisesRegex(ValueError,'stage removal scope.*ambiguous'):stage_removed_uuids(before,board(seg(U[0]),seg(U[1]),via(U[2])))
        with self.assertRaisesRegex(ValueError,'reviewed cut.*ambiguous'):reviewed_copper_removals(before,board(seg(U[0]),seg(U[1]),via(U[2])),[U[0]])
        with self.assertRaisesRegex(ValueError,'stage removal.*ambiguous'):
            reviewed_copper_removals(before,board(seg(U[0]),seg(U[1]),via(U[2])),StageRemovals([U[0]]))
        # Identical duplicate bytes are just as ambiguous as distinct ones.
        twins=board(seg(U[0]),seg(U[0]),seg(U[1]))
        with self.assertRaisesRegex(ValueError,'ambiguous'):stage_removed_uuids(twins,board(seg(U[0]),seg(U[1])))

    def test_repair_selection_and_bounds_refuse_an_ambiguous_cut(self):
        try:from scripts.pcbgen.route_jack_grid import repair_nets,repair_selection,repair_bounds
        except ModuleNotFoundError as e:self.skipTest(f'NOT RUN: {e}')
        dump={'pads':[{'uuid':'pad','net':'T','xy':[5e6,5e6]}],'islands':{'T':[['pad'],['other']]},
              'tracks':[{'uuid':U[0],'net':'X','a':[4e6,5e6],'b':[6e6,5e6],'width':.2e6},{'uuid':U[0],'net':'Y','a':[4e6,6e6],'b':[6e6,6e6],'width':.2e6},
                        {'uuid':U[1],'net':'X','a':[4e6,4e6],'b':[6e6,4e6],'width':.2e6}],
              'vias':[{'uuid':U[1],'net':'Z','xy':[5e6,5e6],'diameter':.6e6}]}
        self.assertEqual(repair_nets({**dump,'vias':[]},['T'],{U[1]}),['T','X'])
        for cut in ({U[0]},{U[1]},{U[0],U[1]}):
            with self.subTest(cut=cut),self.assertRaisesRegex(ValueError,'repair cut.*ambiguous'):repair_nets(dump,['T'],cut)
            with self.assertRaisesRegex(ValueError,'ambiguous'):repair_selection(dump,{'repair':True,'repair_targets':['T'],'repair_source_uuids':sorted(cut)})
            with self.assertRaisesRegex(ValueError,'repair cut.*ambiguous'):
                repair_bounds(dump,{'repair_source_uuids':sorted(cut),'repair_bounds_mm':[3,3,7,7]},['T'],cut)
        clean={**dump,'tracks':dump['tracks'][2:],'vias':[]}
        with self.assertRaisesRegex(ValueError,'unknown source copper'):repair_nets(clean,['T'],{U[5]})
        # repair_bounds reaches repair_nets first, so an absent cut is named there; its own branch stays defensive.
        with self.assertRaisesRegex(ValueError,'unknown source copper'):
            repair_bounds(clean,{'repair_source_uuids':[U[5]],'repair_bounds_mm':[3,3,7,7]},['T'],{U[5]})


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.text=board(seg(U[0]),seg(U[0],x=2),via(U[1]),via(U[1],x=5),seg(U[2]),via(U[2],x=7),seg(U[3]),seg(U[0],x=4))

    def test_later_occurrences_are_renamed_deterministically_and_the_first_keeps_its_id(self):
        manifest,out=propose_normalization(self.text,'synthetic')
        again,out2=propose_normalization(self.text,'synthetic')
        self.assertEqual((manifest,out),(again,out2))
        self.assertEqual([(r['old_uuid'],r['occurrence_index']) for r in manifest['renames']],[(U[0],1),(U[0],2),(U[1],1),(U[2],1)])
        self.assertEqual(len({r['new_uuid'] for r in manifest['renames']}),4)
        self.assertEqual(out.count(U[0]),1);self.assertEqual(out.count(U[1]),1);self.assertEqual(out.count(U[2]),1)
        self.assertEqual(copper_objects(out)[0]['uuid'],U[0])  # first occurrence unchanged
        self.assertEqual(duplicate_groups(copper_objects(out)),[])
        self.assertEqual(manifest['input_board_sha256'],digest(self.text));self.assertEqual(manifest['output_board_sha256'],digest(out))
        # A different input board derives different new ids even for the same old id and index.
        other,_=propose_normalization(self.text.replace('(version 20250000)','(version 20250001)'))
        self.assertNotEqual(manifest['renames'][0]['new_uuid'],other['renames'][0]['new_uuid'])

    def test_proposal_is_idempotent_and_the_proof_reconstructs_the_output_bytewise(self):
        manifest,out=propose_normalization(self.text)
        proof=verify_normalization(self.text,out,manifest)
        self.assertEqual((proof['renames'],proof['objects'],proof['duplicate_groups_before'],proof['duplicate_groups_after']),(4,8,3,0))
        self.assertEqual(proof['differing_bytes'],proof['renamed_token_bytes']);self.assertGreater(proof['differing_bytes'],0)
        second,out2=propose_normalization(out)
        self.assertEqual(second['renames'],[]);self.assertEqual(out2,out)
        self.assertEqual(board_bytes(apply_manifest(self.text,manifest)),board_bytes(out))
        self.assertEqual(propose_normalization(board(seg(U[0])))[0]['renames'],[])

    def test_stale_or_tampered_manifests_and_proposals_are_refused(self):
        manifest,out=propose_normalization(self.text)
        with self.assertRaisesRegex(ValueError,'different board'):apply_manifest(self.text.replace('(width 0.2)','(width 0.3)',1),manifest)
        tampered=json.loads(json.dumps(manifest));tampered['renames'][0]['block_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'block digest'):apply_manifest(self.text,tampered)
        moved=json.loads(json.dumps(manifest));moved['renames'][0]['old_uuid']=U[5]
        with self.assertRaisesRegex(ValueError,'UUID token mismatch'):apply_manifest(self.text,moved)
        swapped=json.loads(json.dumps(manifest));swapped['renames'][0]['new_uuid']=swapped['renames'][1]['new_uuid']
        with self.assertRaisesRegex(ValueError,'collides with an existing token'):apply_manifest(self.text,swapped)
        malformed=json.loads(json.dumps(manifest));malformed['renames'][0]['new_uuid']='not-a-uuid'
        with self.assertRaisesRegex(ValueError,'new UUID invalid'):apply_manifest(self.text,malformed)
        redirected=json.loads(json.dumps(manifest));redirected['renames'][0]['new_uuid']=U[6]
        with self.assertRaisesRegex(ValueError,'output digest'):apply_manifest(self.text,redirected)
        # A new id equal to an existing non-copper token (the gr_text uuid) or to a surviving copper id is a new duplicate.
        for existing in (U[9],U[3]):
            aliased=json.loads(json.dumps(manifest));aliased['renames'][0]['new_uuid']=existing
            with self.subTest(existing=existing),self.assertRaisesRegex(ValueError,'collides with an existing token'):apply_manifest(self.text,aliased)
        with self.assertRaisesRegex(ValueError,'collides'):ci.rebuild(self.text,aliased)
        with self.assertRaisesRegex(ValueError,'schema'):apply_manifest(self.text,{**manifest,'schema':'other'})
        # Malformed manifests are ValueErrors, never KeyError/TypeError/IndexError.
        without=dict(manifest);del without['renames']
        with self.assertRaisesRegex(ValueError,'missing renames'):apply_manifest(self.text,without)
        partial=json.loads(json.dumps(manifest));del partial['renames'][0]['uuid_span']
        with self.assertRaisesRegex(ValueError,'rename 0 missing or malformed uuid_span'):apply_manifest(self.text,partial)
        for bad in ('not a dict',{**manifest,'renames':'x'},{**manifest,'renames':[1]},{**manifest,'input_board_sha256':None}):
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'normalization manifest'):ci.rebuild(self.text,bad)
        short=json.loads(json.dumps(manifest));short['renames'][0]['span']=[1]
        with self.assertRaisesRegex(ValueError,'malformed span'):apply_manifest(self.text,short)
        # Every rename must target a later occurrence of a duplicated copper UUID: never a unique
        # copper id, a first occurrence, or a non-copper block, even with consistent digests.
        objects={o['uuid']:o for o in copper_objects(self.text) if o['uuid'] in (U[3],)}
        first=next(o for o in copper_objects(self.text) if o['uuid']==U[0])
        text_block=next((a,b) for a,b in ci.top_level_spans(self.text) if self.text[a:b].startswith('(gr_text'))
        text_uuid=[text_block[0]+m.start(1) for m in [ci.UUID_RE.search(self.text[text_block[0]:text_block[1]])]][0]
        targets={'unique copper':(U[3],0,objects[U[3]]['span'],objects[U[3]]['uuid_span'],objects[U[3]]['block_sha256']),
                 'first occurrence':(U[0],0,first['span'],first['uuid_span'],first['block_sha256']),
                 'non-copper block':(U[9],0,list(text_block),[text_uuid,text_uuid+36],digest(self.text[text_block[0]:text_block[1]]))}
        for name,(old,index,span,uspan,bsha) in targets.items():
            new='11111111-1111-4111-8111-%012d'%index
            forged={**manifest,'renames':[{'old_uuid':old,'occurrence_index':index,'kind':'x','net':None,'layers':[],'geometry':{},
                                           'block_sha256':bsha,'span':span,'uuid_span':uspan,'new_uuid':new}]}
            forged_out=ci.replace_spans(self.text,[(uspan[0],uspan[1],new)]);forged['output_board_sha256']=digest(forged_out)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'does not target a later duplicate copper occurrence'):
                verify_normalization(self.text,forged_out,forged)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'does not target a later duplicate'):apply_manifest(self.text,forged)
        # The proof requires the differing bytes to equal the renamed token bytes exactly.
        with self.assertRaisesRegex(ValueError,'differ'):verify_normalization(self.text,out.replace('(width 0.2)','(width 0.3)',1),manifest)
        with self.assertRaisesRegex(ValueError,'differ'):verify_normalization(self.text,out+'\n',manifest)

    def test_a_duplicate_referenced_outside_its_copper_refuses_normalization(self):
        group='\t(group "stitch"\n\t\t(uuid "'+U[7]+'")\n\t\t(members\n\t\t\t'+U[0]+'\n\t\t\t'+U[3]+'\n\t\t)\n\t)\n'
        text=board(seg(U[0]),seg(U[0],x=2),seg(U[3]),group)
        with self.assertRaisesRegex(ValueError,U[0]+'.*referenced outside.*group/members@.*refused'):propose_normalization(text)
        refs=ci.foreign_references(text,U[0],[tuple(o['uuid_span']) for o in duplicate_groups(copper_objects(text))[0]['occurrences']])
        self.assertEqual([(r['block'],r['context'],r['quoted']) for r in refs],[('group','members',False)])
        # A quoted parenthesis before the reference does not change the enclosing form, and a quoted hit says so.
        quoted='\t(gr_text "see ('+U[0]+') here" (uuid "'+U[8]+'"))\n'
        hit=ci.foreign_references(board(seg(U[0]),seg(U[0],x=2),quoted),U[0],[tuple(o['uuid_span']) for o in duplicate_groups(copper_objects(board(seg(U[0]),seg(U[0],x=2),quoted)))[0]['occurrences']])
        self.assertEqual([(r['block'],r['context'],r['quoted']) for r in hit],[('gr_text','gr_text',True)])
        # A manifest made for the same bytes without the members reference cannot be verified against a referencing board.
        manifest,out=propose_normalization(board(seg(U[0]),seg(U[0],x=2),seg(U[3])))
        referenced_manifest={**manifest,'input_board_sha256':digest(text),'output_board_sha256':digest(text)}
        with self.assertRaises(ValueError):verify_normalization(text,text,referenced_manifest)
        # A bare id in a text string counts too; a non-duplicate id in a members list does not block anything.
        with self.assertRaisesRegex(ValueError,'gr_text'):propose_normalization(board(seg(U[0]),seg(U[0],x=2),'\t(gr_text "'+U[0]+'" (uuid "'+U[8]+'"))\n'))
        self.assertEqual(len(propose_normalization(board(seg(U[0]),seg(U[0],x=2),seg(U[3]),group.replace(U[0],U[8])))[0]['renames']),1)

    def test_cli_writes_only_into_out_and_never_under_boards(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'in'/'dup.kicad_pcb';src.parent.mkdir();src.write_bytes(board_bytes(self.text))
            run=lambda *a:subprocess.run([sys.executable,'-m','scripts.pcbgen.copper_identity',*a],cwd=ROOT,capture_output=True,text=True)
            r=run('propose-normalization',str(src),'--out',str(Path(d)/'prop'));self.assertEqual(r.returncode,0,r.stderr)
            manifest=json.loads((Path(d)/'prop/manifest.json').read_text());proposal=load_board_text(Path(d)/'prop/dup.kicad_pcb')
            self.assertEqual(len(manifest['renames']),4);self.assertEqual(digest(proposal),manifest['output_board_sha256'])
            self.assertEqual(src.read_bytes(),board_bytes(self.text))
            r=run('verify',str(src),str(Path(d)/'prop/dup.kicad_pcb'),str(Path(d)/'prop/manifest.json'));self.assertEqual(r.returncode,0,r.stderr)
            r=run('apply-manifest',str(src),str(Path(d)/'prop/manifest.json'),'--out',str(Path(d)/'apply/dup.kicad_pcb'));self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual((Path(d)/'apply/dup.kicad_pcb').read_bytes(),board_bytes(proposal))
            # Point the refusal at a boards/ tree inside the temporary directory, never at the canonical one.
            fake_root=Path(d)/'repo';(fake_root/'boards/x').mkdir(parents=True)
            with patch.object(ci,'ROOT',fake_root):
                for out in (fake_root/'boards/x/proposal',fake_root/'boards',fake_root/'boards/x/../y'):
                    with self.subTest(out=out),self.assertRaisesRegex(SystemExit,'refusing'):ci.main(['propose-normalization',str(src),'--out',str(out)])
                with self.assertRaisesRegex(SystemExit,'refusing'):ci.main(['apply-manifest',str(src),str(Path(d)/'prop/manifest.json'),'--out',str(fake_root/'boards/x/dup.kicad_pcb')])
                self.assertEqual(ci.main(['propose-normalization',str(src),'--out',str(fake_root/'elsewhere')]),0)
            self.assertEqual(sorted(p.name for p in (fake_root/'boards/x').iterdir()),[])
            with self.assertRaisesRegex(SystemExit,'refusing'):ci.refuse_boards_dir(ROOT/'boards/osc-core/proposal')


if __name__=='__main__':unittest.main()
