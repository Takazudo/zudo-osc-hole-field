"""Readable manifests with one generated record per line instead of huge diffs."""
import json


def dumps(value,level=0):
    indent='  '*level
    if isinstance(value,dict):
        if not value:return '{}'
        return '{\n'+',\n'.join(indent+'  '+json.dumps(str(k),ensure_ascii=False)+': '+dumps(v,level+1) for k,v in value.items())+'\n'+indent+'}'
    if isinstance(value,list) and value and isinstance(value[0],dict):
        return '[\n'+',\n'.join(indent+'  '+json.dumps(row,ensure_ascii=False,separators=(',',':')) for row in value)+'\n'+indent+']'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))
