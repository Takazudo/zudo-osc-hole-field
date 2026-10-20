"""Check quoted zudo-pd values against the pinned commit (read-only).

Usage: verify_pd_pin.py PATH_TO_ZUDO_PD_CHECKOUT
Without a checkout this prints NOT RUN and exits 2; it never fetches or edits.
"""
from pathlib import Path
import hashlib, json, subprocess, sys

HERE = Path(__file__).resolve().parent


def show(repo, commit, path):
    return subprocess.run(['git', '-C', repo, 'show', f'{commit}:{path}'], capture_output=True, check=True).stdout


def main():
    if len(sys.argv) < 2 or not Path(sys.argv[1], '.git').exists():
        print('NOT RUN: no zudo-pd checkout given')
        return 2
    repo = sys.argv[1]
    sup = json.loads((HERE / 'supply-input.json').read_text())
    c = sup['commit']
    for path, digest in sup['pd_source_sha256'].items():
        assert hashlib.sha256(show(repo, c, path)).hexdigest() == digest, 'hash ' + path
    pb = json.loads(show(repo, c, 'manufacturing/power-budget.json'))
    w = pb['whole_chain_current_thermal_screen']
    ch = sup['chain']
    assert pb['pd_contract']['nominal_power_w'] == sup['input_boundary_W']['nominal_15V_3A']
    assert pb['pd_contract']['minus5pct_source_power_w'] == sup['input_boundary_W']['source_minus_5_percent']
    assert ch['+12V']['pre_rail_min_V'] == pb['positive_pre_regulator_screen']['bounds']['minimum_v']
    assert ch['-12V']['pre_rail_min_V'] == pb['negative_stage_scenarios'][3]['bounds']['minimum_v']
    assert ch['+5V']['pre_rail_min_V'] == w['plus5_pre_hot_tolerance_bounds']['minimum_v']
    assert ch['+12V']['output_conditional_V'] == [w['plus12_output_band_conditional'][k] for k in ('minimum_v', 'maximum_v')]
    assert ch['+5V']['output_conditional_V'] == [w['plus5_output_band_conditional'][k] for k in ('minimum_v', 'maximum_v')]
    assert ch['-12V']['output_conditional_V'] == [w['minus12_output_band_conditional'][k] for k in ('minimum_magnitude_v', 'maximum_magnitude_v')]
    assert sup['pd_screen_at_design_targets']['minimum_weighted_converter_efficiency_at_14V_3A'] == w['minimum_weighted_converter_efficiency_at14v_3a']
    assert sup['pd_screen_at_design_targets']['pre_regulator_power_W_total'] == w['pre_regulator_power_w']['total']
    facts = {}
    for skill in ('component-ptc-smd1210p200tf-c20808', 'component-ptc-msmd110-33v-c70119',
                  'component-ptc-bsmd1206-150-16v-c883133'):
        for f in json.loads(show(repo, c, f'.claude/skills/{skill}/facts.json'))['facts']:
            facts[f['fact_id']] = f['value']
    for rail, prefix in (('+12V', 'ptc1b'), ('+5V', 'ptc2'), ('-12V', 'ptc3')):
        ptc = ch[rail]['ptc']
        assert ptc['ihold_A_25C'] == facts[f'fact-{prefix}-ihold'] and ptc['itrip_A_25C'] == facts[f'fact-{prefix}-itrip'], rail
    assert ch['-12V']['ptc']['ihold_A_85C'] == facts['fact-ptc3-hold-85c'] and ch['-12V']['ptc']['r1max_ohm'] == facts['fact-ptc3-r1max']
    assert ch['+5V']['ptc']['r1max_ohm'] == facts['fact-ptc2-r1max']
    print('PASS pinned zudo-pd quotation at', c)
    return 0


if __name__ == '__main__':
    sys.exit(main())
