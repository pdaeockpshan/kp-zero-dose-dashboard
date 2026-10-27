function mdpReadMe(){
 const st=mdpStart();
 return [
 'Morning team deployment — what this workbook holds',
 'Campaign: '+mdpCampLbl()+(st?' · start '+st:' · start date not recorded for this campaign')+'. The tab keeps one set of reports per campaign; this workbook carries the campaign selected in the tab, never a blend of two.',
 'Purpose. One morning report per district per campaign day, from the time teams start moving (about 08:00) until the last team is out, which can run to 14:00 because of network, security, boycott or access problems. The dashboard shows what has been reported, what is still awaited and where the plan is not being met.',
 'Campaign days. Every district runs 3 active days + 2 catch-up days = 5. Peshawar and Khyber run 5 active days + 2 catch-up days = 7. A district can ask for extended catch-up; those days follow its last catch-up day and only the districts that asked appear on them.',
 'Sheet "Morning report" — the saved district-day reports in the current campaign and division / district filter, in the 39 columns the districts already use. The campaign start date and the day number are written on every row.',
 'Sheet "District summary" — one row per district for the day in view: reports saved, UCs reported, teams deployed against plan, teams awaited, incidents, reason and status.',
 'Sheet "Division summary" — the same measures rolled up to division. The last row is the total for the current filter, labelled with that filter (the campaign register when no filter is set), so a subset is never read as the province.',
 'Collecting a return. Pick the campaign first, then download the template for a day and send it to the district; import the returned sheet here. Import merges by district + campaign day: when two files carry the same district-day the later time of update wins, and rows outside days 1-'+MDP_MAXD+' are skipped.',
 'Awaited counts and the team deployment % are recomputed on import; the sheet values are not trusted. Deployment % = (mobile + fixed + transit + roaming deployed) ÷ (the same four planned).',
 'Privacy. Column F (last team deployed, team number, AIC names) and the free-text remarks are never collected or stored, and no name, e-mail or phone number is read from an imported sheet. This dashboard is a public page — keep names out of it.',
 'Storage. Reports typed in the dashboard or imported stay in this browser only (localStorage), under a key for the selected campaign; they are not sent anywhere. Download the workbook to share them. Clearing browser data removes them.',
 'Status bands: on plan 95% and above · watch 85-95% · short 70-85% · critical below 70%. A district with no report shows as no report, not as zero deployment.'
 ];
}
