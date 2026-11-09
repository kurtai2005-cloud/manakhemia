/* 《微光小圃》 garden3d.js — #89 3D 花園 H1 試點（八方旅人式 HD-2D；遊美 art/garden3d-h1-mesh @ 620509fc）。原創代碼。
   純邏輯（Node 可 require，唔使 three.js）：座標、鏡頭 sway／follow、碰撞、4 方向、日夜光、畫質自動。
   瀏覽器 Scene：Three.js 載 17 件 mesh＋地面＋背景板＋寵物 billboard（radiant 用 dir4；其他形態用 2D sprite 後備）。
   Kurt：三級畫質＋自動偵測＋fps／耗電面板（開發者模式）；?3d=0 返 2D；低畫質／低端機＝2D 後備；
   鏡頭自動擺／跟拍（patch2，Kurt 未批定）做埋，開發者模式有開關（預設開）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.garden3d = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const W = 195, H = 422, CX = 97, GROUND_Y = 292, ZSCALE = 1.6;
  const KEY_Q = 'glimmer.g3d.quality', KEY_SWAY = 'glimmer.g3d.sway', KEY_FOLLOW = 'glimmer.g3d.follow';
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const hex = (c) => { const n = parseInt(String(c || '#ffffff').replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
  const TAU = Math.PI * 2;

  /* ── 座標：3D 原點＝寵物預設腳底 art (97,292)；x＝art x−97；前排 z＝(art y−292)×1.6 ── */
  function artToWorld(ax, ay) { return { x: ax - CX, z: (ay - GROUND_Y) * ZSCALE }; }
  function worldToArtFlat(x, z) { return { x: x + CX, y: GROUND_Y + z / ZSCALE }; }
  function petWorld(beh) {
    const x = beh && beh.x != null ? +beh.x : 0;
    const z = beh && beh.depth ? (+beh.depth) * ZSCALE : 0;
    return { x: x, z: z };
  }

  /* ── 日夜：跟現有 HD-2D 時段（06–16 日、16–19 黃昏、19–06 夜）── */
  function nightMix(hour) {
    const h = ((hour % 24) + 24) % 24;
    if (h >= 6 && h < 16) return 0;
    if (h >= 16 && h < 19) return (h - 16) / 3;
    return 1;
  }
  function mixLights(L, night) {
    night = clamp(night, 0, 1);
    const sun = L.sun || {}, fill = L.fill || {}, N = L.night || {};
    const ambD = hex((sun.ambient && sun.ambient.color) || '#cfe0f0'), ambN = hex(N.ambient || '#4a5a90');
    const points = (L.lights || []).map(function (l) {
      return { id: l.id, x: l.x, y: l.y, z: l.z, color: l.color, radius: l.radius,
        intensity: lerp(l.intensity || 0, l.intensityNight || 0, night), flicker: l.flicker || 0 };
    });
    const byId = {}; points.forEach(function (p) { byId[p.id] = p.intensity; });
    return {
      night: night,
      sun: lerp(sun.intensity == null ? 1 : sun.intensity, N.sun == null ? 0.12 : N.sun, night),
      sunColor: sun.color || '#ffe6b8',
      sunDir: sun.dir || [0.42, -0.72, 0.55],
      shadowIntensity: sun.shadowIntensity == null ? 0.3 : sun.shadowIntensity,
      ambColor: [lerp(ambD[0], ambN[0], night), lerp(ambD[1], ambN[1], night), lerp(ambD[2], ambN[2], night)],
      ambIntensity: lerp((sun.ambient && sun.ambient.intensity) || 0.55, N.ambientIntensity == null ? 0.35 : N.ambientIntensity, night),
      fill: lerp(fill.intensity == null ? 0.38 : fill.intensity, fill.intensityNight == null ? 0 : fill.intensityNight, night),
      fillColor: fill.color || '#ffe2c4',
      fillDir: fill.dir || [0.2, -0.12, -0.97],
      points: points, byId: byId,
      fog: L.fog || { color: '#ffe8c8', near: 420, far: 1400 }
    };
  }

  /* ── 鏡頭：preview_garden3d.py 同行；yaw＝−A·cos(π·t/T) 單程緩入緩出 pingpong；跟拍指數阻尼 ── */
  function swayYaw(t, cam) {
    const A = cam.swayAmplitudeDeg == null ? 5 : cam.swayAmplitudeDeg;
    const T = cam.swayHalfPeriodSec == null ? 6 : cam.swayHalfPeriodSec;
    if (!(T > 0) || A === 0) return cam.yawDeg || 0;
    return -A * Math.cos(Math.PI * t / T);
  }
  function followDesired(cam, pet) {
    const tg = cam.target || [0, 30, -72];
    const w = cam.followWeight || [0.25, 0.3];
    const o = cam.followOffset || [-20, 0];
    const or = cam.followOrigin || [-110, -40];
    const px = pet && pet.x != null ? pet.x : 0, pz = pet && pet.z != null ? pet.z : 0;
    return [tg[0] + o[0] + w[0] * (px - or[0]), tg[1], tg[2] + (o[1] || 0) + w[1] * (pz - or[1])];
  }
  function followStep(cur, desired, dt, damping) {
    const k = 1 - Math.exp(-(damping == null ? 2 : damping) * Math.max(0, dt));
    return [cur[0] + (desired[0] - cur[0]) * k, cur[1] + (desired[1] - cur[1]) * k, cur[2] + (desired[2] - cur[2]) * k];
  }
  function camPos(target, yawDeg, cam) {
    const p = (cam.pitchDeg == null ? 30 : cam.pitchDeg) * Math.PI / 180;
    const yw = yawDeg * Math.PI / 180;
    const d = cam.dist == null ? 580 : cam.dist;
    return [target[0] + d * Math.sin(yw) * Math.cos(p), target[1] + d * Math.sin(p), target[2] + d * Math.cos(yw) * Math.cos(p)];
  }
  function clampYaw(yaw, cam, user) {
    const mn = cam.orbitMinDeg == null ? -10 : cam.orbitMinDeg;
    const mx = cam.orbitMaxDeg == null ? 10 : cam.orbitMaxDeg;
    return clamp((yaw || 0) + (user || 0), mn, mx);
  }

  /* ── 4 方向：|dx|≥|dz| → side（dx<0 鏡像）；dz>0 front；dz<0 back。fps idle 4／walk 10 ── */
  function dirOf(dx, dz, moving) {
    const clip = moving ? 'walk' : 'idle';
    if (Math.abs(dx) >= Math.abs(dz)) return { dir: 'side', flip: dx < 0, clip: clip };
    return { dir: dz < 0 ? 'back' : 'front', flip: false, clip: clip };
  }
  function frameName(info, t) {
    const n = info.clip === 'walk' ? 6 : 4, fps = info.clip === 'walk' ? 10 : 4;
    const i = ((Math.floor(Math.max(0, t) * fps) % n) + n) % n + 1;
    return info.dir + '_' + info.clip + '_' + (i < 10 ? '0' : '') + i;
  }

  /* ── 碰撞：寵物半徑唔可以入 footprint 外擴 pad＋radius（串燈／補位件冇 footprint）── */
  function distRect(x, z, r) {
    const dx = x < r.x[0] ? r.x[0] - x : x > r.x[1] ? x - r.x[1] : 0;
    const dz = z < r.z[0] ? r.z[0] - z : z > r.z[1] ? z - r.z[1] : 0;
    return Math.hypot(dx, dz);
  }
  function distPoly(x, z, pts) {
    let inside = false, min = Infinity, n = pts.length;
    for (let i = 0, j = n - 1; i < n; j = i++) {
      const xi = pts[i][0], zi = pts[i][1], xj = pts[j][0], zj = pts[j][1];
      const den = Math.hypot(xj - xi, zj - zi) || 1e-9;
      const t = clamp(((x - xi) * (xj - xi) + (z - zi) * (zj - zi)) / (den * den), 0, 1);
      min = Math.min(min, Math.hypot(x - (xi + t * (xj - xi)), z - (zi + t * (zj - zi))));
      const hit = ((zi > z) !== (zj > z)) && (x < (xj - xi) * (z - zi) / ((zj - zi) || 1e-9) + xi);
      if (hit) inside = !inside;
    }
    return inside ? 0 : min;
  }
  function fpDist(fp, x, z) {
    if (!fp) return Infinity;
    if (fp.type === 'poly' && fp.points) return distPoly(x, z, fp.points);
    if (fp.type === 'rect' && fp.x && fp.z) return distRect(x, z, fp);
    if (fp.rect) return distRect(x, z, fp.rect);
    if (fp.poly) return distPoly(x, z, fp.poly);
    return Infinity;
  }
  function blocked(objects, x, z, radius) {
    radius = radius == null ? 10 : radius;
    const hit = [];
    (objects || []).forEach(function (o) {
      const fp = o.footprint; if (!fp || o.backfill) return;
      const d = fpDist(fp, x, z), pad = (fp.pad == null ? 0 : fp.pad);
      if (d < pad + radius) hit.push(o.id);
    });
    return hit;
  }

  /* ── 畫質：high／mid＝3D；low＝2D 後備。?3d=0 永遠 2D；低端機自動 low。── */
  const QSET = {
    high: { dpr: 2, shadow: 2048, tex3x: true, shadows: true },
    mid: { dpr: 1, shadow: 1024, tex3x: false, shadows: true },
    low: { dpr: 1, shadow: 0, tex3x: false, shadows: false }
  };
  function detectQuality(o) {
    o = o || {};
    const qs = o.qs || {};
    const v = qs['3d'];
    if (o.force === 'off' || v === '0') return { want: false, quality: 'low', reason: 'off' };
    if (o.webgl === false) return { want: false, quality: 'low', reason: 'nowebgl' };
    if (v === 'high' || v === 'mid' || v === 'low') return { want: v !== 'low', quality: v, reason: 'qs' };
    if (v === '1') { /* 強制開，仲可以自動揀級 */ }
    const lowEnd = (o.hardwareConcurrency != null && o.hardwareConcurrency <= (o.lowEndCores || 4))
      || (o.deviceMemory != null && o.deviceMemory <= (o.lowEndMemGB || 4));
    if (lowEnd && v !== '1') return { want: false, quality: 'low', reason: 'lowend' };
    return { want: true, quality: 'high', reason: 'auto' };
  }
  function hasWebGL() {
    if (typeof document === 'undefined') return false;
    try {
      const c = document.createElement('canvas');
      return !!(c.getContext('webgl2') || c.getContext('webgl') || c.getContext('experimental-webgl'));
    } catch (e) { return false; }
  }
  function lsGet(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { } }

  // ───────── 瀏覽器 Scene ─────────
  function Scene(opts) {
    opts = opts || {};
    this.base = opts.base || 'art/garden3d/H1/';
    this.dir4base = opts.dir4base || 'art/garden3d/dir4/';
    this.enabled = opts.enabled !== false;
    this.quality = opts.quality || 'high';
    this.swayOn = opts.swayOn !== false;
    this.followOn = opts.followOn !== false;
    this.ready = false; this.error = null; this.loaded = false;
    this.t = 0; this.userYaw = 0; this.look = null; this.yaw = 0;
    this.pet = { x: 0, z: 0, dx: 0, dz: 0, moving: false, glow: 1, form: 'radiant', facing: { dir: 'front', flip: false, clip: 'idle' } };
    this.stat = { draws: 0, meshes: 0, frames: 0, ms: 0, fps: 0, lastMs: 0 };
    this.perf = { n: 0, sum: 0, max: 0, last: 0, fps: 0, acc: 0, fn: 0 };
    this.objects = []; this.lightsJ = null; this.camJ = null; this.objJ = null;
    this._drag = null; this._fbSprite = null; this._night = 0;
  }
  Scene.prototype.on = function () { return !!(this.enabled && this.ready && this.quality !== 'low'); };
  Scene.prototype.ownsPet = function () { return this.on(); };
  Scene.prototype.qs = function () { return QSET[this.quality] || QSET.high; };

  Scene.prototype.load = function () {
    const self = this, B = this.base, D4 = this.dir4base;
    const THREE = (typeof window !== 'undefined' && window.THREE) || (typeof globalThis !== 'undefined' && globalThis.THREE);
    if (!THREE) { this.error = 'no THREE'; return Promise.resolve(false); }
    const img = (u) => new Promise(function (res, rej) { const im = new Image(); im.onload = function () { res(im); }; im.onerror = function () { rej(new Error(u)); }; im.src = u; });
    const js = (u) => fetch(u).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    return Promise.all([js(B + 'objects.json'), js(B + 'lights.json'), js(B + 'camera.json'),
      js(D4 + 'atlas_radiant_dir4.json'), img(D4 + 'atlas_radiant_dir4.png'), img(D4 + 'atlas_radiant_dir4_n.png'), img(D4 + 'atlas_radiant_dir4_emissive.png')
    ]).then(function (pack) {
      const oj = pack[0], lj = pack[1], cj = pack[2];
      self.objJ = oj; self.lightsJ = lj; self.camJ = cj;
      self.dir4 = { json: pack[3], img: pack[4], n: pack[5], e: pack[6] };
      self.objects = oj.objects || [];
      const jobs = [];
      const g = oj.ground;
      jobs.push(Promise.all([img(B + g.file), img(B + g.file3x), img(B + g.ao), img(B + g.ao3x), img(B + g.outerTile.file), img(B + g.outerTile.file3x)]).then(function (im) {
        self.groundIm = { c1: im[0], c3: im[1], ao1: im[2], ao3: im[3], t1: im[4], t3: im[5] };
      }));
      self.meshJ = {}; self.meshIm = {};
      self.objects.forEach(function (o) {
        if (o.type === 'mesh') {
          jobs.push(js(B + o.mesh).then(function (m) {
            self.meshJ[o.id] = m;
            const te = [];
            te.push(img(B + m.texture), img(B + m.texture3x));
            if (m.emissive) te.push(img(B + m.emissive), img(B + m.emissive3x));
            return Promise.all(te).then(function (ims) { self.meshIm[o.id] = { c1: ims[0], c3: ims[1], e1: ims[2], e3: ims[3] }; });
          }));
        } else if (o.type === 'backdrop') {
          jobs.push(Promise.all([img(B + o.file), img(B + o.file3x)]).then(function (ims) { self.meshIm[o.id] = { c1: ims[0], c3: ims[1] }; }));
        }
      });
      return Promise.all(jobs);
    }).then(function () {
      self._build(THREE);
      self.ready = true; self.loaded = true; self.stat.meshes = (self.objects.filter(function (o) { return o.type === 'mesh'; }).length);
      return true;
    }).catch(function (e) { self.error = String(e && e.message || e); self.ready = false; return false; });
  };

  Scene.prototype._tex = function (THREE, im, opts) {
    opts = opts || {};
    const t = new THREE.Texture(im);
    t.magFilter = t.minFilter = THREE.NearestFilter;
    t.generateMipmaps = false;
    t.wrapS = t.wrapT = opts.repeat ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
    if (opts.repeat) { t.repeat.set(opts.repeat[0], opts.repeat[1]); }
    if (opts.srgb && THREE.SRGBColorSpace) t.colorSpace = THREE.SRGBColorSpace;
    t.needsUpdate = true;
    t.flipY = opts.flipY !== false; // images default flipY true（同 three 慣例；mesh uv 已經 V 上）
    if (opts.flipY === false) t.flipY = false;
    return t;
  };
  Scene.prototype._aoAlbedo = function (color, ao) {
    const c = document.createElement('canvas'); c.width = color.width; c.height = color.height;
    const x = c.getContext('2d', { willReadFrequently: true }); x.imageSmoothingEnabled = false; x.drawImage(color, 0, 0);
    const ac = document.createElement('canvas'); ac.width = c.width; ac.height = c.height;
    const ax = ac.getContext('2d', { willReadFrequently: true }); ax.imageSmoothingEnabled = false; ax.drawImage(ao, 0, 0, c.width, c.height);
    const cd = x.getImageData(0, 0, c.width, c.height), ad = ax.getImageData(0, 0, c.width, c.height);
    const d = cd.data, a = ad.data;
    for (let i = 0; i < d.length; i += 4) { const m = a[i] / 255; d[i] *= m; d[i + 1] *= m; d[i + 2] *= m; }
    x.putImageData(cd, 0, 0);
    return c;
  };
  Scene.prototype._flipUVV = function (geo) {
    const uv = geo.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i)); uv.needsUpdate = true;
  };

  Scene.prototype._build = function (THREE) {
    const self = this, Q = this.qs();
    if (this.renderer) { try { this.renderer.dispose(); } catch (e) { } }
    const canvas = document.createElement('canvas');
    canvas.width = W * 2; canvas.height = H * 2;
    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: false, alpha: false, preserveDrawingBuffer: true, powerPreference: this.quality === 'high' ? 'high-performance' : 'low-power' });
    renderer.outputColorSpace = THREE.SRGBColorSpace || renderer.outputColorSpace;
    if ('useLegacyLights' in renderer) renderer.useLegacyLights = true;
    renderer.shadowMap.enabled = !!Q.shadows;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.setPixelRatio(1);
    renderer.setSize(W * 2, H * 2, false);
    renderer.setClearColor(0xffe8c8, 1);
    this.canvas = canvas; this.renderer = renderer;
    const scene = new THREE.Scene();
    this.scene = scene;
    const cam = new THREE.PerspectiveCamera(40, W / H, 10, 4000);
    this.camera = cam;
    this.look = followDesired(this.camJ, this.pet);

    // fog
    const fog = this.lightsJ.fog || { color: '#ffe8c8', near: 420, far: 1400 };
    scene.fog = new THREE.Fog(fog.color, fog.near, fog.far);

    // lights
    this.ambL = new THREE.AmbientLight(0xcfe0f0, 0.55); scene.add(this.ambL);
    this.sunL = new THREE.DirectionalLight(0xffe6b8, 1); this.sunL.castShadow = !!Q.shadows;
    this.sunL.shadow.intensity = (this.lightsJ.sun && this.lightsJ.sun.shadowIntensity) || 0.3;
    this.sunL.shadow.mapSize.set(Q.shadow || 1024, Q.shadow || 1024);
    const sc = this.sunL.shadow.camera; sc.left = -280; sc.right = 280; sc.top = 280; sc.bottom = -160; sc.near = 10; sc.far = 1800;
    this.sunL.shadow.bias = -0.0008;
    scene.add(this.sunL); scene.add(this.sunL.target);
    this.fillL = new THREE.DirectionalLight(0xffe2c4, 0.38); this.fillL.castShadow = false; scene.add(this.fillL);
    this.pointL = [];
    (this.lightsJ.lights || []).forEach(function (l) {
      const pl = new THREE.PointLight(l.color, 0, l.radius || 40, 2);
      pl.position.set(l.x, l.y, l.z); pl.userData.id = l.id; pl.castShadow = false;
      scene.add(pl); self.pointL.push({ light: pl, src: l });
    });

    // ground + outer tile
    const use3 = Q.tex3x;
    const tileIm = use3 ? this.groundIm.t3 : this.groundIm.t1;
    // 外圍 tile：以 (−128,−128) 對齊每 64 units；平面 x±640、z −480…+320（中心 z −80）
    const tile = this._tex(THREE, tileIm, { srgb: true, repeat: [1280 / 64, 800 / 64], flipY: true });
    tile.offset.set(-8, -5.5);
    const tileMat = new THREE.MeshLambertMaterial({ map: tile });
    const tileGeo = new THREE.PlaneGeometry(1280, 800);
    this._flipUVV(tileGeo);
    const tileMesh = new THREE.Mesh(tileGeo, tileMat);
    tileMesh.rotation.x = -Math.PI / 2; tileMesh.position.set(0, -0.2, -80); tileMesh.receiveShadow = !!Q.shadows;
    scene.add(tileMesh); this.tileMesh = tileMesh;

    const gIm = use3 ? this.groundIm.c3 : this.groundIm.c1, aoIm = use3 ? this.groundIm.ao3 : this.groundIm.ao1;
    const gCanvas = this._aoAlbedo(gIm, aoIm);
    const gTex = this._tex(THREE, gCanvas, { srgb: true, flipY: true });
    const gMat = new THREE.MeshLambertMaterial({ map: gTex });
    const gGeo = new THREE.PlaneGeometry(256, 256);
    this._flipUVV(gGeo);   // rotX −90 之後世界 z＝−localY；翻 v 令 v=(z+128)/256（圖頂 z −128）
    const gMesh = new THREE.Mesh(gGeo, gMat);
    gMesh.rotation.x = -Math.PI / 2; gMesh.position.set(0, 0, 0); gMesh.receiveShadow = !!Q.shadows;
    scene.add(gMesh); this.groundMesh = gMesh;

    // meshes + backdrops
    this.meshObj = {}; this.emissiveMat = []; this.backdropMat = [];
    this.objects.forEach(function (o) {
      if (o.type === 'mesh') {
        const m = self.meshJ[o.id], ims = self.meshIm[o.id];
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(m.positions, 3));
        geo.setAttribute('normal', new THREE.Float32BufferAttribute(m.normals, 3));
        geo.setAttribute('uv', new THREE.Float32BufferAttribute(m.uvs, 2));
        geo.setIndex(m.indices);
        // mesh UV 係 V 上、原點左下（three.js 慣例）→ flipY 保持預設 true
        const cmap = self._tex(THREE, use3 ? ims.c3 : ims.c1, { srgb: true });
        const mat = new THREE.MeshLambertMaterial({
          map: cmap, alphaTest: m.alphaTest == null ? 0.5 : m.alphaTest, transparent: false,
          side: THREE.FrontSide
        });
        if (m.emissive && (ims.e1 || ims.e3)) {
          mat.emissive = new THREE.Color(0xffffff);
          mat.emissiveMap = self._tex(THREE, use3 ? ims.e3 : ims.e1, { srgb: true });
          mat.emissiveIntensity = 0;
          self.emissiveMat.push({ mat: mat, light: o.emissiveLight });
        }
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(o.x, o.y || 0, o.z);
        mesh.rotation.y = (o.yawDeg || 0) * Math.PI / 180;
        mesh.castShadow = !!(Q.shadows && o.castShadow);
        mesh.receiveShadow = !!(Q.shadows && o.receiveShadow);
        mesh.userData.id = o.id;
        scene.add(mesh); self.meshObj[o.id] = mesh;
      } else if (o.type === 'backdrop') {
        const ims = self.meshIm[o.id];
        const tex = self._tex(THREE, use3 ? ims.c3 : ims.c1, { srgb: true, flipY: true });
        const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: 0.05, depthWrite: false, fog: false });
        const plane = new THREE.Mesh(new THREE.PlaneGeometry(o.w, o.h), mat);
        // pivot [0.5, 1]＝底中；原點喺 (x, 0, z)，板向上
        const pv = o.pivot || [0.5, 1];
        plane.position.set(o.x + (0.5 - pv[0]) * o.w, o.h * (1 - pv[1]) + o.h / 2, o.z);
        plane.rotation.y = (o.yawDeg || 0) * Math.PI / 180;
        plane.frustumCulled = false;
        plane.renderOrder = -10;
        scene.add(plane); self.meshObj[o.id] = plane;
        self.backdropMat = self.backdropMat || [];
        self.backdropMat.push(mat);
      }
    });

    // pet billboard（圓柱面向）＋軟影
    const petGeo = new THREE.PlaneGeometry(64, 64);
    this.petCanvas = document.createElement('canvas'); this.petCanvas.width = 64; this.petCanvas.height = 64;
    this.petTex = this._tex(THREE, this.petCanvas, { srgb: true, flipY: false });
    this.petEmTex = this._tex(THREE, this.petCanvas, { srgb: true, flipY: false }); // replaced per frame
    this.petMat = new THREE.MeshLambertMaterial({ map: this.petTex, alphaTest: 0.5, transparent: false, side: THREE.DoubleSide });
    this.petMat.emissive = new THREE.Color(0xffffff);
    this.petMesh = new THREE.Mesh(petGeo, this.petMat);
    this.petMesh.castShadow = false; this.petMesh.receiveShadow = false;
    this.petMesh.userData.id = 'pet';
    // pivot (32,61)：腳底大約 y=0 → 平面中心要喺 y = 64-61 = 3 之上再加一半？平面高 64，中心喺幾何中心。
    // 腳底喺局部 (0, −(64-61), 0) 相對中心＝中心喺腳底上方 61。所以 mesh.position.y = 61（當腳底 y=0）。
    // 但 PlaneGeometry 中心係幾何中心，pivot 係 (32,61) 由頂向下。圖 v 向上（flipY false）時，
    // 圖底喺 y=-32，圖頂 y=+32。pivot y=61 由頂向下 → 離底 64-61=3 px，即腳底喺幾何 y = -32+3 = -29。
    // 所以要 position.y = 29 令腳底喺 y=0。更清楚：offset = (py - h/2) 若 v 上從底計 pivot 離底 = h-py = 3，中心離腳底 = h/2 - 3 = 29。
    this.petYOffset = 64 / 2 - (64 - 61); // 29
    this.petMesh.position.set(0, this.petYOffset, 0);
    scene.add(this.petMesh);

    // blob shadow
    const shC = document.createElement('canvas'); shC.width = 64; shC.height = 64;
    const sx = shC.getContext('2d'); const grd = sx.createRadialGradient(32, 32, 0, 32, 32, 30);
    grd.addColorStop(0, 'rgba(10,20,20,0.45)'); grd.addColorStop(1, 'rgba(10,20,20,0)');
    sx.fillStyle = grd; sx.fillRect(0, 0, 64, 64);
    const shTex = this._tex(THREE, shC, { srgb: false, flipY: true });
    const shMat = new THREE.MeshBasicMaterial({ map: shTex, transparent: true, depthWrite: false });
    this.shadowMesh = new THREE.Mesh(new THREE.PlaneGeometry(28, 18), shMat);
    this.shadowMesh.rotation.x = -Math.PI / 2; this.shadowMesh.position.set(0, 0.15, 0);
    scene.add(this.shadowMesh);

    this._applyLights(0, 0);
    this._placeCamera(0);
  };

  Scene.prototype._applyLights = function (night, t) {
    if (!this.lightsJ || !this.ambL) return;
    const M = mixLights(this.lightsJ, night);
    this._night = night;
    const ac = M.ambColor;
    this.ambL.color.setRGB(ac[0] / 255, ac[1] / 255, ac[2] / 255);
    this.ambL.intensity = M.ambIntensity;
    this.sunL.color.set(M.sunColor);
    this.sunL.intensity = M.sun;
    const sd = M.sunDir;
    this.sunL.position.set(-sd[0], -sd[1], -sd[2]).multiplyScalar(900);
    this.sunL.target.position.set(0, 40, -20);
    this.sunL.shadow.intensity = M.shadowIntensity;
    this.fillL.color.set(M.fillColor);
    this.fillL.intensity = M.fill;
    const fd = M.fillDir;
    this.fillL.position.set(-fd[0], -fd[1], -fd[2]).multiplyScalar(700);
    const self = this;
    this.pointL.forEach(function (p) {
      const src = M.points.filter(function (q) { return q.id === p.src.id; })[0];
      let I = src ? src.intensity : 0;
      if (src && src.flicker && t != null) I *= 1 + src.flicker * Math.sin(t * 8 + (p.src.x || 0));
      p.light.intensity = I * 2.2;
    });
    this.emissiveMat.forEach(function (e) {
      // glb emissiveFactor＝1，呢度乘返 emissiveLight 強度。小屋側窗改跟 window_side（同 window 一張 emissive 圖就用較大嗰個）。
      let ids = (e.lights || (e.light ? [e.light] : [])).slice();
      if (e.light === 'window' && ids.indexOf('window_side') < 0) ids.push('window_side');
      let I = 0;
      ids.forEach(function (id) { if (M.byId[id] != null) I = Math.max(I, M.byId[id]); });
      e.mat.emissiveIntensity = I;
    });
    if (this.scene && this.scene.fog && M.fog) {
      const fc = night > 0.5 ? 0x4a5a90 : M.fog.color;
      this.scene.fog.color.set(fc);
    }
    if (this.renderer) {
      const cc = night > 0.5 ? 0x2a3358 : 0xffe8c8;
      this.renderer.setClearColor(cc, 1);
    }
    // 背景板未有夜景圖：夜晚將 unlit 板乘暗藍，唔好停喺日頭色
    if (this.backdropMat) {
      const r = 1 - night * 0.72, g = 1 - night * 0.68, b = 1 - night * 0.45;
      this.backdropMat.forEach(function (m) { m.color.setRGB(r, g, b); });
    }
    this._lit = M;
  };

  Scene.prototype._placeCamera = function (dt) {
    const cam = this.camJ; if (!cam || !this.camera) return;
    const des = followDesired(cam, this.pet);
    if (!this.look) this.look = des.slice();
    if (this.followOn) this.look = followStep(this.look, des, dt || 0, cam.followDamping);
    else this.look = (cam.target || [0, 30, -72]).slice();
    const auto = this.swayOn ? swayYaw(this.t, cam) : 0;
    this.yaw = clampYaw(auto, cam, this.userYaw);
    const P = camPos(this.look, this.yaw, cam);
    this.camera.fov = cam.fovDeg || 40;
    this.camera.near = cam.near || 10;
    this.camera.far = cam.far || 4000;
    this.camera.aspect = W / H;
    this.camera.position.set(P[0], P[1], P[2]);
    this.camera.lookAt(this.look[0], this.look[1], this.look[2]);
    this.camera.updateProjectionMatrix();
    this.camera.updateMatrixWorld();
  };

  Scene.prototype._dir4Frame = function (name, flip) {
    const J = this.dir4 && this.dir4.json, fr = J && J.frames[name]; if (!fr) return null;
    const f = fr.frame, c = this.petCanvas, x = c.getContext('2d');
    x.imageSmoothingEnabled = false; x.clearRect(0, 0, 64, 64);
    if (flip) { x.save(); x.translate(64, 0); x.scale(-1, 1); }
    x.drawImage(this.dir4.img, f.x, f.y, f.w, f.h, 0, 0, 64, 64);
    if (flip) x.restore();
    this.petTex.needsUpdate = true;
    // emissive
    if (!this.petEmCanvas) { this.petEmCanvas = document.createElement('canvas'); this.petEmCanvas.width = 64; this.petEmCanvas.height = 64; }
    const e = this.petEmCanvas.getContext('2d'); e.imageSmoothingEnabled = false; e.clearRect(0, 0, 64, 64);
    if (flip) { e.save(); e.translate(64, 0); e.scale(-1, 1); }
    e.drawImage(this.dir4.e, f.x, f.y, f.w, f.h, 0, 0, 64, 64);
    if (flip) e.restore();
    if (!this.petEmTex2) {
      const THREE = window.THREE;
      this.petEmTex2 = this._tex(THREE, this.petEmCanvas, { srgb: true, flipY: false });
      this.petMat.emissiveMap = this.petEmTex2;
    } else this.petEmTex2.needsUpdate = true;
    // normal map：左方向鏡像之後要反 R channel（R → 255−R）
    if (this.dir4.n) {
      if (!this.petNCanvas) { this.petNCanvas = document.createElement('canvas'); this.petNCanvas.width = 64; this.petNCanvas.height = 64; }
      const nctx = this.petNCanvas.getContext('2d', { willReadFrequently: true });
      nctx.imageSmoothingEnabled = false; nctx.clearRect(0, 0, 64, 64);
      if (flip) { nctx.save(); nctx.translate(64, 0); nctx.scale(-1, 1); }
      nctx.drawImage(this.dir4.n, f.x, f.y, f.w, f.h, 0, 0, 64, 64);
      if (flip) nctx.restore();
      if (flip) {
        const id = nctx.getImageData(0, 0, 64, 64), d = id.data;
        for (let i = 0; i < d.length; i += 4) d[i] = 255 - d[i];
        nctx.putImageData(id, 0, 0);
      }
      if (!this.petNTex) {
        const THREE = window.THREE;
        this.petNTex = this._tex(THREE, this.petNCanvas, { srgb: false, flipY: false });
        this.petMat.normalMap = this.petNTex;
      } else this.petNTex.needsUpdate = true;
    }
    return fr;
  };

  Scene.prototype.setPetSprite = function (src, o) {
    o = o || {}; this._fbSprite = src ? { src: src, mir: o.mir || 1, px: src.px, py: src.py } : null;
  };

  Scene.prototype._fallbackFrame = function () {
    const fb = this._fbSprite, src = fb && fb.src; if (!src || !src.img) return false;
    const c = this.petCanvas, x = c.getContext('2d');
    x.imageSmoothingEnabled = false; x.clearRect(0, 0, 64, 64);
    const mir = fb.mir < 0;
    const dx = 32 - src.px, dy = 61 - src.py;
    if (mir) { x.save(); x.translate(64, 0); x.scale(-1, 1); }
    x.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, mir ? (64 - (dx + src.sw)) : dx, dy, src.sw, src.sh);
    if (mir) x.restore();
    this.petTex.needsUpdate = true;
    return true;
  };

  Scene.prototype._updatePet = function () {
    if (!this.petMesh) return;
    const p = this.pet;
    this.petMesh.position.set(p.x, this.petYOffset, p.z);
    this.shadowMesh.position.set(p.x, 0.15, p.z);
    // cylindrical face camera
    const cx = this.camera.position.x - p.x, cz = this.camera.position.z - p.z;
    this.petMesh.rotation.set(0, Math.atan2(cx, cz), 0);
    const useDir4 = this.dir4 && (!p.form || p.form === 'radiant' || p.form === 'bright' || p.fk === 'radiant' || p.fk === 'evo_still_radiant' || p.useDir4);
    // 試點得 radiant 一隻 dir4；其他形態用 2D sprite 後備
    const isRadiant = !p.form || p.form === 'radiant' || p.fk === 'radiant' || p.useDir4 === true;
    if (isRadiant && this.dir4) {
      const info = p.facing || dirOf(p.dx || 0, p.dz || 0, !!p.moving);
      const name = frameName(info, this.t);
      this._dir4Frame(name, !!info.flip);
      this._lastFrame = name;
      this.petMat.emissiveIntensity = (p.glow == null ? 1 : p.glow);
    } else {
      this._fallbackFrame();
      this.petMat.emissiveIntensity = (p.glow == null ? 1 : p.glow) * 0.2;
      this._lastFrame = 'fallback';
    }
    this.petMesh.visible = !p.hidden;
    this.shadowMesh.visible = !p.hidden;
  };

  Scene.prototype.update = function (dt, ctx) {
    dt = Math.max(0, Math.min(dt || 0, 0.1)); this.t += dt;
    ctx = ctx || {};
    if (ctx.pet) {
      this.pet.x = ctx.pet.x != null ? ctx.pet.x : this.pet.x;
      this.pet.z = ctx.pet.z != null ? ctx.pet.z : this.pet.z;
      this.pet.dx = ctx.pet.dx != null ? ctx.pet.dx : this.pet.dx;
      this.pet.dz = ctx.pet.dz != null ? ctx.pet.dz : this.pet.dz;
      this.pet.moving = !!ctx.pet.moving;
      this.pet.glow = ctx.pet.glow != null ? ctx.pet.glow : this.pet.glow;
      this.pet.form = ctx.pet.form || this.pet.form;
      this.pet.fk = ctx.pet.fk;
      this.pet.hidden = !!ctx.pet.hidden;
      const fac = (this.pet.dx || this.pet.dz) ? dirOf(this.pet.dx, this.pet.dz, this.pet.moving) : (this.pet.facing || dirOf(0, 1, false));
      if (ctx.pet.facing) this.pet.facing = ctx.pet.facing;
      else if (this.pet.moving) this.pet.facing = fac;
      else if (this.pet.facing) this.pet.facing.clip = 'idle';
    }
    if (this._forcePet) {
      if (this._forcePet.x != null) this.pet.x = this._forcePet.x;
      if (this._forcePet.z != null) this.pet.z = this._forcePet.z;
      if (this._forcePet.hidden != null) this.pet.hidden = !!this._forcePet.hidden;
    }
    const hour = ctx.hour != null ? ctx.hour : 8;
    const forced = ctx.night; // 0/1 override
    const night = forced == null ? nightMix(hour) : +forced;
    this._applyLights(night, this.t);
    this._placeCamera(dt);
    this._updatePet();
    return this;
  };

  Scene.prototype.resize = function (k) {
    k = k || 2; if (!this.renderer) return;
    this.renderer.setSize(W * k, H * k, false);
    if (this.camera) { this.camera.aspect = W / H; this.camera.updateProjectionMatrix(); }
    this.k = k;
  };

  Scene.prototype.draw = function (ctx, k, _opt) {
    if (!this.on() || !this.renderer) return false;
    const t0 = (typeof performance !== 'undefined' && performance.now) ? performance.now() : 0;
    this.resize(k || this.k || 2);
    this.renderer.render(this.scene, this.camera);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(this.canvas, 0, 0);
    const ms = ((typeof performance !== 'undefined' && performance.now) ? performance.now() : 0) - t0;
    this.stat.draws++; this.stat.lastMs = ms; this.stat.ms += ms;
    this.perf.n++; this.perf.sum += ms; this.perf.max = Math.max(this.perf.max, ms); this.perf.last = ms;
    this.perf.acc += ms; this.perf.fn++;
    if (this.perf.fn >= 30) { this.perf.drawMs = this.perf.acc / this.perf.fn; this.perf.acc = 0; this.perf.fn = 0; }
    return true;
  };

  Scene.prototype.project = function (x, y, z) {
    if (!this.camera) return worldToArtFlat(x, z);
    const THREE = window.THREE;
    const v = new THREE.Vector3(x, y, z).project(this.camera);
    return { x: (v.x * 0.5 + 0.5) * W, y: (-v.y * 0.5 + 0.5) * H, ndc: [v.x, v.y, v.z] };
  };
  Scene.prototype.petDraw = function () {
    const p = this.pet, foot = this.project(p.x, 0, p.z), head = this.project(p.x, 64, p.z);
    const y0 = Math.min(foot.y, head.y), y1 = Math.max(foot.y, head.y);
    const w = 40, h = Math.max(24, y1 - y0);
    return { x: foot.x - w / 2, y: y0, w: w, h: h, bud: { x: foot.x, y: y0 + 8 }, footY: foot.y, g3d: true };
  };
  Scene.prototype.petHit = function (ax, ay) {
    const box = this.petDraw();
    return ax >= box.x && ax <= box.x + box.w && ay >= box.y && ay <= box.y + box.h;
  };
  Scene.prototype.occluded = function (x, z) {
    if (!this.camera || !window.THREE) return false;
    const THREE = window.THREE;
    const origin = this.camera.position.clone();
    const target = new THREE.Vector3(x, 20, z);
    const dir = target.clone().sub(origin).normalize();
    const ray = new THREE.Raycaster(origin, dir);
    const meshes = [];
    this.scene.traverse(function (o) { if (o.isMesh && o.userData && o.userData.id && o.userData.id !== 'pet') meshes.push(o); });
    const hits = ray.intersectObjects(meshes, false);
    if (!hits.length) return false;
    const petDist = origin.distanceTo(target);
    return hits[0].distance + 1 < petDist;
  };
  Scene.prototype.setQuality = function (q) {
    if (q !== 'high' && q !== 'mid' && q !== 'low') return this.quality;
    const prev = this.quality; this.quality = q; lsSet(KEY_Q, q);
    if (this.loaded && prev !== q && q !== 'low') {
      try { this._build(window.THREE); } catch (e) { this.error = String(e && e.message || e); }
    }
    return this.quality;
  };
  Scene.prototype.setSway = function (on) { this.swayOn = !!on; lsSet(KEY_SWAY, on ? '1' : '0'); return this.swayOn; };
  Scene.prototype.setFollow = function (on) { this.followOn = !!on; lsSet(KEY_FOLLOW, on ? '1' : '0'); return this.followOn; };
  Scene.prototype.orbit = function (deg) {
    const cam = this.camJ || { orbitMinDeg: -10, orbitMaxDeg: 10 };
    this.userYaw = clamp(deg, cam.orbitMinDeg, cam.orbitMaxDeg);
    this._placeCamera(0); return this.userYaw;
  };
  Scene.prototype.autoDrop = function (avgMs, slowMs) {
    if (this.quality === 'low') return this.quality;
    if (avgMs > (slowMs || 28)) {
      const nq = this.quality === 'high' ? 'mid' : 'low';
      this.setQuality(nq); return nq;
    }
    return this.quality;
  };

  /* ── 開發者模式：畫質／擺鏡／跟拍／fps 面板 ── */
  function mountPerf(G, S) {
    if (typeof document === 'undefined') return;
    let el = document.getElementById('g3dPerf');
    if (!el) {
      el = document.createElement('div'); el.id = 'g3dPerf'; el.dataset.testid = 'g3d-perf';
      el.style.cssText = 'display:none;position:absolute;right:8px;top:112px;z-index:7;padding:4px 8px;border-radius:8px;font:700 11px/16px sans-serif;color:#fff3d6;background:rgba(14,16,34,.82);border:1px solid rgba(255,214,110,.55);pointer-events:none;white-space:pre';
      const ui = document.getElementById('ui'); if (ui) ui.appendChild(el); else document.body.appendChild(el);
    }
    S.perfEl = el;
    S.showPerf = S.showPerf || lsGet('glimmer.g3d.perf', '0') === '1';
    el.style.display = S.showPerf ? 'block' : 'none';
  }
  function tickPerf(S) {
    if (!S.perfEl || !S.showPerf) return;
    const fps = S.stat.fps ? S.stat.fps.toFixed(0) : '—';
    const ms = (S.stat.lastFrameMs != null) ? S.stat.lastFrameMs.toFixed(1) : (S.perf.last ? S.perf.last.toFixed(1) : '—');
    const on = S.on() ? ('3D ' + S.quality) : '2D 後備';
    S.perfEl.textContent = on + '  ' + fps + ' fps  ' + ms + ' ms/幀\n耗電：' + (S.quality === 'high' ? '高（影圖＋@3x）' : S.quality === 'mid' ? '中（1x＋較細影）' : '低（2D）');
  }

  function install(G, NS) {
    const D = NS.data, P = D.PARAMS, qs = new URLSearchParams(location.search);
    const savedQ = lsGet(KEY_Q, '');
    const det = detectQuality({
      qs: { '3d': qs.get('3d') },
      webgl: hasWebGL(),
      hardwareConcurrency: navigator.hardwareConcurrency,
      deviceMemory: navigator.deviceMemory,
      lowEndCores: (P.quality && P.quality.lowEndCores) || 4,
      lowEndMemGB: (P.quality && P.quality.lowEndMemGB) || 4
    });
    let quality = det.quality;
    if (savedQ && !qs.get('3d') && (savedQ === 'high' || savedQ === 'mid' || savedQ === 'low')) quality = savedQ;
    const S = new Scene({
      base: (P.art && P.art.base || 'art/') + 'garden3d/H1/',
      dir4base: (P.art && P.art.base || 'art/') + 'garden3d/dir4/',
      enabled: det.want || quality !== 'low',
      quality: quality,
      swayOn: lsGet(KEY_SWAY, '1') !== '0',
      followOn: lsGet(KEY_FOLLOW, '1') !== '0'
    });
    if (qs.get('3d') === '0') { S.enabled = false; S.quality = 'low'; }
    G.g3d = S; if (G.renderer) G.renderer.g3d = S;
    const loadP = (S.enabled && S.quality !== 'low') ? S.load() : Promise.resolve(false);
    G.g3dLoad = loadP;
    loadP.then(function (ok) {
      if (!ok && S.quality !== 'low' && qs.get('3d') !== '0') { S.quality = 'low'; }
      if (G.renderer) G.renderer.g3d = S;
    });
    mountPerf(G, S);

    // 自動降畫質（自己嘅窗口，唔改現有 2D quality auto）
    const qm = { sum: 0, n: 0, slow: 0, grace: 90 };
    S.noteFrame = function (frameMs) {
      // 用整幀 wall-clock（render.js frame()）計 fps，唔好用 WebGL 單獨耗時
      S.stat.lastFrameMs = frameMs;
      S.perf.fAcc = (S.perf.fAcc || 0) + frameMs; S.perf.fN = (S.perf.fN || 0) + 1;
      if (S.perf.fN >= 30) { S.stat.fps = S.perf.fAcc > 0 ? 1000 / (S.perf.fAcc / S.perf.fN) : 0; S.perf.fAcc = 0; S.perf.fN = 0; }
      tickPerf(S);
      if (S.quality === 'low' || !S.on()) return;
      if (qm.grace > 0) { qm.grace--; return; }
      qm.sum += frameMs; qm.n++;
      if (qm.n >= 120) {
        const avg = qm.sum / qm.n; qm.sum = 0; qm.n = 0;
        if (avg > 28) qm.slow++; else qm.slow = 0;
        if (qm.slow >= 2) {
          const nq = S.autoDrop(99, 1);
          qm.slow = 0; qm.grace = 90;
          if (NS.ui && NS.ui.toast) NS.ui.toast(nq === 'low' ? '效能較低，已轉返 2D 花園' : '效能較低，已降低 3D 畫質');
        }
      }
    };

    // 拖鏡（空地水平拖）
    if (typeof document !== 'undefined') {
      const cv = G.renderer && G.renderer.canvas;
      if (cv) {
        cv.addEventListener('pointerdown', function (e) {
          if (!S.on() || (G.ui && G.ui.isModalOpen && G.ui.isModalOpen())) return;
          const art = G.renderer.screenToArt(e.clientX, e.clientY);
          if (S.petHit(art.x, art.y)) return;
          if (art.y < 38 || art.y > 360) return;
          S._drag = { x0: e.clientX, y0: e.clientY, yaw0: S.userYaw, moved: false, id: e.pointerId };
        });
        cv.addEventListener('pointermove', function (e) {
          const d = S._drag; if (!d || d.id !== e.pointerId) return;
          const dx = e.clientX - d.x0;
          if (!d.moved && Math.abs(dx) < 16) return;
          d.moved = true;
          try { cv.setPointerCapture(e.pointerId); } catch (err) { }
          S.orbit(d.yaw0 - dx * 0.05);
        });
        const up = function (e) { if (S._drag && S._drag.id === e.pointerId) S._drag = null; };
        cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
      }
    }

    window.__qa = window.__qa || {};
    window.__qa.g3d = {
      on: function () { return S.on(); },
      ready: function () { return !!S.ready; },
      quality: function () { return S.quality; },
      setQuality: function (q) { return S.setQuality(q); },
      meshes: function () { return S.stat.meshes; },
      error: function () { return S.error; },
      night: function () { return S._night; },
      yaw: function () { return S.yaw; },
      look: function () { return S.look && S.look.slice(); },
      pet: function () { return { x: S.pet.x, z: S.pet.z, frame: S._lastFrame, facing: S.pet.facing }; },
      forcePet: function (p) { S._forcePet = p || null; return S._forcePet; },
      project: function (x, y, z) { return S.project(x, y, z); },
      petDraw: function () { return S.petDraw(); },
      petHit: function (x, y) { return S.petHit(x, y); },
      occluded: function (x, z) { return S.occluded(x == null ? S.pet.x : x, z == null ? S.pet.z : z); },
      orbit: function (d) { return S.orbit(d); },
      setSway: function (v) { return S.setSway(v); },
      setFollow: function (v) { return S.setFollow(v); },
      swayOn: function () { return S.swayOn; },
      followOn: function () { return S.followOn; },
      fps: function () { return S.stat.fps; },
      lastMs: function () { return S.stat.lastMs; },
      lastFrameMs: function () { return S.stat.lastFrameMs; },
      lit: function () { return S._lit && { sun: S._lit.sun, fill: S._lit.fill, night: S._lit.night, byId: S._lit.byId }; },
      blocked: function (x, z) { return blocked(S.objects, x, z, (S.objJ && S.objJ.pet && S.objJ.pet.radius) || 10); },
      showPerf: function (v) { S.showPerf = v !== false; lsSet('glimmer.g3d.perf', S.showPerf ? '1' : '0'); if (S.perfEl) S.perfEl.style.display = S.showPerf ? 'block' : 'none'; return S.showPerf; },
      reload: function () { return S.load(); }
    };

    const DEV = {
      id: 'g3d', title: '3D 花園 H1', order: 13,
      status: function () { return (S.on() ? ('3D ' + S.quality) : (qs.get('3d') === '0' ? '?3d=0 2D' : '2D 後備')) + '・擺鏡 ' + (S.swayOn ? '開' : '關') + '・跟拍 ' + (S.followOn ? '開' : '關'); },
      items: [
        { k: 'high', label: '畫質：高（3D）', run: function () { S.setQuality('high'); if (!S.ready) S.load(); return { ok: true, msg: '3D 畫質 → 高' }; } },
        { k: 'mid', label: '畫質：中（3D）', run: function () { S.setQuality('mid'); if (!S.ready) S.load(); return { ok: true, msg: '3D 畫質 → 中' }; } },
        { k: 'low', label: '畫質：低（2D 後備）', run: function () { S.setQuality('low'); return { ok: true, msg: '已轉返 2D 花園' }; } },
        { k: 'sway', label: '鏡頭自動擺（預設開）', run: function () { const v = S.setSway(!S.swayOn); return { ok: true, msg: v ? '自動擺鏡開' : '自動擺鏡關' }; } },
        { k: 'follow', label: '鏡頭跟拍（預設開）', run: function () { const v = S.setFollow(!S.followOn); return { ok: true, msg: v ? '跟拍開' : '跟拍關' }; } },
        { k: 'perf', label: 'fps／耗電面板', run: function () { const v = !S.showPerf; window.__qa.g3d.showPerf(v); return { ok: true, msg: v ? '面板開' : '面板關' }; } },
        { k: 'off', label: '轉返 2D（?3d=0）', run: function () { const q = new URLSearchParams(location.search); q.set('3d', '0'); setTimeout(function () { location.search = q.toString(); }, 50); return { ok: true, msg: '重新載入 2D…' }; } }
      ]
    };
    if (NS) { if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV); }
    return S;
  }

  return {
    W: W, H: H, CX: CX, GROUND_Y: GROUND_Y, ZSCALE: ZSCALE, QSET: QSET,
    artToWorld: artToWorld, worldToArtFlat: worldToArtFlat, petWorld: petWorld,
    nightMix: nightMix, mixLights: mixLights,
    swayYaw: swayYaw, followDesired: followDesired, followStep: followStep, camPos: camPos, clampYaw: clampYaw,
    dirOf: dirOf, frameName: frameName,
    fpDist: fpDist, blocked: blocked,
    detectQuality: detectQuality, hasWebGL: hasWebGL,
    Scene: Scene, install: install
  };
});
