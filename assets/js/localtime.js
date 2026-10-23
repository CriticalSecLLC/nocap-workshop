// Rewrites every <time data-local> from its UTC datetime into the visitor's own
// timezone. Without JS the server-rendered UTC text stays, so nothing breaks.
(function () {
  var fmt = new Intl.DateTimeFormat(undefined, {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: 'numeric', minute: '2-digit', timeZoneName: 'short'
  });
  var timeOnly = new Intl.DateTimeFormat(undefined, {
    hour: 'numeric', minute: '2-digit', timeZoneName: 'short'
  });
  document.querySelectorAll('time[data-local]').forEach(function (el) {
    var d = new Date(el.getAttribute('datetime'));
    if (!isNaN(d)) { el.textContent = (el.getAttribute('data-local') === 'time' ? timeOnly : fmt).format(d); }
  });
  var note = document.getElementById('tz-note');
  if (note) {
    var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz) { note.textContent = 'Session times are shown in your local time (' + tz.replace(/_/g, ' ') + ').'; }
  }
})();
