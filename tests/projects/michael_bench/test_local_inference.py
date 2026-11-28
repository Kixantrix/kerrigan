"""Offline synthetic provider; never connects to the operational model server."""
import subprocess
import json

import pytest

from benchmarks.michael.replay_trial import api


def test_local_condition_tool_loop_and_unknown_usage_offline():
    script = """
import assert from 'node:assert/strict';
import {localLoop,validateLocalCondition,LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,
 concurrency:1,grading:'after-window-release'};
assert.throws(()=>validateLocalCondition({...condition,endpoint:'http://example.test/v1'}),/endpoint/);
assert.throws(()=>validateLocalCondition({...condition,concurrency:2}),/condition/);
const records=[],calls=[];let requests=0,boundaries=0,sessionId;
await assert.rejects(()=>localLoop({condition,prompt:'synthetic',tools:[],signal:new AbortController().signal,
 clock:()=>1000,boundary:async()=>{boundaries++},record:r=>records.push(r),
 execute:async(id,args)=>{calls.push(args);return {exitCode:0}},
 fetcher:async(url,options)=>{
  const body=JSON.parse(options.body);assert.equal(body.max_tokens,16384);
  if(!requests)sessionId=options.headers['x-mtplx-session-id'];
  assert.match(sessionId,/^mbr3-synthetic-[0-9a-f-]{36}$/);
  assert.equal(options.headers['x-mtplx-session-id'],sessionId);
  if(requests)assert.equal(body.messages.at(-1).role,'tool');
  const message=requests++===0?{role:'assistant',content:null,tool_calls:[
   {type:'function',id:'tool-1',function:{name:'mb_action',arguments:'{"op":"read","path":"TASK.md"}'}}]}:
   {role:'assistant',content:'done'};
  return new Response(JSON.stringify({id:options.headers['x-mtplx-request-id'],model:'synthetic-only',
    choices:[{message}],usage:requests===1?{prompt_tokens:12,completion_tokens:3,total_tokens:15}:undefined}));
 }}),/ambiguous_native_fit/);
assert.equal(requests,2);assert.equal(boundaries,4);assert.equal(calls[0].op,'read');
assert.equal(records.filter(r=>r.type==='local_request_finished')[1].usage,null);
assert.equal(records.filter(r=>r.type==='local_request_finished')[0].usage.inputTokens,12);
assert(records.filter(r=>r.type==='local_request_started').every(r=>r.sessionId===sessionId));
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)


def test_local_identity_mismatch_and_busy_boundary_fail_before_tools():
    script = """
import assert from 'node:assert/strict';
import {localLoop,LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,
 concurrency:1,grading:'after-window-release'};
const base={condition,prompt:'synthetic',tools:[],signal:new AbortController().signal,clock:()=>1000,
 record:()=>{},execute:async()=>{throw Error('should never execute')}};
await assert.rejects(()=>localLoop({...base,boundary:async()=>{throw Error('ownership ambiguous')},
 fetcher:async()=>{throw Error('must not fetch')}}),/ownership ambiguous/);
const records=[];
await assert.rejects(()=>localLoop({...base,record:r=>records.push(r),boundary:async()=>{},
 fetcher:async()=>new Response(JSON.stringify({id:'wrong',model:'synthetic-only',choices:[]}))}),/identity/);
assert.equal(records.at(-1).type,'local_request_failed');
assert.equal(records.at(-1).reason,'local_response_identity_or_shape');
assert(records.at(-1).wallMs>=0);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)


def test_local_unknown_or_invalid_usage_never_executes_generated_tools():
    script = """
import assert from 'node:assert/strict';
import {localLoop,LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,
 concurrency:1,grading:'after-window-release'};
const base={condition,prompt:'synthetic',tools:[],signal:new AbortController().signal,clock:()=>1000,
 record:()=>{},boundary:async()=>{},execute:async()=>{throw Error('must not execute')}};
for(const [usage,reason] of [[undefined,/ambiguous_native_fit/],
 [{prompt_tokens:-1,completion_tokens:2,total_tokens:1},/usage_shape/],
 [{prompt_tokens:1,completion_tokens:2,total_tokens:4},/context_budget/],
 [{prompt_tokens:3,completion_tokens:1,total_tokens:4,
   prompt_tokens_details:{cached_tokens:4}},/context_budget/],
 [{prompt_tokens:229377,completion_tokens:1,total_tokens:229378},/context_budget/]]) {
 await assert.rejects(()=>localLoop({...base,fetcher:async(url,options)=>new Response(JSON.stringify({
  id:options.headers['x-mtplx-request-id'],model:'synthetic-only',usage,
  choices:[{message:{role:'assistant',tool_calls:[{type:'function',id:'t',
    function:{name:'mb_action',arguments:'{"op":"read","path":"TASK.md"}'}}]}}]}))}),reason);
}
await assert.rejects(()=>localLoop({...base,prompt:'x'.repeat(229377),
 fetcher:async()=>{throw Error('must not request')}}),/context_budget/);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)


def test_offline_window_health_projection_contention_and_background_workloads():
    script = """
import assert from 'node:assert/strict';
import {localWindow} from './benchmarks/michael/local_transport/local_window.mjs';
import {LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,
 concurrency:1,grading:'after-window-release'};
let active=0,pressureState='normal',generations=0;const events=[];
const makeWindow=()=>localWindow({condition,record:r=>events.push(r),clock:()=>1000,
 snapshot:()=>({memoryPressureFreePercent:45,memoryPressureState:pressureState,loadAverage:[4,3,2],
 heavyProcesses:[{name:'Gridiron',cpuPercent:60,residentBytes:2000000000}]}),
 fetcher:async(url,options)=>{
  assert(!url.includes('snapshot')&&!url.includes('flight'));
  if(url.endsWith('/health'))return new Response(JSON.stringify({ok:true,active_requests:active}));
  if(url.endsWith('/models'))return new Response(JSON.stringify({data:[{id:'synthetic-only'}]}));
  generations++;
  return new Response(JSON.stringify({id:options.headers['x-mtplx-request-id'],model:'synthetic-only',
   usage:{prompt_tokens:10,completion_tokens:1,total_tokens:11},
   choices:[{message:{role:'assistant',content:'done'}}]}));
 }});
let window=makeWindow();
const options={prompt:'synthetic',tools:[],signal:new AbortController().signal,
 execute:async()=>{throw Error('unexpected tool')}};
active=1;await assert.rejects(()=>window.run(options),/contention/);
active=0;
await assert.rejects(()=>window.run(options),/concurrency_denied/);
await window.release();window=makeWindow();
const result=await window.run(options);
assert.equal(result.status,'completed');
assert(events.some(r=>r.resources?.heavyProcesses[0].name==='Gridiron'));
const release=await window.release();
assert.equal(release.ownedRequestsDrained,true);assert.equal(release.ownRequestIds.length,1);
assert.equal(release.attempts.length,2);
await assert.rejects(()=>window.run({}),/concurrency_denied/);
pressureState='warning';window=makeWindow();
await assert.rejects(()=>window.run(options),/resource_pressure/);
assert.equal(generations,1);await window.release();
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)


def test_window_accepts_large_diagnostic_health_but_keeps_metadata_bounded():
    script = """
import assert from 'node:assert/strict';
import {localWindow,LOCAL_METADATA_BYTES} from './benchmarks/michael/local_transport/local_window.mjs';
import {LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,
 concurrency:1,grading:'after-window-release'};
let padding=76000;
const make=()=>localWindow({condition,record:()=>{},clock:()=>1000,
 snapshot:()=>({memoryPressureFreePercent:45,memoryPressureState:'normal',loadAverage:[1,1,1],heavyProcesses:[]}),
 fetcher:async url=>{
  if(url.endsWith('/health'))return new Response(JSON.stringify({ok:true,active_requests:0,diagnostics:'x'.repeat(padding)}));
  return new Response(JSON.stringify({data:[{id:'synthetic-only'}]}));
 }});
await make().boundary();
padding=LOCAL_METADATA_BYTES;
await assert.rejects(()=>make().boundary(),/local_metadata_overflow/);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)


def test_multiple_tool_calls_in_one_response_run_sequentially_and_stay_bounded():
    script = """
import assert from 'node:assert/strict';
import {localLoop,LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,
 concurrency:1,grading:'after-window-release'};
const call=i=>({id:'c'+i,type:'function',function:{name:'mb_action',arguments:JSON.stringify({op:'read',path:'f'+i})}});
const run=async count=>{
 let turn=0;const executed=[];const bodies=[];
 const result=await localLoop({condition,prompt:'p',tools:[],signal:new AbortController().signal,
  boundary:async()=>{},record:()=>{},clock:()=>1000,
  execute:async(id,args)=>{executed.push([id,args.path]);return {ok:true}},
  fetcher:async(url,options)=>{const body=JSON.parse(options.body);bodies.push(body);turn++;
   const message=turn===1?{role:'assistant',content:null,tool_calls:Array.from({length:count},(_,i)=>call(i))}:
    {role:'assistant',content:'done'};
   return new Response(JSON.stringify({id:options.headers['x-mtplx-request-id'],model:'synthetic-only',
    usage:{prompt_tokens:10,completion_tokens:1,total_tokens:11},choices:[{message,finish_reason:'stop'}]}));}});
 return {result,executed,bodies};
};
const two=await run(2);
assert.equal(two.result.status,'completed');
assert.deepEqual(two.executed,[['c0','f0'],['c1','f1']]);
assert.deepEqual(two.bodies[1].messages.slice(-2).map(m=>[m.role,m.tool_call_id]),[['tool','c0'],['tool','c1']]);
await assert.rejects(()=>run(LOCAL_LIMITS.toolCallsPerResponse+1),/local_parallel_tools_denied/);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)


def test_scratch_scan_timeout_is_a_distinct_missed_observation(tmp_path):
    slow = tmp_path / "slow-python"
    slow.write_text("#!/bin/sh\nsleep 5\n")
    slow.chmod(0o755)
    script = f"""
import assert from 'node:assert/strict';
import {{scratchState,SCAN}} from './benchmarks/michael/local_transport/scratch.mjs';
assert(SCAN.timeoutMs >= 10000 && SCAN.consecutiveMissesAllowed === 2);
assert.throws(()=>scratchState('{tmp_path}',[0,0],'{slow}',200),e=>e.scanTimeout===true&&/scratch_scan:.*ETIMEDOUT/.test(e.message));
assert.throws(()=>scratchState('{tmp_path}',[0,0],'{tmp_path}/missing-python',200),e=>e.scanTimeout!==true);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=20)


def test_input_bound_derives_from_native_tokens_not_a_byte_cap():
    script = """
import assert from 'node:assert/strict';
import {localLoop,LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
assert(!('inputBytes' in LOCAL_LIMITS));
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,
 concurrency:1,grading:'after-window-release'};
const run=async(toolResultBytes,reportedInput)=>{
 let turn=0;const started=[];
 const result=await localLoop({condition,prompt:'p',tools:[],signal:new AbortController().signal,
  boundary:async()=>{},record:e=>{if(e.type==='local_request_started')started.push(e)},clock:()=>1000,
  execute:async()=>({data:'x'.repeat(toolResultBytes)}),
  fetcher:async(url,options)=>{turn++;
   const message=turn===1?{role:'assistant',content:null,tool_calls:[{id:'c',type:'function',
     function:{name:'mb_action',arguments:'{}'}}]}:{role:'assistant',content:'done'};
   return new Response(JSON.stringify({id:options.headers['x-mtplx-request-id'],model:'synthetic-only',
    usage:{prompt_tokens:reportedInput,completion_tokens:1,total_tokens:reportedInput+1},
    choices:[{message,finish_reason:'stop'}]}));}});
 return {result,started};
};
// 200 KB of tool output is far over the old 64 KiB cap but well inside the token guardrail.
const ok=await run(200000,1000);
assert.equal(ok.result.status,'completed');
assert(ok.started[1].inputBytes>65536 && ok.started[1].inputTokenBound<LOCAL_LIMITS.inputTokens);
// The same growth on top of a near-limit native count is refused before the request.
await assert.rejects(()=>run(200000,LOCAL_LIMITS.inputTokens-1000),/local_context_budget/);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=20)


def test_local_own_response_native_timings_ignore_derived_defaults_and_preserve_caps():
    script = """
import assert from 'node:assert/strict';
import {localLoop,LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,
 concurrency:1,grading:'after-window-release'};
for(const native of [undefined,{prompt_eval_time_s:2,new_prefill_tokens:10,cached_tokens:20,
 prefill_compute_tok_s:5,decode_elapsed_s:3,decode_tok_s:4}]) {
 const records=[];let time=0;
 const result=await localLoop({condition,prompt:'synthetic',tools:[],signal:new AbortController().signal,
  clock:()=>1000,monotonic:()=>{time+=1000;return time},boundary:async()=>{},
  execute:async()=>{throw Error('length-capped tool must not execute')},record:r=>records.push(r),
  fetcher:async(url,options)=>new Response(JSON.stringify({id:options.headers['x-mtplx-request-id'],
   model:'synthetic-only',usage:{prompt_tokens:30,completion_tokens:12,total_tokens:42,
    completion_tokens_details:{reasoning_tokens:8}},mtplx_stats:native,
   timings:{prompt_ms:0,predicted_ms:0},choices:[{finish_reason:'length',message:{role:'assistant',
    tool_calls:[{type:'function',id:'t',function:{name:'mb_action',arguments:'{}'}}]}}]}))});
 assert.equal(result.status,'output-cap');
 const receipt=records.find(r=>r.type==='local_request_finished');
 assert.equal(receipt.wallMs,1000);assert.equal(receipt.tokensPerSecond,12);
 assert.equal(receipt.usage.reasoningTokens,8);
 assert.equal(receipt.prefillSeconds,native?2:null);
 assert.equal(receipt.decodeTokensPerSecond,native?4:null);
 assert.equal(receipt.nativeStats.ttft_s,null);
}
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)


def test_local_real_http_stub_tool_loop_and_deadline_release():
    script = """
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {localWindow} from './benchmarks/michael/local_transport/local_window.mjs';
import {LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
let active=0,requests=0,stall=false,invalid=false,sessionId;const ids=new Set();
const server=createServer((req,res)=>{
 const reply=value=>{res.setHeader('content-type','application/json');res.end(JSON.stringify(value))};
 if(req.url==='/health')return reply({ok:true,active_requests:active});
 if(req.url==='/v1/models')return reply({data:[{id:'synthetic-only'}]});
 assert.equal(req.url,'/v1/chat/completions');
 assert.equal(req.method,'POST');
 const id=req.headers['x-mtplx-request-id'];
 assert(!ids.has(id));ids.add(id);
 const parts=[];
 req.on('data',part=>parts.push(part));
 req.on('end',()=>{
  const body=JSON.parse(Buffer.concat(parts));requests++;
  assert.equal(body.model,'synthetic-only');
  assert.equal(body.max_tokens,16384);
  if(stall) {
   active++;res.once('close',()=>{active--});return;
  }
  if(invalid)return res.end('PRIVATE_SENTINEL not JSON');
  if(requests===1)sessionId=req.headers['x-mtplx-session-id'];
  assert.equal(req.headers['x-mtplx-session-id'],sessionId);
  const message=requests===1?{role:'assistant',content:null,tool_calls:[
   {type:'function',id:'t',function:{name:'mb_action',arguments:'{"op":"read","path":"TASK.md"}'}}]}:
   {role:'assistant',content:'done'};
  if(requests===2)assert.equal(body.messages.at(-1).role,'tool');
  reply({id,model:'synthetic-only',choices:[{message,finish_reason:requests===1?'tool_calls':'stop'}],
   usage:{prompt_tokens:20,completion_tokens:4,total_tokens:24}});
 });
});
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
try {
 const port=server.address().port;assert.notEqual(port,8000);
 const now=Date.now();
 const condition={endpoint:`http://127.0.0.1:${port}/v1`,synthetic:true,model:'synthetic-only',
  limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:now-1000,windowEndMs:now+60000,
  concurrency:1,grading:'after-window-release'};
 const events=[];let actions=0;
 const makeWindow=condition=>localWindow({condition,record:r=>events.push(r),
  snapshot:()=>({memoryPressureFreePercent:45,memoryPressureState:'normal',
   loadAverage:[1,1,1],heavyProcesses:[]})});
 let window=makeWindow(condition);
 const options={prompt:'synthetic',tools:[],signal:new AbortController().signal,
  execute:async(id,args)=>{actions++;assert.equal(args.path,'TASK.md');return {text:'synthetic task'}}};
 assert.equal((await window.run(options)).status,'completed');
 assert.equal(actions,1);assert.equal(requests,2);
 assert.equal((await window.release()).ownedRequestsDrained,true);
 stall=true;window=makeWindow({...condition,requestSeconds:0.0255});
 await assert.rejects(()=>window.run(options),error=>error.name==='TimeoutError');
 await assert.rejects(()=>window.run(options),/concurrency_denied/);
 const release=await window.release();
 assert.equal(release.ownedRequestsDrained,true);assert.equal(active,0);
 assert.equal(release.ownRequestIds.length,1);
 assert.equal(release.attempts.at(-1).reason,'deadline');
 assert.equal(release.attempts.at(-1).usage,undefined);
 assert.equal(actions,1);assert.equal(requests,3);
 stall=false;invalid=true;window=makeWindow(condition);
 await assert.rejects(()=>window.run(options),/local_response_json_invalid/);
 const invalidRelease=await window.release();
 assert.equal(invalidRelease.attempts.at(-1).reason,'local_response_json_invalid');
 assert(!JSON.stringify(events).includes('PRIVATE_SENTINEL'));
 assert.equal(actions,1);assert.equal(requests,4);
} finally {
 server.closeAllConnections();
 await new Promise(resolve=>server.close(resolve));
}
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=15)


def test_local_ledger_requires_backend_drain_and_excludes_synthetic_native_proofs(tmp_path):
    from benchmarks.michael.replay_trial import handoff
    bundle = handoff.bundle(tmp_path, "test-only", synthetic=True, configuration={
        "source": {}, "localInference": {"model": "test-only"}})
    assert bundle["condition"]["hosts"]["inference"]["value"] == "local-macos"
    native = {"stopReason": "session_idle", "wholeProcessQuiescent": True, "cleanupSeconds": 1,
              "nativePrompts": 0, "localInference": {"synthetic": False, "attempts": 2,
                  "result": {"status": "completed"}, "release": {"ownedRequestsDrained": True}}}
    report = {"status": "graded", "verdict": "pass", "cleanup": {"proven": True},
              "bindings": {"source_sha256": "a" * 64}, "assertions": [{"passed": True}]}
    def result():
        return handoff.terminal(bundle, native, report, {"end_to_end": 10},
            owner_exited=True, source_sha="a" * 64, expected_assertions=1)["attempts"][0]
    assert result()["verdict"] == "passed"
    native["localInference"]["release"]["ownedRequestsDrained"] = False
    assert result()["verdict"] == "ungraded"
    native["localInference"]["release"]["ownedRequestsDrained"] = True
    native["localInference"]["synthetic"] = True
    assert result()["verdict"] == "ungraded"


def test_local_post_window_grader_refuses_missing_or_wrong_release_before_docker(tmp_path, monkeypatch):
    from benchmarks.michael.local_transport import local_trial
    model = "test-only"
    run = tmp_path / model
    run.mkdir()
    (tmp_path / "seal.json").write_text(json.dumps({"frozen": {"models": [model], "package": "validator",
        "localInference": {"owningSession": "owner", "requestNamespace": "namespace"}}}))
    (run / "local-outcome.json").write_text(json.dumps({"finishedAtMs": 100}))
    monkeypatch.setattr(api.grader, "grade", lambda *args, **kwargs: pytest.fail("Docker before release"))
    for receipt in ({}, {"released": True, "ownedRequestsDrained": True, "releasedAtMs": 200,
                        "owningSession": "wrong", "requestNamespace": "namespace"}):
        with pytest.raises(api.TrialError, match="matching window release"):
            local_trial.finalize(tmp_path, receipt)


@pytest.mark.parametrize("start,end", [(0, 9000), (20000, 100000)])
def test_local_closed_window_cannot_allocate_a_ledger_or_process(tmp_path, monkeypatch, start, end):
    from benchmarks.michael.local_transport import local_trial
    frozen = {"source": {},
              "localTrialSha256": api.sha(local_trial.Path(local_trial.__file__).read_bytes()),
              "localInference": {"windowStartMs": start, "windowEndMs": end}}
    (tmp_path / "seal.json").write_text(json.dumps({"frozen": frozen}))
    monkeypatch.setattr(local_trial.native, "sources", lambda: {})
    monkeypatch.setattr(local_trial.time, "time", lambda: 10)
    monkeypatch.setattr(local_trial.handoff, "Ledger", lambda *args: pytest.fail("allocated closed slot"))
    monkeypatch.setattr(local_trial.api.runner, "launch", lambda *args: pytest.fail("started closed slot"))
    with pytest.raises(api.TrialError, match="window not open"):
        local_trial.execute(tmp_path)


def test_local_stable_warning_is_conditional_but_critical_and_swap_growth_stop():
    script = """
import assert from 'node:assert/strict';
import {localWindow} from './benchmarks/michael/local_transport/local_window.mjs';
import {LOCAL_LIMITS} from './benchmarks/michael/local_transport/local_inference.mjs';
const condition={endpoint:'http://127.0.0.1:9876/v1',synthetic:true,model:'synthetic-only',
 limits:LOCAL_LIMITS,requestSeconds:2,windowStartMs:0,windowEndMs:3600000,allowWarning:true,
 residentInfrastructure:[{name:'synthetic-idle-vm',idleVerified:true}],
 concurrency:1,grading:'after-window-release'};
let swap=100,state='warning',requests=0;
const events=[];
const make=()=>localWindow({condition,record:r=>events.push(r),clock:()=>1000,
 snapshot:()=>({memoryPressureFreePercent:53,memoryPressureState:state,
  swapUsedBytes:swap,loadAverage:[1,1,1],heavyProcesses:[]}),
 fetcher:async(url,options)=>{
  if(url.endsWith('/health'))return new Response(JSON.stringify({ok:true,active_requests:0}));
  if(url.endsWith('/models'))return new Response(JSON.stringify({data:[{id:'synthetic-only'}]}));
  requests++;swap+=10;
  return new Response(JSON.stringify({id:options.headers['x-mtplx-request-id'],model:'synthetic-only',
   usage:{prompt_tokens:2,completion_tokens:1,total_tokens:3},
   choices:[{message:{role:'assistant',content:'done'},finish_reason:'stop'}]}));
 }});
const options={prompt:'synthetic',tools:[],signal:new AbortController().signal,execute:async()=>{}};
let window=make();
assert.equal((await window.run(options)).status,'completed');
assert.equal((await window.run(options)).status,'completed');
// A second consecutive boundary increase is sustained, unlike a single sample.
swap+=10;
await assert.rejects(()=>window.run(options),/resource_pressure/);
assert(events.some(e=>e.resources?.memoryPressureState==='warning'));
assert(events.filter(e=>e.resources?.memoryPressureState==='warning')
 .every(e=>e.resources.condition==='contended/non-isolated'));
assert(events.some(e=>e.resources?.swapUsedChangeBytes===10));
await window.release();
state='critical';window=make();
const before=requests;
await assert.rejects(()=>window.run(options),/resource_pressure/);
assert.equal(requests,before);await window.release();
state='normal';window=make();
assert.equal((await window.run(options)).status,'completed');
const resources=events.findLast(e=>e.type==='local_boundary').resources;
assert.match(resources.condition,/resident-idle.*not fully isolated/);
assert.deepEqual(resources.residentInfrastructure,condition.residentInfrastructure);
await window.release();
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)
