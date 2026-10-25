"""Receipt failure boundaries for the single admitted route. No native calls."""
import copy
import unittest
from unittest.mock import patch
import run_route_1438 as run


class Route1438Tests(unittest.TestCase):
    def receipt(self):
        worker='o1-two-a-r1438-123-1';slice_name='epic242-w'+worker.encode().hex()+'.slice'
        plan={'worker':worker,'admission_id':run.ADMISSION,'sha':run.host.METHOD,'seconds':300,
              'command':['reviewed-payload'],'memory_max':6442450944,'memory_swap_max':0,
              'aggregate_memory_max':12884901888,'free_floor':2147483648,'early_abort_free':2684354560,
              'hook_sha256':'f91b2c8846856a6d38a10eb9e6314b6ebec3222b68df37942f3716ab860d8c91'}
        d={'plan':plan,'status':'COMMAND PASS ONLY; native acceptance requires exact complete evidence',
           'final_owned_state':{'workload_absent':True},'container_admissions':{},'container_memberships':{},'container_states':{}}
        for cid in ('a'*64,'b'*64):
            d['container_admissions'][cid]={'request':{'command':['kicad-cli','version'],'worker':worker,'token':'token','container_id':cid},'ack':'token:'+cid}
            d['container_memberships'][cid]={'worker':worker,'container_id':cid,'host_config':{'Memory':6442450944,'MemorySwap':6442450944,'CgroupParent':slice_name},'cgroup':'0::/epic242.slice/'+slice_name+'/docker-'+cid+'.scope'}
            d['container_states'][cid]={'Status':'exited','Running':False,'ExitCode':0,'OOMKilled':False,'Error':''}
        d['observed_containers']=list(d['container_admissions'])
        return d

    def summary(self,guard=None,proposal=None,code=0,unchanged=True):
        return run.result_summary(guard or self.receipt(),proposal or {'copper':[],'removed_uuids':[]},code,unchanged,['reviewed-payload'])

    def test_zero_additions_is_no_improvement_not_acceptance(self):
        result=self.summary()
        self.assertTrue(result['command_pass'])
        self.assertEqual(result['status'],'NO IMPROVEMENT')

    def test_missing_retained_exit_or_ack_blocks(self):
        for mutate in (lambda d:d['container_states'].pop('a'*64),
                       lambda d:d['container_admissions']['a'*64].update(ack='wrong'),
                       lambda d:d['container_memberships']['a'*64]['host_config'].update(Memory=1)):
            d=self.receipt();mutate(d)
            self.assertFalse(self.summary(d)['command_pass'])

    def test_timeout_cleanup_input_drift_and_cuts_block(self):
        self.assertFalse(self.summary(code=124)['command_pass'])
        self.assertFalse(self.summary(unchanged=False)['command_pass'])
        self.assertFalse(self.summary(proposal={'copper':[],'removed_uuids':['cut']})['command_pass'])
        d=self.receipt();d['final_owned_state']['workload_absent']=False
        self.assertFalse(self.summary(d)['command_pass'])

    def test_native_budget_cannot_expand(self):
        for key,value in [('seconds',301),('memory_swap_max',1),('free_floor',1)]:
            d=self.receipt();d['plan'][key]=value
            self.assertFalse(self.summary(d)['command_pass'])

    def test_workflow_rerun_rejected_before_any_source_or_native_call(self):
        env={'PARENT_ADMISSION_ID':run.ADMISSION,'GITHUB_REPOSITORY':run.REPOSITORY,
             'GITHUB_REF_NAME':run.BRANCH,'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted',
             'GITHUB_RUN_ID':'123','GITHUB_RUN_ATTEMPT':'2'}
        with patch.dict(run.os.environ,env,clear=True):
            with self.assertRaisesRegex(ValueError,'first-attempt'):
                run.request(None)


if __name__=='__main__':unittest.main()
