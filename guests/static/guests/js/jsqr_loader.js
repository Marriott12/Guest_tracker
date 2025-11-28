// Loader for jsQR: uses vendored copy if present, otherwise injects CDN script.
(function(){
  function loadCDN(){
    var s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js';
    s.async = true;
    document.head.appendChild(s);
  }

  // If jsQR already present, nothing to do. Otherwise, attempt to load a local file
  if (typeof window.jsQR === 'undefined'){
    // Try to load local vendored file
    var local = document.createElement('script');
    local.src = '/static/guests/js/jsqr.min.js';
    local.async = true;
    local.onerror = function(){ loadCDN(); };
    document.head.appendChild(local);
    // fallback to CDN after short timeout if still not available
    setTimeout(function(){ if (typeof window.jsQR === 'undefined') loadCDN(); }, 500);
  }
})();
