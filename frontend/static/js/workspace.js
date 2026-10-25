const video = document.querySelector("#video");
const canvas = document.querySelector("#corners");
const context = canvas.getContext("2d");
const input = document.querySelector("#clip");
const status = document.querySelector("#status");
const summary = document.querySelector("#clip-summary");
const cornerList = document.querySelector("#corner-list");
const confirmButton = document.querySelector("#confirm");
const undoButton = document.querySelector("#undo");
const removeButton = document.querySelector("#remove");
const limits = input.dataset;
let objectUrl = null;
let points = [];
let revision = 0;
let referenceTime = null;
let ready = false;
let selectedClipFile = null;

function setStatus(message) { status.textContent = message; }

function resetCorners(message = "Pause on a clear frame and mark the table corners.") {
  revision += 1;
  points = [];
  referenceTime = null;
  renderCorners();
  if (ready) setStatus(message);
}

function renderCorners() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  cornerList.replaceChildren();
  document.querySelector("#corner-count").textContent = `${points.length} / 4`;
  document.querySelector("#corner-empty").hidden = points.length > 0;
  points.forEach(([x, y], index) => {
    const row = document.createElement("li");
    row.textContent = `Corner ${index + 1}: ${x.toFixed(1)}, ${y.toFixed(1)} px`;
    cornerList.append(row);
  });
  if (points.length) {
    context.strokeStyle = "#ffb469";
    context.lineWidth = Math.max(2, canvas.width / 350);
    context.beginPath();
    points.forEach(([x, y], index) => index ? context.lineTo(x, y) : context.moveTo(x, y));
    if (points.length === 4) context.closePath();
    context.stroke();
    points.forEach(([x, y], index) => {
      context.fillStyle = "#183347";
      context.beginPath(); context.arc(x, y, 12, 0, Math.PI * 2); context.fill();
      context.strokeStyle = "#ffb469"; context.stroke();
      context.fillStyle = "#fff"; context.textAlign = "center";
      context.font = "bold 14px sans-serif"; context.fillText(String(index + 1), x, y + 5);
    });
  }
  confirmButton.disabled = points.length !== 4;
  undoButton.disabled = points.length === 0;
}

function removeClip(message = "Choose a local video to begin.", clearInput = true) {
  ready = false;
  selectedClipFile = null;
  document.dispatchEvent(new CustomEvent("replay:clip-cleared"));
  video.pause();
  video.removeAttribute("src");
  video.load();
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = null;
  if (clearInput) input.value = "";
  resetCorners();
  document.querySelector("#empty").hidden = false;
  document.querySelector("#media").hidden = true;
  summary.textContent = "No video selected";
  removeButton.disabled = true;
  document.querySelector("#geometry").textContent = "";
  document.querySelector("#time").textContent = "0.000 s";
  document.querySelector("#seek").value = "0";
  setStatus(message);
}

input.addEventListener("change", () => {
  const file = input.files[0];
  if (!file) return;
  removeClip(undefined, false);
  if (!file.size || file.size > Number(limits.maxBytes)) {
    setStatus("Choose a nonempty video of at most 100 MiB."); return;
  }
  selectedClipFile = file;
  objectUrl = URL.createObjectURL(file);
  summary.textContent = file.name;
  video.src = objectUrl;
  removeButton.disabled = false;
  setStatus("Reading video metadata…");
});

video.addEventListener("loadedmetadata", () => {
  if (!objectUrl) return;
  if (!Number.isFinite(video.duration) || video.duration <= 0 ||
      video.duration > Number(limits.maxDuration) || !video.videoWidth || !video.videoHeight ||
      video.videoWidth > Number(limits.maxWidth) || video.videoHeight > Number(limits.maxHeight)) {
    removeClip("Use a video up to 60 seconds and 1920 × 1080."); return;
  }
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ready = true;
  document.dispatchEvent(new CustomEvent("replay:clip-ready", {detail: {file: selectedClipFile}}));
  document.querySelector("#empty").hidden = true;
  document.querySelector("#media").hidden = false;
  document.querySelector("#geometry").textContent =
    `${video.videoWidth} × ${video.videoHeight} px / ${video.duration.toFixed(3)} s`;
  setStatus("Pause on a clear frame. Select four corners clockwise, starting at the upper-left.");
});
video.addEventListener("error", () => {
  if (objectUrl) removeClip("This video could not be played. Choose a supported MP4 or WebM clip.");
});
video.addEventListener("play", () => {
  if (points.length) resetCorners("Playback cleared the frame calibration. Pause to mark corners again.");
});
video.addEventListener("seeking", () => {
  if (points.length) resetCorners("The frame changed. Mark the table corners again.");
});
video.addEventListener("timeupdate", () => {
  if (referenceTime !== null && Math.abs(video.currentTime - referenceTime) > .001) {
    resetCorners("The frame changed. Mark the table corners again.");
  }
});

function addCorner(x, y) {
  if (!ready || !video.paused || video.seeking) {
    setStatus("Pause the video and wait for seeking to finish before marking corners."); return;
  }
  if (points.length === 4) { setStatus("Undo a corner or check the four selected corners."); return; }
  revision += 1;
  referenceTime = video.currentTime;
  points.push([x, y]);
  renderCorners();
  setStatus(points.length === 4 ? "Four corners selected. Check calibration." :
    `Corner ${points.length} selected. Continue clockwise.`);
}

canvas.addEventListener("click", event => {
  const bounds = canvas.getBoundingClientRect();
  const x = (event.clientX - bounds.left) * canvas.width / bounds.width;
  const y = (event.clientY - bounds.top) * canvas.height / bounds.height;
  addCorner(Math.min(canvas.width - 1, Math.max(0, x)), Math.min(canvas.height - 1, Math.max(0, y)));
});

// Numeric source coordinates provide a keyboard-accessible alternative to the canvas.
document.querySelector("#coordinate-form").addEventListener("submit", event => {
  event.preventDefault();
  const x = Number(document.querySelector("#corner-x").value);
  const y = Number(document.querySelector("#corner-y").value);
  if (!Number.isFinite(x) || !Number.isFinite(y) || x < 0 || y < 0 ||
      x >= canvas.width || y >= canvas.height) {
    setStatus("Enter coordinates inside the source frame."); return;
  }
  addCorner(x, y);
});
undoButton.addEventListener("click", () => {
  revision += 1; points.pop(); renderCorners(); setStatus("Corner removed. Continue clockwise.");
});
removeButton.addEventListener("click", () => removeClip());
confirmButton.addEventListener("click", async () => {
  const submittedRevision = revision;
  confirmButton.disabled = true;
  setStatus("Checking table geometry…");
  try {
    const response = await fetch("/api/calibration", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({width: canvas.width, height: canvas.height, corners: points}),
    });
    const result = await response.json();
    if (submittedRevision !== revision) return;
    if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Check the four corner coordinates.");
    setStatus("Table geometry checked for this frame. Camera stability and ball tracking have not been evaluated.");
  } catch (error) {
    if (submittedRevision === revision) setStatus(error.message || "Calibration could not be checked. Try again.");
  } finally {
    if (submittedRevision === revision) confirmButton.disabled = points.length !== 4;
  }
});
window.addEventListener("pagehide", () => removeClip());
document.addEventListener("visibilitychange", () => { if (document.hidden) video.pause(); });

const playButton = document.querySelector("#toggle-play");
const seek = document.querySelector("#seek");
playButton.addEventListener("click", async () => {
  if (video.paused) {
    try { await video.play(); } catch { setStatus("Playback could not start. Select the video again."); }
  } else video.pause();
});
video.addEventListener("play", () => { playButton.textContent = "Pause"; });
video.addEventListener("pause", () => { playButton.textContent = "Play"; });
video.addEventListener("loadedmetadata", () => { seek.max = String(video.duration || 1); seek.value = "0"; });
video.addEventListener("timeupdate", () => {
  seek.value = String(video.currentTime);
  document.querySelector("#time").textContent = `${video.currentTime.toFixed(3)} s`;
});
seek.addEventListener("input", () => { video.pause(); video.currentTime = Number(seek.value); });
