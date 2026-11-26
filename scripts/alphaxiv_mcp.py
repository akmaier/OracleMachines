#!/usr/bin/env python3
"""Small alphaXiv MCP client. Credentials stay in an ignored local file.

Use `tools`, `call NAME ARGUMENTS.json`, or `upload PAPER.pdf`. Publishing is
explicit: this script never uploads, publishes, or schedules work automatically.
Only the official alphaXiv API receives the bearer token. No credential is stored
in arguments, output, manuscript, or publication metadata.
"""
import argparse,json,sys,urllib.error,urllib.request
from pathlib import Path

API='https://api.alphaxiv.org'
ROOT=Path(__file__).resolve().parents[1]


def read_token(path):
    raw=path.read_text().strip()
    try:
        obj=json.loads(raw)
        token=obj if isinstance(obj,str) else next(obj[k] for k in ('token','api_key','apiKey','access_token') if k in obj)
    except (ValueError,StopIteration):token=raw
    if isinstance(token,str) and token.lower().startswith('bearer '):token=token[7:].strip()
    if not isinstance(token,str) or not token or any(c.isspace() for c in token):
        raise ValueError('Token must be one string or a supported JSON token object; content withheld')
    return token


def request(path,data,token,content_type):
    headers={'Content-Type':content_type,'Accept':'application/json, text/event-stream','User-Agent':'OracleMachines/1.0 MCP client'}
    if token is not None:headers['Authorization']='Bearer '+token
    req=urllib.request.Request(API+path,data=data,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=100) as response:return response.read().decode()
    except urllib.error.HTTPError as error:
        raise RuntimeError('alphaXiv HTTP '+str(error.code)+' '+error.read().decode(errors='replace')[:1200].replace(token or '\0','[REDACTED]')) from None


def rpc(method,params,token,ident=1):
    data=request('/mcp/v1',json.dumps(dict(jsonrpc='2.0',id=ident,method=method,params=params)).encode(),token,'application/json')
    if data.startswith('data:') or '\ndata:' in data:
        messages=[json.loads(line[5:].strip()) for line in data.splitlines() if line.startswith('data:')]
        result=next(m for m in messages if m.get('id')==ident)
    else:result=json.loads(data)
    if 'error' in result:raise RuntimeError(json.dumps(result['error']).replace(token,'[REDACTED]'))
    return result['result']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--token-file',type=Path,default=ROOT/'alphaxiv.org')
    parser.add_argument('action',choices=('tools','call','upload'));parser.add_argument('items',nargs='*');args=parser.parse_args()
    token=read_token(args.token_file)
    if args.action=='upload':
        if len(args.items)!=1:parser.error('upload requires one PDF path')
        data=Path(args.items[0]).read_bytes()
        if not data.startswith(b'%PDF-') or len(data)>50*1024*1024:parser.error('Expected a PDF no larger than 50 MB')
        result=json.loads(request('/papers/v3/submissions/pdf-uploads',data,None,'application/pdf'))
    else:
        rpc('initialize',dict(protocolVersion='2025-11-25',capabilities={},clientInfo=dict(name='OracleMachines-research',version='1.0')),token)
        if args.action=='tools':result=rpc('tools/list',{},token,2)
        else:
            if not 1<=len(args.items)<=2:parser.error('call requires a tool name and optional argument JSON file')
            result=rpc('tools/call',dict(name=args.items[0],arguments=json.loads(Path(args.items[1]).read_text()) if len(args.items)>1 else {}),token,2)
    print(json.dumps(result,ensure_ascii=False,indent=2).replace(token,'[REDACTED]'))


if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError) as error:sys.exit(str(error))
