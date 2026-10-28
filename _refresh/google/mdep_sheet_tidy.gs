// Drops the orphaned column blocks from the morning-response sheet, keeping only the 24 columns
// that belong to the questions the form carries now. Every earlier rebuild or rename appended a
// fresh block, so Form Responses 1 had 53 columns for 24 questions.
//
// It finds the current block by matching the 24 titles in item order, so it cannot delete the wrong
// columns: if the block is not there it aborts, and it aborts if any response row exists. Orphan
// columns belong to deleted items, so Google never writes to them - deleting them cannot lose data.
function tidyMorningSheet() {
  var SS = SpreadsheetApp.openById('12xvLgWLk60L5XM6fwtog5Jc0_3KwUrIT-fKMyN1wfNE');
  var sh = SS.getSheetByName('Form Responses 1');
  if (!sh) { Logger.log('ABORT: tab Form Responses 1 not found'); return; }
  var keep = ['District', 'Campaign day', 'UCs planned', 'UCs reported',
    'Mobile teams planned', 'Mobile teams deployed',
    'Influencers planned', 'Influencers deployed',
    'Fixed teams planned', 'Fixed teams deployed',
    'Transit teams planned', 'Transit teams deployed',
    'Roaming teams planned', 'Roaming teams deployed',
    'AIC teams planned', 'AIC teams deployed',
    'UPEC chairmen planned', 'UPEC chairmen deployed',
    'DCF teams planned', 'DCF teams deployed',
    'Security planned', 'Security deployed',
    'Security incidents today', 'Why is deployment late? (leave blank if on time)'];
  var rows = sh.getLastRow(), w = sh.getLastColumn();
  Logger.log('before: ' + rows + ' row(s), ' + w + ' column(s)');
  if (rows > 1) { Logger.log('ABORT: the sheet holds responses, nothing deleted'); return; }
  var head = sh.getRange(1, 1, 1, w).getValues()[0];
  var start = -1;
  for (var c = 0; c <= w - keep.length && start < 0; c++) {
    var ok = true;
    for (var k = 0; k < keep.length; k++) {
      if (String(head[c + k]).trim() !== keep[k]) { ok = false; break; }
    }
    if (ok) start = c + 1;
  }
  if (start < 0) { Logger.log('ABORT: the current question block was not found in row 1'); return; }
  Logger.log('current block: columns ' + start + '-' + (start + keep.length - 1));
  var tail = w - (start - 1) - keep.length;
  if (tail > 0) sh.deleteColumns(start + keep.length, tail);
  if (start > 1) sh.deleteColumns(1, start - 1);
  var after = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  Logger.log('after: ' + after.length + ' column(s): ' + after.join(' | '));
}
