"""Pure Specctra session (SES) text helpers used before KiCad import."""


def without_placement(text):
    """Drop the SES `(placement ...)` block; routing never moves footprints.

    Freerouting writes board-only footprints with an empty FPID as `(component `
    with no image name, which KiCad's SES parser rejects.
    """
    start=text.find('(placement')
    if start<0:return text
    depth=0;quoted=False
    for index in range(start,len(text)):
        char=text[index]
        if char=='"':quoted=not quoted
        elif not quoted and char=='(':depth+=1
        elif not quoted and char==')':
            depth-=1
            if depth==0:return text[:start]+text[index+1:]
    raise ValueError('unterminated SES placement block')
