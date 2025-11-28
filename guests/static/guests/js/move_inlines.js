document.addEventListener('DOMContentLoaded', function() {
  try {
    // find the Event Details fieldset module by heading
    var modules = document.querySelectorAll('div.app-guests div.module');
    var targetModule = null;
    modules.forEach(function(m) {
      var h2 = m.querySelector('h2');
      if (h2 && h2.textContent.trim() === 'Event Details') {
        targetModule = m;
      }
    });

    if (!targetModule) return;

    // collect inline groups we want to move (ProgramItem, MenuItem, Table inlines)
    var inlineGroups = Array.from(document.querySelectorAll('.inline-group'));
    // filter for specific inlines if possible
    inlineGroups = inlineGroups.filter(function(g) {
      var id = g.getAttribute('id') || '';
      return id.indexOf('programitem') !== -1 || id.indexOf('menuitem') !== -1 || id.indexOf('table_set') !== -1 || id.indexOf('table') !== -1;
    });

    // Move each inline group after the target module
    inlineGroups.forEach(function(g){
      targetModule.parentNode.insertBefore(g, targetModule.nextSibling);
    });
  } catch (e) {
    // graceful fallback
    console && console.log && console.log('move_inlines failed', e);
  }
});
