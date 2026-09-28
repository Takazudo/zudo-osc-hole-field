"""Remove one fanout pair from a disposable board for native diagnosis."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pcbnew

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('receipt',type=Path);p.add_argument('scratch',type=Path);p.add_argument('index',type=int);a=p.parse_args()
    rows=json.loads(a.receipt.read_text())['added'];row=rows[a.index];a.scratch.parent.mkdir(parents=True,exist_ok=True)
    board=pcbnew.LoadBoard(str(a.candidate));by_uuid={x.m_Uuid.AsString():x for x in board.GetTracks()}
    board.Remove(by_uuid[row['track_uuid']]);board.Remove(by_uuid[row['via_uuid']])
    pcbnew.SaveBoard(str(a.scratch),board)
    print(json.dumps({'index':a.index,'ref':row['ref'],'pad':row['pad'],'output':str(a.scratch)}))
if __name__=='__main__':main()
