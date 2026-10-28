/**
 * Morning team deployment - creates the Google Form and its response sheet.
 *
 * Run once, in your own Google account: open this project, pick createMorningForm, Run, and
 * approve the access prompt. It creates
 *   - a spreadsheet "Morning team deployment - SNID Nov-26 (responses)"
 *   - a form "Morning team deployment - SNID Nov-26", linked to that spreadsheet
 *   - a "Links" tab holding the form link, the sheet link and the CSV feed URL
 * and touches nothing else in your Drive. It asks for Forms and Sheets access only; the sheet is
 * shared by hand afterwards (Share - Anyone with the link - Viewer) so the feed URL opens.
 *
 * The form carries counts and fixed reason codes only. There is deliberately no free-text field:
 * any text box would end up holding AIC / UCMO names, and the responses sheet sits behind a
 * public dashboard. If remarks are ever wanted they belong in a second, unpublished sheet.
 *
 * One submission per district per campaign day; a district that resubmits creates a second row
 * and the board keeps the later update - the same rule the workbook import uses.
 */

var DISTRICTS = [
  'PESHAWAR', 'DIKHAN', 'DIRLOWER', 'CHARSADA', 'NOWSHERA', 'BANNU', 'BAJOUR', 'DIRUPPER',
  'ABOTABAD', 'KHYBER', 'KOHAT', 'LAKKIMRWT', 'WAZIR-N', 'KARAK', 'KURRAM', 'MOHMAND', 'HANGU',
  'TANK', 'WAZIR-S Lower', 'CHITRALLOWER', 'ORAKZAI', 'TORGHAR', 'KOHISTANUPPER',
  'KOHISTANLOWER', 'CHITRALUPPER', 'KOLAIPALAS', 'WAZIR-S Upper'
];

// The nine cadres the board reports on, in the board's own order.
var CADRES = ['Mobile teams', 'Influencers', 'Fixed teams', 'Transit teams', 'Roaming teams',
              'AIC teams', 'UPEC chairmen', 'DCF teams', 'Security'];

function createMorningForm() {
  var props = PropertiesService.getScriptProperties();
  var done = props.getProperty('mdep_form');
  if (done) throw new Error('Already created once. Existing form: ' + done);

  var ss;
  try { ss = SpreadsheetApp.getActiveSpreadsheet(); } catch (e) { ss = null; }
  if (!ss) ss = SpreadsheetApp.create('Morning team deployment - SNID Nov-26 (responses)');
  else ss.rename('Morning team deployment - SNID Nov-26 (responses)');

  var form = FormApp.create('Morning team deployment - SNID Nov-26');
  form.setDescription('Daily morning report from every district in the SNID Nov-26 scope. ' +
    'Counts only - no names, no free text. If something changes during the morning, submit ' +
    'again with the later time: the latest update for that district and day is the one used.');
  form.setCollectEmail(false);
  form.setProgressBar(true);
  form.setConfirmationMessage('Received. The provincial board picks this up on its next refresh.');

  form.addListItem().setTitle('Campaign').setChoiceValues(['SNID Nov-26']).setRequired(true);
  form.addListItem().setTitle('District').setChoiceValues(DISTRICTS).setRequired(true);
  var days = [];
  for (var d = 1; d <= 12; d++) days.push(String(d));
  form.addListItem().setTitle('Campaign day').setChoiceValues(days).setRequired(true)
    .setHelpText('Day 1 is the first campaign day (2 Nov 2026). Days 8-12 are extended catch-up.');
  form.addTimeItem().setTitle('Time of this update').setRequired(true).setHelpText('Local time.');

  form.addPageBreakItem().setTitle("Today's teams");
  form.addTextItem().setTitle('UCs reported today').setRequired(true).setValidation(whole());
  // A one-column grid keeps the nine counts on one screen on a phone. If the account refuses a
  // single-column grid, fall back to nine number questions.
  try {
    form.addGridItem().setTitle('Teams deployed today').setRows(CADRES)
      .setColumns(['Deployed']).setRequired(true);
  } catch (e) {
    for (var i = 0; i < CADRES.length; i++) {
      form.addTextItem().setTitle(CADRES[i] + ' deployed today')
        .setRequired(true).setValidation(whole());
    }
  }
  form.addTextItem().setTitle('Security incidents today').setRequired(true).setValidation(whole())
    .setHelpText('0 if none.');
  form.addCheckboxItem().setTitle('Why is deployment late? (only if it is)')
    .setChoiceValues(['Security incident (SEC)', 'Network / connectivity (NET)',
                      'Boycott / access refusal (BOY)', 'Transport / access (TRA)',
                      'Other (OTH)']);

  form.addPageBreakItem().setTitle('Plan change - leave blank unless the plan changed');
  try {
    form.addGridItem().setTitle('Planned teams, if the plan changed').setRows(CADRES)
      .setColumns(['Planned']);
  } catch (e) {
    for (var j = 0; j < CADRES.length; j++) {
      form.addTextItem().setTitle(CADRES[j] + ' planned (if changed)').setValidation(whole());
    }
  }
  form.addTextItem().setTitle('UCs planned (if changed)').setValidation(whole())
    .setHelpText('Blank means the plan already on file stands.');

  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  var feed = 'https://docs.google.com/spreadsheets/d/' + ss.getId() +
             '/gviz/tq?tqx=out:csv&sheet=Form%20Responses%201';
  var share = 'share by hand: Share - Anyone with the link - Viewer, or the feed URL returns 403';

  var links = ss.insertSheet('Links');
  links.getRange(1, 1, 6, 2).setValues([
    ['Share this with districts', form.getPublishedUrl()],
    ['Edit the form', form.getEditUrl()],
    ['Responses sheet', ss.getUrl()],
    ['CSV feed', feed],
    ['Sheet sharing', share],
    ['Created', new Date().toISOString()]
  ]);
  links.setColumnWidth(1, 240);
  links.getRange('B1:B4').setFontColor('#1155cc');

  props.setProperty('mdep_form', form.getPublishedUrl());
  props.setProperty('mdep_sheet', ss.getId());
  props.setProperty('mdep_feed', feed);

  Logger.log('form  %s', form.getPublishedUrl());
  Logger.log('sheet %s', ss.getUrl());
  Logger.log('feed  %s', feed);
  Logger.log('share %s', share);
}

function whole() {
  return FormApp.createTextValidation().requireNumberBetween(0, 100000)
    .setHelpText('Whole number, 0 or more').build();
}
