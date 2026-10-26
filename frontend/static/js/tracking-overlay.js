// Only associated observations are drawn. Missing/tentative/predicted points are not.
(() => {
  const video = document.querySelector("#video");
  const canvas = document.querySelector("#tracking-overlay");
  const context = canvas.getContext("2d");
  const controls = document.querySelector("#tracking-controls");
  const toggle = document.querySelector("#show-tracking");
  const stepBack = document.querySelector("#step-back");
  const stepForward = document.querySelector("#step-forward");
  const playback = document.querySelector(".playback");
  const status = document.querySelector("#tracking-status");
  let records = [];
  let frameCallback = null;

  function clear() {
    records = [];
    stepBack.disabled = true;
    stepForward.disabled = true;
    context.clearRect(0, 0, canvas.width, canvas.height);
    controls.hidden = true;
    status.textContent = "No tracking result.";
  }

  function latestFrame(time) {
    let low = 0;
    let high = records.length - 1;
    let found = -1;
    while (low <= high) {
      const middle = Math.floor((low + high) / 2);
      if (records[middle].timestamp_seconds <= time + .00001) {
        found = middle;
        low = middle + 1;
      } else high = middle - 1;
    }
    return found;
  }

  function draw(time) {
    context.clearRect(0, 0, canvas.width, canvas.height);
    if (!records.length) return;
    const index = latestFrame(time);
    stepBack.disabled = index <= 0;
    stepForward.disabled = index >= records.length - 1;
    if (index < 0) return;
    const current = records[index];
    if (!toggle.checked) {
      status.textContent = `Frame ${current.frame_index}: trail hidden`;
      return;
    }
    status.textContent = current.status === "observed" ?
      `Frame ${current.frame_index}: associated candidate` :
      `Frame ${current.frame_index}: no observation (${current.status})`;
    if (current.track_id === null) return;
    let start = index;
    while (start > 0 && records[start - 1].timestamp_seconds >= time - .6) start -= 1;
    context.strokeStyle = "#46c7cf";
    context.lineWidth = Math.max(2, canvas.width / 384);
    context.lineJoin = "round";
    context.beginPath();
    let previous = null;
    for (let position = start; position <= index; position += 1) {
      const row = records[position];
      if (row.status !== "observed" || row.track_id !== current.track_id || !row.observation) {
        previous = null;
        continue;
      }
      const [x, y] = row.observation;
      if (!previous || row.break_before || row.frame_index !== previous.frame_index + 1) context.moveTo(x, y);
      else context.lineTo(x, y);
      previous = row;
    }
    context.stroke();
    if (current.status === "observed" && current.observation) {
      const [x, y] = current.observation;
      context.beginPath();
      context.arc(x, y, 7, 0, Math.PI * 2);
      context.strokeStyle = "#fff";
      context.lineWidth = 2;
      context.stroke();
      context.beginPath();
      context.arc(x, y, 4, 0, Math.PI * 2);
      context.fillStyle = "#46c7cf";
      context.fill();
    }
  }

  function step(direction) {
    if (!records.length) return;
    const current = latestFrame(video.currentTime);
    const target = Math.max(0, Math.min(records.length - 1, current + direction));
    video.pause();
    const start = records[target].timestamp_seconds;
    const end = records[target + 1]?.timestamp_seconds ?? video.duration;
    // Seek inside the source frame interval; decoder rounding at its boundary can show the prior frame.
    video.currentTime = Number.isFinite(end) && end > start ? start + (end - start) / 2 : start;
  }

  stepBack.addEventListener("click", () => step(-1));
  stepForward.addEventListener("click", () => step(1));
  playback.addEventListener("keydown", event => {
    if (event.target.closest("input") || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (!records.length || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault();
    step(event.key === "ArrowLeft" ? -1 : 1);
  });

  function requestFrame() {
    if (!video.requestVideoFrameCallback) return;
    frameCallback = video.requestVideoFrameCallback((_, metadata) => {
      frameCallback = null;
      if (!video.seeking) draw(metadata.mediaTime);
      requestFrame();
    });
  }

  document.addEventListener("replay:clip-ready", () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    if (frameCallback === null) requestFrame();
  });
  document.addEventListener("replay:clip-cleared", () => {
    if (frameCallback !== null && video.cancelVideoFrameCallback) video.cancelVideoFrameCallback(frameCallback);
    frameCallback = null;
    clear();
  });
  document.addEventListener("replay:tracking-cleared", clear);
  document.addEventListener("replay:tracking-ready", event => {
    clear();
    controls.hidden = false;
    const result = event.detail.result;
    if (result.fps_fallback_frames > 0) {
      status.textContent = "Overlay unavailable: source timestamps were estimated.";
      return;
    }
    if (result.source_dimensions[0] !== video.videoWidth || result.source_dimensions[1] !== video.videoHeight) {
      status.textContent = "Overlay unavailable: source dimensions differ from playback.";
      return;
    }
    records = result.tracking.frames;
    toggle.checked = true;
    draw(video.currentTime);
  });
  toggle.addEventListener("change", () => draw(video.currentTime));
  video.addEventListener("seeking", () => context.clearRect(0, 0, canvas.width, canvas.height));
  video.addEventListener("seeked", () => draw(video.currentTime));
  video.addEventListener("timeupdate", () => {
    if (!video.seeking && (video.paused || !video.requestVideoFrameCallback)) draw(video.currentTime);
  });
})();
