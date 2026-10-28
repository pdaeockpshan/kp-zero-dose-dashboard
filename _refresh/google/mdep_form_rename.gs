// Renames the morning-report questions to "Mobile teams planned" / "Mobile teams deployed" style.
// Paste into the Apps Script project, select all (Ctrl+A) first so nothing of the old text is left,
// then Run renameMorningForm.
function renameMorningForm() {
  var form = FormApp.openById('1UnWmFlLedcMJyz8ttlHb669IYZZWoS_obPtMw-7jx-U');
  var cadres = ['Mobile teams', 'Influencers', 'Fixed teams', 'Transit teams', 'Roaming teams',
                'AIC teams', 'UPEC chairmen', 'DCF teams', 'Security'];
  var map = { 'UCs planned today': 'UCs planned', 'UCs reported today': 'UCs reported' };
  for (var c = 0; c < cadres.length; c++) {
    map['Teams planned today - ' + cadres[c]] = cadres[c] + ' planned';
    map['Teams deployed today - ' + cadres[c]] = cadres[c] + ' deployed';
  }
  var done = 0, left = [];
  form.getItems().forEach(function (it) {
    var t = it.getTitle();
    if (map[t]) { it.setTitle(map[t]); done++; }
    else if (/planned|deployed/.test(t)) { left.push(t); }
  });
  Logger.log('renamed ' + done + ' item(s)');
  if (left.length) { Logger.log('still old-style: ' + left.join(' | ')); }
}
