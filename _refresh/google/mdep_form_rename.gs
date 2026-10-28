/**
 * Morning team deployment - renames the count questions to plain English.
 *
 * "Teams planned today - Mobile teams" becomes "Mobile teams planned", and so on for every cadre,
 * with "UCs planned today" / "UCs reported today" becoming "UCs planned" / "UCs reported".
 *
 * Paste this file into the same Apps Script project as mdep_form_fix.gs (File - New - Script file),
 * pick renameMorningForm from the Run dropdown and Run. It only sets titles: item order, required
 * flags, whole-number validation, the form link and the response sheet are untouched, and no
 * response is created or deleted. Safe to run twice - a second run finds nothing left to rename.
 */

var FORM_ID = '1UnWmFlLedcMJyz8ttlHb669IYZZWoS_obPtMw-7jx-U';

var CADRES = ['Mobile teams', 'Influencers', 'Fixed teams', 'Transit teams', 'Roaming teams',
              'AIC teams', 'UPEC chairmen', 'DCF teams', 'Security'];

function renameMorningForm() {
  var form = FormApp.openById(FORM_ID);
  var map = {
    'UCs planned today': 'UCs planned',
    'UCs reported today': 'UCs reported'
  };
  for (var c = 0; c < CADRES.length; c++) {
    map['Teams planned today - ' + CADRES[c]] = CADRES[c] + ' planned';
    map['Teams deployed today - ' + CADRES[c]] = CADRES[c] + ' deployed';
  }

  var renamed = [], skipped = [];
  var items = form.getItems();
  for (var i = 0; i < items.length; i++) {
    var it = items[i], t = it.getTitle();
    if (map[t]) { it.setTitle(map[t]); renamed.push(t + ' -> ' + map[t]); }
    else if (/planned|deployed/i.test(t)) skipped.push(t);
  }

  // Anything still titled in the old style means the map did not cover it - say so loudly.
  Logger.log('renamed %s item(s)', renamed.length);
  renamed.forEach(function (s) { Logger.log('  %s', s); });
  if (skipped.length) {
    Logger.log('untouched pairs (check these by hand):');
    skipped.forEach(function (s) { Logger.log('  %s', s); });
  }
  Logger.log('form now: %s', form.getItems().map(function (x) { return x.getTitle(); }).join(' | '));
}
