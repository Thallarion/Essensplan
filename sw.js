/* Service Worker: App offline starten (Stale-While-Revalidate für eigene Dateien) */
const CACHE = "essensplan-app-v1";
const PRE = ["./", "index.html", "manifest.webmanifest", "icon.png", "fonts/fraunces.woff2", "fonts/atkinson-400.woff2", "fonts/atkinson-700.woff2"];
self.addEventListener("install", e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(PRE)).then(()=>self.skipWaiting()));
});
self.addEventListener("activate", e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener("fetch", e=>{
  const r = e.request, u = new URL(r.url);
  if(r.method!=="GET" || u.origin!==location.origin) return;                 // Firebase & Co. nicht anfassen
  if(u.pathname.includes("/hilfe/")) return;                                // Hilfe-Bilder nur online
  const nav = r.mode==="navigate";
  const key = nav && (u.pathname.endsWith("/") || u.pathname.endsWith("/index.html")) ? "index.html" : r;
  e.respondWith(caches.open(CACHE).then(async c=>{
    const hit = await c.match(key, {ignoreSearch: nav});
    const net = fetch(r).then(res=>{ if(res && res.ok) c.put(key, res.clone()); return res; }).catch(()=>null);
    if(hit){ e.waitUntil(net); return hit; }
    const res = await net;
    if(res) return res;
    if(nav){ const idx = await c.match("index.html"); if(idx) return idx; }
    return new Response("Offline", {status:503, statusText:"Offline"});
  }));
});
