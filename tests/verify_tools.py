#!/usr/bin/env python3
import asyncio,json
from pathlib import Path
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
def norm(x,root=False):
    if isinstance(x,list):return [norm(v) for v in x]
    if isinstance(x,dict):
        return {k:norm(v) for k,v in x.items() if not(k=='required' and v==[]) and not(root and k=='title')}
    return x
async def check():
    expected=json.loads(Path('/contract/contract-tools.json').read_text())
    async with streamable_http_client('http://127.0.0.1:18768/mcp') as conn:
        reader,writer=conn[:2]
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            response=(await session.list_tools()).tools
            tools={v.name:(v.model_dump(by_alias=True).get('inputSchema') or v.model_dump(by_alias=True).get('input_schema')) for v in response}
            assert len(tools)==4 and set(tools)==set(expected),('TOOLS',set(tools)^set(expected))
            changed=[k for k in tools if norm(tools[k],True)!=norm(expected[k],True)]
            assert not changed,('SCHEMA_CHANGED',changed)
            print('GODSEYE_FOUR_MCP_NAMES_AND_SCHEMAS_PASS',flush=True)
            for name,args in [
                ('regional_brief',{'latitude':48.8,'longitude':2.3}),
                ('weather_effects',{'latitude':48.8,'longitude':2.3}),
                ('aircraft_near',{'latitude':48.8,'longitude':2.3}),
                ('source_status',{})
            ]:
                result=await session.call_tool(name,args)
                assert not getattr(result,"is_error",False),('ERROR',name,result.content)
                payload=json.dumps([str(v) for v in result.content])
                assert 'fixture' in payload or 'FIXTURE' in payload or 'abc123' in payload,(name,payload[:200])
            print('GODSEYE_FOUR_NATIVE_HTTP_BACKEND_CALLS_PASS',flush=True)
    h={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
    req={'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'probe','version':'1'}}}
    a=httpx.post('http://127.0.0.1:18768/mcp',json=req,headers={**h,'Host':'127.0.0.1:18768'},timeout=6)
    b=httpx.post('http://127.0.0.1:18768/mcp',json=req,headers={**h,'Host':'malicious.invalid:18768'},timeout=6)
    assert (a.status_code,b.status_code)==(200,421),('SECURITY',a.status_code,b.status_code)
    print('GODSEYE_DNS_REBINDING_HTTP200_421_PASS',flush=True)
asyncio.run(check())
