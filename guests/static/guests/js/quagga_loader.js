// Loader for QuaggaJS: tries local vendor then CDN fallback
(function(){
  function loadCDN(){
    var s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js';
    s.async = true;
    document.head.appendChild(s);
  }

  if (typeof window.Quagga === 'undefined'){
    var local = document.createElement('script');
    local.src = '/static/guests/js/quagga.min.js';
    local.async = true;
    local.onerror = function(){ loadCDN(); };
    document.head.appendChild(local);
    setTimeout(function(){ if (typeof window.Quagga === 'undefined') loadCDN(); }, 500);
  }
})();
