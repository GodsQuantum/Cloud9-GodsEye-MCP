#!/usr/bin/env python3
from pathlib import Path
import subprocess,re,json,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent.parent
filelist=subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split(chr(0))
patterns=[re.compile(s,re.I) for s in ['a'+'rezki','chou'+'gar','kech'+'idi','fe'+'lla',r'192[.]168[.]',r'home[.]arpa','/srv/'+'lxc/','/home/'+'arezki',r'@gmail[.]com',r'-----BEGIN PRIVATE KEY',r'github_pat_[A-Za-z0-9_]{25,}']]
bad=[]
for name in filelist:
    if not name or name=='tests/privacy.py':continue
    p=root/name
    if not p.is_file() or p.stat().st_size>300000:continue
    text=p.read_text(errors='replace')
    if any(pat.search(text) for pat in patterns):bad.append(name)
assert not bad,('PRIVATE_TEXT_REVIEW_REQUIRED',bad)
assert len(json.loads((root/'tests/contract-tools.json').read_text()))==4
ET.parse(root/'docs/logo.svg');ET.parse(root/'docs/tools.svg')
print('PUBLIC_GODSEYE_MCP_PRIVACY_AND_CONTRACT_PASS')
