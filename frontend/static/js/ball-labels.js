// Exact decoded images are reviewed locally; this tool makes no network requests.
(() => {
  const byId = id => document.getElementById(id);
  const canvas = byId('label-canvas'), ctx = canvas.getContext('2d');
  const loupe = byId('label-loupe'), lens = loupe.getContext('2d');
  const fields = ['box-left', 'box-top', 'box-right', 'box-bottom'].map(byId);
  const states = {visible: 'Ball box saved', not_visible: 'Not visible', uncertain: 'Uncertain'};
  const shaPattern = /^[a-f0-9]{64}$/;
  let manifest = null, files = new Map(), labels = new Map(), current = 0;
  let image = null, draft = null, anchor = null, generation = 0, renderVersion = 0;
  const message = text => { byId('label-message').textContent = text; };
  const hash = async file => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', await file.arrayBuffer())))
    .map(v => v.toString(16).padStart(2, '0')).join('');
  const frame = () => manifest?.frames[current];

  function validBox(box) {
    if (!manifest || !Array.isArray(box) || box.length !== 4 || !box.every(Number.isFinite)) return false;
    const [w, h] = manifest.source_dimensions;
    return box[0] >= 0 && box[1] >= 0 && box[2] > box[0] && box[3] > box[1] && box[2] <= w && box[3] <= h;
  }
  function checkManifest(m) {
    if (m.schema_version !== 1 || m.coordinate_space !== 'source_image_xyxy' ||
        !/^[a-z0-9][a-z0-9-]{0,63}$/.test(m.recording_id) || !shaPattern.test(m.source_sha256) ||
        !Array.isArray(m.source_dimensions) || m.source_dimensions.length !== 2 ||
        !m.source_dimensions.every(v => Number.isInteger(v) && v >= 2) ||
        m.source_dimensions[0] > 1920 || m.source_dimensions[1] > 1080 ||
        !Array.isArray(m.frames) || !m.frames.length || m.frames.length > 120) throw Error('Use a prepared source-frame manifest.');
    let lastIndex = -1, lastTime = -1;
    for (const f of m.frames) {
      if (!Number.isInteger(f.frame_index) || f.frame_index <= lastIndex ||
          f.filename !== `frame-${String(f.frame_index).padStart(6, '0')}.png` || !shaPattern.test(f.image_sha256) ||
          !Number.isFinite(f.timestamp_seconds) || f.timestamp_seconds < 0 || f.timestamp_seconds <= lastTime ||
          !['presentation', 'fps_fallback'].includes(f.timestamp_source)) throw Error('Invalid frame provenance in manifest.');
      lastIndex = f.frame_index; lastTime = f.timestamp_seconds;
    }
  }
  function sync() {
    const loaded = Boolean(manifest && image);
    ['label-save','label-absent','label-uncertain'].forEach(id => { byId(id).disabled = !loaded; });
    byId('label-remove').disabled = !loaded || !labels.has(frame().frame_index);
    byId('label-prev').disabled = !loaded || current === 0;
    byId('label-next').disabled = !loaded || current === manifest.frames.length-1;
    byId('label-select').disabled = !loaded;
    byId('label-import').disabled = !loaded;
    byId('label-download').disabled = !loaded || labels.size === 0;
    byId('label-progress').textContent = manifest ? `${labels.size} / ${manifest.frames.length} reviewed` : 'No frames loaded';
    byId('label-state').textContent = loaded ? (states[labels.get(frame().frame_index)?.visibility] || 'Unreviewed') : 'Unreviewed';
    if (manifest) Array.from(byId('label-select').options).forEach((option, i) => {
      const f = manifest.frames[i]; option.textContent = `Frame ${f.frame_index} — ${states[labels.get(f.frame_index)?.visibility] || 'Unreviewed'}`;
    });
  }
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!image) return;
    ctx.drawImage(image, 0, 0);
    const box = draft || labels.get(frame().frame_index)?.bbox;
    ctx.strokeStyle = '#ffb469'; ctx.lineWidth = Math.max(1, canvas.width/500);
    if (box) ctx.strokeRect(box[0], box[1], box[2]-box[0], box[3]-box[1]);
    if (anchor) {ctx.beginPath(); ctx.arc(...anchor, 3, 0, 2*Math.PI); ctx.stroke();}
  }
  function magnify(x, y) {
    lens.clearRect(0, 0, 200, 160);
    if (!image) return;
    const left = Math.min(image.width-50, Math.max(0, x-25));
    const top = Math.min(image.height-40, Math.max(0, y-20));
    lens.imageSmoothingEnabled = false;
    lens.drawImage(image, left, top, 50, 40, 0, 0, 200, 160);
    const box = draft || labels.get(frame().frame_index)?.bbox;
    if (box) {lens.strokeStyle = '#ffb469';lens.lineWidth = 1; lens.strokeRect((box[0]-left)*4, (box[1]-top)*4, (box[2]-box[0])*4, (box[3]-box[1])*4);}
  }
  async function openFrame(index) {
    current = index; draft = null; anchor = null; fields.forEach(f => {f.value = '';});
    image?.close(); image = null; draw(); sync();
    const version = ++renderVersion, selected = frame();
    try {
      const bitmap = await createImageBitmap(files.get(selected.filename));
      if (version !== renderVersion) {bitmap.close();return;}
      if (bitmap.width !== manifest.source_dimensions[0] || bitmap.height !== manifest.source_dimensions[1]) {bitmap.close();throw Error('Frame size differs from the manifest.');}
      image = bitmap;canvas.width = bitmap.width;canvas.height = bitmap.height;
      byId('label-empty').hidden = true;byId('label-image-area').hidden = false;
      byId('label-frame-name').textContent = `Frame ${selected.frame_index}`;
      byId('label-frame-time').textContent = `${selected.timestamp_seconds.toFixed(3)} s (${selected.timestamp_source === 'presentation' ? 'source time' : 'FPS fallback'})`;
      byId('label-select').value = String(index);
      const saved = labels.get(selected.frame_index);
      if (saved?.bbox) {draft = [...saved.bbox];fields.forEach((f,i) => {f.value = draft[i];});}
      draw();magnify(saved?.bbox?.[0] ?? bitmap.width/2, saved?.bbox?.[1] ?? bitmap.height/2);sync();
      message(saved ? 'Saved label loaded. You can replace or clear it.' : 'Select two corners around the ball, or choose a visibility state.');
    } catch (error) {if (version === renderVersion) message(error.message);}
  }
  byId('label-files').addEventListener('change', async event => {
    const selected = Array.from(event.target.files), nextGeneration = ++generation;
    if (!selected.length) return;
    const previous = {manifest,files,labels};
    message('Checking local frame checksums…');
    try {
      if (selected.length > 121 || selected.reduce((n,f) => n+f.size,0) > 128*1024*1024) throw Error('Open at most 120 images and one manifest, up to 128 MiB.');
      const incoming = new Map(selected.map(f => [f.name,f]));
      if (incoming.size !== selected.length) throw Error('Choose files with unique names from one bundle.');
      const meta = incoming.get('manifest.json');
      if (!meta || meta.size > 1024*1024) throw Error('Include the prepared manifest.json with the PNG images.');
      const m = JSON.parse(await meta.text());checkManifest(m);
      for (const f of m.frames) {
        const file = incoming.get(f.filename);
        if (!file || file.size > 8*1024*1024 || await hash(file) !== f.image_sha256) throw Error(`Missing or changed image: ${f.filename}`);
      }
      if (nextGeneration !== generation) return;
      manifest = m;files = incoming;labels = new Map();
      byId('label-source').textContent = `${m.recording_id} · ${m.source_dimensions.join(' × ')} source pixels`;
      byId('label-select').replaceChildren(...m.frames.map((_, i) => {const o = document.createElement('option');o.value = String(i);return o;}));
      await openFrame(0);
    } catch (error) {if (nextGeneration === generation) {({manifest,files,labels} = previous);message(error.message);sync();}}
    event.target.value = '';
  });
  function save(visibility, bbox = null) {
    if (!image) return;
    if (visibility === 'visible' && !validBox(bbox)) {message('Enter a nonempty box inside the source image.');return;}
    labels.set(frame().frame_index, {frame_index: frame().frame_index, image_sha256: frame().image_sha256, visibility, bbox});
    draft = bbox ? [...bbox] : null;anchor = null;
    if (!bbox) fields.forEach(f => {f.value = '';});
    draw();sync();message(`${states[visibility]}. Move to the next frame when ready.`);
  }
  byId('label-box-form').addEventListener('submit', event => {event.preventDefault();save('visible', fields.map(f => Number(f.value)));});
  byId('label-absent').addEventListener('click', () => save('not_visible'));
  byId('label-uncertain').addEventListener('click', () => save('uncertain'));
  byId('label-remove').addEventListener('click', () => {labels.delete(frame().frame_index);draft = null;anchor = null;fields.forEach(f => {f.value = '';});draw();sync();message('Label cleared. This frame is excluded until reviewed again.');});
  byId('label-prev').addEventListener('click', () => openFrame(current-1));
  byId('label-next').addEventListener('click', () => openFrame(current+1));
  byId('label-select').addEventListener('change', e => openFrame(Number(e.target.value)));
  function point(event) {const r = canvas.getBoundingClientRect();return [Math.min(canvas.width,Math.max(0,(event.clientX-r.left)*canvas.width/r.width)),Math.min(canvas.height,Math.max(0,(event.clientY-r.top)*canvas.height/r.height))];}
  canvas.addEventListener('click', event => {
    if (!image) return;
    const p = point(event);
    if (!anchor) {anchor = p;draft = null;message('Select the opposite corner.');}
    else {draft = [Math.min(anchor[0],p[0]),Math.min(anchor[1],p[1]),Math.max(anchor[0],p[0]),Math.max(anchor[1],p[1])].map(v => Math.round(v*100)/100);anchor = null;fields.forEach((f,i) => {f.value = draft[i];});message('Draft box ready. Save ball box to keep it.');}
    draw();magnify(...p);
  });
  canvas.addEventListener('pointermove', e => {if (image) magnify(...point(e));});
  fields.forEach(f => f.addEventListener('input', () => {draft = fields.every(f => f.value !== '') ? fields.map(f => Number(f.value)) : null;anchor = null;draw();if (validBox(draft)) magnify(draft[0],draft[1]);message('Draft coordinates changed. Save ball box to keep them.');}));
  byId('label-download').addEventListener('click', () => {
    const review = {schema_version:1, recording_id:manifest.recording_id, source_sha256:manifest.source_sha256,
      source_dimensions:manifest.source_dimensions, coordinate_space:'source_image_xyxy', annotation_method:'Manual visible-extent review; single reviewer, not independently verified.', labels:Array.from(labels.values()).sort((a,b) => a.frame_index-b.frame_index)};
    const url = URL.createObjectURL(new Blob([JSON.stringify(review,null,2)+'\n'], {type:'application/json'}));
    const link = document.createElement('a');link.href = url;link.download = `${manifest.recording_id}-labels.json`;link.click();setTimeout(() => URL.revokeObjectURL(url),1000);
    message('Labels downloaded. Use the local export tool to prepare reviewed images and YOLO text labels.');
  });
  byId('label-import').addEventListener('change', async event => {
    const file = event.target.files[0], version = generation;
    if (!manifest || !file) return;
    try {
      if (file.size > 1024*1024) throw Error('Labels JSON must be at most 1 MiB.');
      const review = JSON.parse(await file.text());
      if (version !== generation) return;
      if (review.schema_version !== 1 || review.coordinate_space !== 'source_image_xyxy' || review.source_sha256 !== manifest.source_sha256 || review.recording_id !== manifest.recording_id || JSON.stringify(review.source_dimensions) !== JSON.stringify(manifest.source_dimensions) || !Array.isArray(review.labels) || review.labels.length > manifest.frames.length) throw Error('Labels do not match this review bundle.');
      const loaded = new Map();
      for (const row of review.labels) {
        const f = manifest.frames.find(f => f.frame_index === row.frame_index);
        if (!f || loaded.has(row.frame_index) || row.image_sha256 !== f.image_sha256 || !Object.hasOwn(states, row.visibility) || (row.visibility === 'visible' ? !validBox(row.bbox) : row.bbox !== null)) throw Error('Invalid source frame, visibility or box in labels.');
        loaded.set(row.frame_index, {frame_index:row.frame_index,image_sha256:row.image_sha256,visibility:row.visibility,bbox:row.bbox});
      }
      labels = loaded;await openFrame(current);message('Saved review resumed. Download again after making changes.');
    } catch (error) {if (version === generation) message(error.message);}
    event.target.value = '';
  });
})();
