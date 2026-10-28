/**
 * Rebuilds the items of the live morning-report form in place.
 *
 * Same form id, same linked response sheet, same responder link. Run once from a script bound to
 * the owning account: pick fixMorningForm, Run, approve the access prompt. It rebuilds the
 * question list so that every count is a whole-number field (planned and reported pairs for UCs
 * and for each of the nine cadres, in the template's order) instead of an unvalidated text box.
 *
 * Planned counts are optional: a blank planned value means the plan already on file stands, the
 * same rule the workbook import uses. Deployed / reported counts are required.
 *
 * It refuses to run if the form already has responses, because dropping items would leave those
 * rows without their columns. The sheet's header row is regenerated from the item list on the
 * next submission while the form is empty.
 */

var FORM_ID = '1UnWmFlLedcMJyz8ttlHb669IYZZWoS_obPtMw-7jx-U';

var DISTRICTS = ['PESHAWAR', 'DIKHAN', 'DIRLOWER', 'CHARSADA', 'NOWSHERA', 'BANNU', 'BAJOUR',
  'DIRUPPER', 'ABOTABAD', 'KHYBER', 'KOHAT', 'LAKKIMRWT', 'WAZIR-N', 'KARAK', 'KURRAM',
  'MOHMAND', 'HANGU', 'TANK', 'WAZIR-S Lower', 'CHITRALLOWER', 'ORAKZAI', 'TORGHAR',
  'KOHISTANUPPER', 'KOHISTANLOWER', 'CHITRALUPPER', 'KOLAIPALAS', 'WAZIR-S Upper'];

var CADRES = ['Mobile teams', 'Influencers', 'Fixed teams', 'Transit teams', 'Roaming teams',
  'AIC teams', 'UPEC chairmen', 'DCF teams', 'Security'];

function fixMorningForm() {
  var form = FormApp.openById(FORM_ID);
  if (form.getResponses().length) {
    throw new Error('Form already has responses - refusing to rebuild items');
  }

  var items = form.getItems();
  for (var i = items.length - 1; i >= 0; i--) form.deleteItem(items[i]);

  form.addListItem().setTitle('District').setChoiceValues(DISTRICTS).setRequired(true)
    .setHelpText('The district this report covers.');

  var days = [];
  for (var d = 1; d <= 12; d++) days.push(String(d));
  form.addListItem().setTitle('Campaign day').setChoiceValues(days).setRequired(true)
    .setHelpText('Day 1 is the first campaign day (2 Nov 2026). Days 8-12 are extended catch-up.');

  count(form, 'UCs planned today', 'Leave blank if the plan on file stands.', false);
  count(form, 'UCs reported today', 'UCs whose teams have reported by now.', true);

  for (var c = 0; c < CADRES.length; c++) {
    count(form, 'Teams planned today - ' + CADRES[c],
      'Leave blank if the plan on file stands.', false);
    count(form, 'Teams deployed today - ' + CADRES[c], 'Deployed by now.', true);
  }

  count(form, 'Security incidents today', '0 if none.', true);

  form.addCheckboxItem().setTitle('Why is deployment late? (leave blank if on time)')
    .setChoiceValues(['Security incident (SEC)', 'Network / connectivity (NET)',
      'Boycott / access refusal (BOY)', 'Transport / access (TRA)', 'Other (OTH)']);

  Logger.log('items=%s published=%s', form.getItems().length, form.getPublishedUrl());
}

function count(form, title, help, required) {
  var v;
  try {
    v = FormApp.createTextValidation().requireWholeNumber().setHelpText('Whole number').build();
  } catch (e) {
    v = FormApp.createTextValidation().requireNumberBetween(0, 100000)
      .setHelpText('Whole number').build();
  }
  return form.addTextItem().setTitle(title).setHelpText(help)
    .setValidation(v).setRequired(required);
}
