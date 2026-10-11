# Reviewed coordination update

Verified lane assignment source: `1da1909846dc3255888ecd36c88cee9737c85834`. Hardware epoch remains epic242-e0. #244, #250 and #251 sessions are recorded in ownership.json; source/evidence preparation only, with zero native admission. #250 reported startup-blocked.

## Startup diagnosis

Both runtime restoration and the personal loader were denied because they access `/root/.codex`. No alternate startup path was established or independently authorized. Repository AGENTS/WORKFLOW and tracked skills were read directly; this does not prove managed startup success or waive a stop rule. The reported `/workspace/AGENTS.md` bridge to `/home/agent/.codex/cloud-profile/current/AGENTS.md` is not verified installed-profile access and must not be used to evade the denial. Keep #250 blocked pending an explicit user waiver of optional personal-profile loading for repository-only work. No retry, forbidden-access escalation, runtime/config change or installer fallback is proposed.

## PR261 source acceptance

Reviewed source `7aba720c1246d6ec3f02909af6fb08dc774b3d31`, exactly eight owned files, integrated by cherry-pick. Independent review passed deterministic inventory and all eleven focused tests, source intent for 100 trimmers / 28 roles, and all 23 gap records (Ref, role, resistance, native pins, blank MPN, same-value candidates). No existing hardware input changed. LABEL_CONTRACT_READY: #249 can start from the integration commit containing this update.

Manufacturer primary TC33 PDF downloaded independently from https://www.bourns.com/docs/product-datasheets/tc33.pdf; SHA256 `b13258ee9f777b70198554ad4ed43cab2167b2bdf31bdcbe52c4956bfff1adbf` matches retained TC33X.pdf. Page-one drawing was rendered and inspected: nominal terminal-inclusive 3.6 x 3.8 x 1.2 mm with general +/-0.3 mm tolerance supports conservative 3.9 x 4.1 x 1.5 mm. Codes 203/503/504 correspond to 20k/50k/500k; +/-25%, 270 +/-20 degree adjustment and tool constraints match review. Conservative envelope does not establish fit in the current 5.3 x 3.9 mm courtyard: orientation, installed height, back-face access, tool clearance and pad qualification remain open. COMPONENT_REVIEW_READY means completed dispositions only. No MPN selected, no production fit/calibration/native acceptance.

## Scoped CI scheduling proposal (not applied)

`ci-scheduling-proposal.patch` proposes only existing workflow concurrency and board job scheduling: share the existing audit controller group with cancellation disabled; run python/native suite before board DRC; cap the DRC matrix at two. Preserve triggers, all checks, matrix boards, severities and timeouts. No workflow dispatch or actual workflow change occurred.

GitHub concurrency serializes same-group workflows within this repository, but a single pending run can be replaced by a later one: parent should admit only one queued workflow. See https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency and https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations .

This patch is NOT execution-ready by itself. `max-parallel` cannot enforce memory or free-memory floor. Parent must reserve both global native slots for the complete admitted workflow, exclude all other routing/local jobs outside this group, and establish each worker's 6 GiB cap / 12 GiB aggregate / 2 GiB free guard before execution. Current Docker wrapper lacks these caps; a separately reviewed narrow resource guard is still required. Existing timeguards remain mandatory. Documentation/build resources must also be accounted for. Only after those prerequisites and parent review should a reviewed workflow commit be pushed without skip-ci; then retain full job evidence. Do not dispatch the current default potentially four-native workflow. A skipped dependent job after failure is not acceptance.
