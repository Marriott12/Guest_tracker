// Service Worker for offline check-in support
const CACHE_NAME = 'guest-tracker-v1';
const OFFLINE_DB_NAME = 'offline-checkins';
const OFFLINE_STORE_NAME = 'pending-checkins';

// Install service worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        '/static/guests/css/style.css',
        '/static/guests/js/scanner.js',
      ]);
    })
  );
  self.skipWaiting();
});

// Activate service worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Intercept fetch requests
self.addEventListener('fetch', (event) => {
  // Handle API check-in requests specially
  if (event.request.url.includes('/api/check-in/') && event.request.method === 'POST') {
    event.respondWith(
      fetch(event.request.clone())
        .then((response) => {
          // Online - return response
          return response;
        })
        .catch(() => {
          // Offline - save to IndexedDB
          return event.request.json().then((data) => {
            return saveOfflineCheckIn(data).then(() => {
              return new Response(
                JSON.stringify({
                  success: true,
                  offline: true,
                  message: 'Check-in saved offline. Will sync when online.',
                }),
                {
                  status: 202,
                  headers: { 'Content-Type': 'application/json' },
                }
              );
            });
          });
        })
    );
    return;
  }

  // Default fetch handling
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});

// Save offline check-in to IndexedDB
function saveOfflineCheckIn(data) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(OFFLINE_DB_NAME, 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction([OFFLINE_STORE_NAME], 'readwrite');
      const store = transaction.objectStore(OFFLINE_STORE_NAME);

      const checkInData = {
        ...data,
        timestamp: Date.now(),
        synced: false,
      };

      store.add(checkInData);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(OFFLINE_STORE_NAME)) {
        db.createObjectStore(OFFLINE_STORE_NAME, { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

// Listen for online event to sync
self.addEventListener('message', (event) => {
  if (event.data.action === 'sync-offline-checkins') {
    syncOfflineCheckIns();
  }
});

// Sync offline check-ins when online
function syncOfflineCheckIns() {
  const request = indexedDB.open(OFFLINE_DB_NAME, 1);

  request.onsuccess = () => {
    const db = request.result;
    const transaction = db.transaction([OFFLINE_STORE_NAME], 'readwrite');
    const store = transaction.objectStore(OFFLINE_STORE_NAME);
    const getAllRequest = store.getAll();

    getAllRequest.onsuccess = () => {
      const checkIns = getAllRequest.result;
      const unsyncedCheckIns = checkIns.filter((c) => !c.synced);

      unsyncedCheckIns.forEach((checkIn) => {
        fetch('/api/check-in/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': checkIn.csrfToken || '',
          },
          body: JSON.stringify({
            event_id: checkIn.event_id,
            barcode_number: checkIn.barcode_number,
            check_in: checkIn.check_in,
          }),
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              // Mark as synced
              const updateTransaction = db.transaction([OFFLINE_STORE_NAME], 'readwrite');
              const updateStore = updateTransaction.objectStore(OFFLINE_STORE_NAME);
              checkIn.synced = true;
              updateStore.put(checkIn);
            }
          })
          .catch(console.error);
      });
    };
  };
}
