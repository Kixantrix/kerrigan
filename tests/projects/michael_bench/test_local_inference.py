"""Offline synthetic provider; never connects to the operational model server."""
import subprocess

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
const records=[],calls=[];let requests=0,boundaries=0;
const result=await localLoop({condition,prompt:'synthetic',tools:[],signal:new AbortController().signal,
 clock:()=>1000,boundary:async()=>{boundaries++},record:r=>records.push(r),
 execute:async(id,args)=>{calls.push(args);return {exitCode:0}},
 fetcher:async(url,options)=>{
  const body=JSON.parse(options.body);assert.equal(body.max_tokens,16384);
  if(requests)assert.equal(body.messages.at(-1).role,'tool');
  const message=requests++===0?{role:'assistant',content:null,tool_calls:[
   {type:'function',id:'tool-1',function:{name:'mb_action',arguments:'{"op":"read","path":"TASK.md"}'}}]}:
   {role:'assistant',content:'done'};
  return new Response(JSON.stringify({id:options.headers['x-mtplx-request-id'],model:'synthetic-only',
    choices:[{message}],usage:requests===1?{prompt_tokens:12,completion_tokens:3,total_tokens:15}:undefined}));
 }});
assert.equal(result.calls,2);assert.equal(boundaries,4);assert.equal(calls[0].op,'read');
assert.equal(records.filter(r=>r.type==='local_request_finished')[1].usage,null);
assert.equal(records.filter(r=>r.type==='local_request_finished')[0].usage.inputTokens,12);
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
await assert.rejects(()=>localLoop({...base,boundary:async()=>{},
 fetcher:async()=>new Response(JSON.stringify({id:'wrong',model:'synthetic-only',choices:[]}))}),/identity/);
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
 [{prompt_tokens:229377,completion_tokens:1,total_tokens:229378},/context_budget/]]) {
 await assert.rejects(()=>localLoop({...base,fetcher:async(url,options)=>new Response(JSON.stringify({
  id:options.headers['x-mtplx-request-id'],model:'synthetic-only',usage,
  choices:[{message:{role:'assistant',tool_calls:[{type:'function',id:'t',
    function:{name:'mb_action',arguments:'{"op":"read","path":"TASK.md"}'}}]}}]}))}),reason);
}
await assert.rejects(()=>localLoop({...base,prompt:'x'.repeat(65537),
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
let active=0;const events=[];
const window=localWindow({condition,record:r=>events.push(r),clock:()=>1000,
 snapshot:()=>({memoryPressureFreePercent:45,loadAverage:[4,3,2],
 heavyProcesses:[{name:'Gridiron',cpuPercent:60,residentBytes:2000000000}]}),
 fetcher:async(url,options)=>{
  assert(!url.includes('snapshot')&&!url.includes('flight'));
  if(url.endsWith('/health'))return new Response(JSON.stringify({ok:true,active_requests:active}));
  if(url.endsWith('/models'))return new Response(JSON.stringify({data:[{id:'synthetic-only'}]}));
  return new Response(JSON.stringify({id:options.headers['x-mtplx-request-id'],model:'synthetic-only',
   usage:{prompt_tokens:10,completion_tokens:1,total_tokens:11},
   choices:[{message:{role:'assistant',content:'done'}}]}));
 }});
active=1;await assert.rejects(()=>window.boundary(),/contention/);
active=0;
const result=await window.run({prompt:'synthetic',tools:[],signal:new AbortController().signal,
 execute:async()=>{throw Error('unexpected tool')}});
assert.equal(result.status,'completed');
assert(events.some(r=>r.resources?.heavyProcesses[0].name==='Gridiron'));
const release=await window.release();
assert.equal(release.ownedRequestsDrained,true);assert.equal(release.ownRequestIds.length,1);
assert.equal(release.attempts.length,2);
await assert.rejects(()=>window.run({}),/concurrency_denied/);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=api.packages.ROOT,
                   check=True, timeout=10)
