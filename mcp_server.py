from __future__ import annotations
import argparse, inspect, math, os, re
from typing import Any
import httpx
from mcp.server.mcpserver import MCPServer as FastMCP
from mcp.server.transport_security import TransportSecuritySettings

BASE=os.environ.get("GODS_EYE_BASE_URL","http://gods-eye-view:4173").rstrip("/")
TIMEOUT=httpx.Timeout(12.0, connect=4.0)

def _get(path:str, params:dict|None=None)->Any:
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as c:
        r=c.get(BASE+path, params=params)
        ct=r.headers.get("content-type","")
        data=r.json() if "json" in ct else {"text":r.text[:4000]}
        if r.status_code>=400:
            return {"status":"unavailable","http_status":r.status_code,"detail":data}
        return data

def allowed_hosts() -> list[str]:
    hosts=["127.0.0.1:18768","localhost:18768","gods-eye-read-mcp:18768"]
    for item in os.environ.get("MCP_ALLOWED_HOSTS","").split(","):
        item=item.strip()
        if not item:
            continue
        if not re.fullmatch(r"(?:[A-Za-z0-9][A-Za-z0-9._-]{0,125}|(?:[0-9]{1,3}\.){3}[0-9]{1,3}):[0-9]{1,5}",item):
            raise ValueError("Invalid MCP_ALLOWED_HOSTS entry")
        port=int(item.rsplit(":",1)[1])
        if not 1 <= port <= 65535:
            raise ValueError("Invalid MCP_ALLOWED_HOSTS port")
        hosts.append(item)
    return hosts

SECURITY=TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=allowed_hosts(),
    allowed_origins=[],
)

mcp=FastMCP(
    name="gods-eye-finance-context",
    instructions=(
      "Read-only geopolitical/geospatial context from the local God's Eye View instance. "
      "These tools are contextual evidence only, never authoritative price data or proof of causality."
    ),
)

@mcp.tool()
def regional_brief(latitude:float, longitude:float, article_limit:int=8)->dict:
    """Regional place/weather/news brief for a coordinate. Context only."""
    if not (-90<=latitude<=90 and -180<=longitude<=180):
        return {"error":"invalid coordinates"}
    d=_get("/api/regional-brief",{"latitude":latitude,"longitude":longitude})
    if isinstance(d,dict) and isinstance(d.get("articles"),list):
        d=dict(d); d["articles"]=d["articles"][:max(0,min(article_limit,20))]
    return d

@mcp.tool()
def weather_effects(latitude:float, longitude:float)->dict:
    """Current local weather context for logistics/commodities/event risk."""
    if not (-90<=latitude<=90 and -180<=longitude<=180):
        return {"error":"invalid coordinates"}
    return _get("/api/weather-effects",{"latitude":latitude,"longitude":longitude})

@mcp.tool()
def aircraft_near(latitude:float, longitude:float, radius_deg:float=3.0, limit:int=40)->dict:
    """Aircraft states near a coordinate, filtered locally from God's Eye/OpenSky data."""
    if not (-90<=latitude<=90 and -180<=longitude<=180):
        return {"error":"invalid coordinates"}
    radius=max(0.25,min(float(radius_deg),15.0)); limit=max(1,min(int(limit),100))
    # Gods Eye View v0.3+ renamed the official OpenSky HTTP proxy to
    # /api/flights; retain compatibility with prior releases without
    # rewriting or replacing the upstream application.
    d=_get("/api/flights",{"lat":latitude,"lon":longitude})
    if isinstance(d,dict) and d.get("http_status")==404:
        d=_get("/api/opensky",{"lat":latitude,"lon":longitude})
    states=(d or {}).get("states") if isinstance(d,dict) else None
    if not isinstance(states,list): return {"status":"unavailable","detail":d}
    out=[]
    for s in states:
        if not isinstance(s,list) or len(s)<11: continue
        lon=s[5]; lat=s[6]
        if lon is None or lat is None: continue
        try:
            if abs(float(lat)-latitude)<=radius and abs(float(lon)-longitude)<=radius:
                out.append({
                  "icao24":s[0],"callsign":str(s[1] or "").strip(),"country":s[2],
                  "longitude":lon,"latitude":lat,"altitude_m":s[7],
                  "on_ground":s[8],"velocity_mps":s[9],"heading_deg":s[10]
                })
        except Exception: pass
        if len(out)>=limit: break
    return {"retrievedAt":d.get("time"),"center":{"latitude":latitude,"longitude":longitude},
            "radius_deg":radius,"count":len(out),"aircraft":out,
            "note":"Context only; coverage and latency vary by OpenSky/source availability."}

@mcp.tool()
def source_status()->dict:
    """Non-secret health/availability status for selected God's Eye data sources."""
    checks={}
    for name,path in [
        ("setup","/api/setup/status"),
        ("overpass","/api/overpass/status"),
        ("firms","/api/firms/status"),
        ("ais","/api/ais-live?maxRows=1"),
    ]:
        d=_get(path)
        if name=="setup" and isinstance(d,dict) and d.get("http_status")==403:
            # Upstream protects provider settings from non-loopback clients.
            # Preserve this security gate; restricted does not mean down.
            d={"status":"restricted","reason":"provider_settings_local_only"}
        if name=="setup" and isinstance(d,dict):
            # Keep only key-presence booleans/status; never return values.
            safe={}
            for k,v in d.items():
                if isinstance(v,(bool,int,float)) or v is None: safe[k]=v
                elif isinstance(v,str) and len(v)<120: safe[k]=v
            d=safe
        if name=="ais" and isinstance(d,dict):
            d={k:d.get(k) for k in ("status","source","error","lastMessageAt","staleAfterMs")}
        checks[name]=d
    return checks

def _serve(server:Any,host:str,port:int,path:str)->None:
    settings=getattr(server,"settings",None)
    if settings is not None:
        for attr,value in (("host",host),("port",port),("streamable_http_path",path)):
            if hasattr(settings,attr): setattr(settings,attr,value)
    params=inspect.signature(server.run).parameters
    if "host" in params or any(p.kind is p.VAR_KEYWORD for p in params.values()):
        server.run(transport="streamable-http",host=host,port=port,streamable_http_path=path,transport_security=SECURITY)
    else:
        server.run(transport="streamable-http")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--host",default="0.0.0.0"); ap.add_argument("--port",type=int,default=18768)
    a=ap.parse_args(); _serve(mcp,a.host,a.port,"/mcp")
