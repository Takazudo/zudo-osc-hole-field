"""Remove only derived KiCad zone-fill caches; retain all source geometry bytes.

An output without caches requires native refill before connectivity analysis.
This pure transformation is not an acceptance check.
"""
from scripts.pcbgen.uuid_tools import top_level_spans


def without_zone_cache(text):
    spans=[]
    for start,end in top_level_spans(text):
        zone=text[start:end]
        if not zone.startswith('(zone\n') and not zone.startswith('(zone '):continue
        for a,b in top_level_spans(zone):
            kind=zone[a+1:b].split(None,1)[0].rstrip(')')
            if kind in ('filled_polygon','fill_segments'):spans.append((start+a,start+b))
    chunks=[];last=0
    for start,end in spans:
        chunks.append(text[last:start]);last=end
    chunks.append(text[last:])
    return ''.join(chunks),len(spans)
