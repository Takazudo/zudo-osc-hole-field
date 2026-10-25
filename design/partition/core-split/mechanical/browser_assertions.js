// Executes inside a temporary instrumented copy of the real generated inspector.
(async () => {
  const result = {status: 'FAIL', assertions: [], errors: browserErrors};
  const check = (condition, label) => { if (!condition) throw Error(label); };
  const change = (id, value) => { $(id).value = value; $(id).dispatchEvent(new Event('change', {bubbles: true})); };
  const cleared = () => check($('detail').textContent === '' && !$('trims').querySelector('.selected') && selected === null, 'stale selection');
  const buttons = () => [...$('trims').querySelectorAll('button')];
  const select = t => {
    const button = buttons().find(b => b.textContent === t.ref);
    check(button, 'missing button '+t.ref);
    button.click();
    check(JSON.stringify(JSON.parse($('detail').textContent)) === JSON.stringify(t), 'detail association '+t.ref);
    check($('face').value === t.mounted_face && $('detailTitle').textContent === t.label+' — '+t.board+' '+t.mounted_face, 'face/title association');
    check($('plan').textContent.includes(t.ref) && $('trims').querySelector('.selected button').textContent === t.ref, 'selection highlight');
  };
  const asset = async url => {
    const image = new Image(); image.src = url; await image.decode();
    check(image.naturalWidth > 0, 'missing asset '+url);
  };
  try {
    if (capture.verify) {
      check(report.alternatives.length === 5 && $('alternative').options.length === 5, 'alternative count');
      let total = 0;
      const physicalRefs = new Set();
      for (const a of report.alternatives) {
        change('alternative', a.id); cleared();
        check([...$('board').options].map(o=>o.value).join() === a.boards.map(b=>b.id).join(), 'board options');
        const refs = new Set();
        for (const b of a.boards) {
          change('board', b.id); cleared();
          const trims = a.trimmers.filter(t=>t.board===b.id);
          check(buttons().map(b=>b.textContent).join() === trims.map(t=>t.ref).join(), 'board inventory');
          for (const t of trims) { check(!refs.has(t.ref), 'duplicate Ref'); refs.add(t.ref); physicalRefs.add(t.ref); }
          for (const face of ['F.Cu', 'B.Cu']) {
            change('face', face); cleared();
            const t = trims.find(t=>t.mounted_face===face);
            check(t, 'missing representative face'); select(t);
            change('face', face==='F.Cu'?'B.Cu':'F.Cu'); cleared();
            result.assertions.push(`${a.id}/${b.id}/${face}: selected ${t.ref}, full detail and plan match; opposite face clears`);
          }
          select(trims[0]); // Leave a real selection for the next board/alternative reset.
          check($('plan').textContent.includes(b.id+' F Z='+b.front_z_mm), 'board geometry');
        }
        check(refs.size === 100, 'inventory per alternative'); total += refs.size;
        check($('assembledLink').getAttribute('href') === a.id+'-assembled.svg' && $('explodedLink').getAttribute('href') === a.id+'-exploded.svg', 'asset association');
        await asset($('assembledLink').href); await asset($('explodedLink').href);
        result.assertions.push(`${a.id}: 100 unique Ref rows across every board; assembled/exploded assets decoded`);
      }
      check(total === 500, '500 alternative-specific rows');
      result.alternative_specific_rows = total;
      check(physicalRefs.size === 100, 'same 100 physical trimmers across alternatives');
      result.distinct_physical_trimmers = physicalRefs.size;
      // Filter, internal table scrolling and the courtyard control remain usable.
      change('alternative', 'three-compact');
      const t = current().trimmers.find(t=>t.board===$('board').value);
      $('filter').value=t.ref; $('filter').dispatchEvent(new Event('input'));
      check(buttons().length === 1 && buttons()[0].textContent === t.ref, 'filter');
      $('filter').value=''; $('filter').dispatchEvent(new Event('input'));
      $('showParts').click(); check(!$('showParts').checked, 'courtyard toggle off'); $('showParts').click();
      const scroll = document.querySelector('.scroll'); scroll.scrollTop=scroll.scrollHeight;
      check(scroll.scrollTop>0, 'table scrolling'); scroll.scrollTop=0;
      result.assertions.push('Ref filter, courtyard toggle and table scrolling');
    }
    change('alternative', capture.alternative);
    if (capture.board) change('board', capture.board);
    const t = current().trimmers.find(t=>t.board===$('board').value && t.mounted_face===(capture.face||'F.Cu'));
    select(t);
    if (capture.reset) { change('face', 'B.Cu'); cleared(); }
    await $('stack').decode();
    if (capture.svg) {
      const url = $(capture.svg+'Link').href;
      const image = new Image(); image.src=url; await image.decode();
      image.style.cssText='display:block;width:1000px;height:720px';
      document.body.replaceChildren(image);
    }
    check(browserErrors.length === 0, 'application/resource errors: '+browserErrors.join('; '));
    result.capture = capture;
    result.status = 'PASS';
  } catch (error) { result.failure = error.stack; }
  const output = document.createElement('pre'); output.id='browser-result'; output.hidden=true;
  output.textContent=JSON.stringify(result); document.body.append(output);
})();
