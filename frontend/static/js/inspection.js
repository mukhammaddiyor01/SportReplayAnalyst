// Inspection owns its worker handle; table calibration remains frame-local.
(() => {
  const trackButton = document.querySelector("#track-start");
  const startButton = document.querySelector("#inspect-start");
  const cancelButton = document.querySelector("#inspect-cancel");
  const deleteButton = document.querySelector("#inspect-delete");
  const refreshButton = document.querySelector("#inspect-refresh");
  const statusText = document.querySelector("#inspection-status");
  const resultList = document.querySelector("#inspection-result");
  const workflowHint = document.querySelector("#workflow-hint");
  const workflowMode = document.querySelector("#workspace-mode");
  const terminalStates = new Set(["completed", "failed", "cancelled"]);
  let file = null;
  let job = null;
  let generation = 0;
  let reserving = false;
  let trackingRegion = null;

  function setMessage(message) {
    statusText.textContent = message;
  }

  function updateControls() {
    const terminal = job && terminalStates.has(job.status);
    startButton.disabled = !file || reserving || job !== null;
    trackButton.disabled = startButton.disabled || !trackingRegion;
    cancelButton.hidden = !job || terminal;
    cancelButton.disabled = job?.status === "cancelling";
    deleteButton.hidden = !terminal;
    let mode = "Choose a video";
    let hint = "Choose a video to get started.";
    if (file) {
      mode = "Prepare the table";
      hint = "Mark four corners and check calibration to enable tracking.";
    }
    if (trackingRegion) {
      mode = "Ready to track";
      hint = "The search window is ready. Start ball tracking below.";
    }
    if (reserving || (job && !terminal)) {
      mode = "Analyzing locally";
      hint = "You can keep reviewing the video while analysis runs.";
    } else if (terminal) {
      mode = job.status === "completed" ? "Ready to review" : "Analysis stopped";
      hint = job.status === "completed" ? (job.trackingPublished ?
        "Review tracking gaps below the video." : "Open Inspection details to see the results.") :
        "Clear the current result before running another analysis.";
    }
    workflowMode.textContent = mode;
    workflowHint.textContent = hint;
  }

  async function jobRequest(handle, suffix = "", method = "GET", keepalive = false) {
    const response = await fetch(`/api/inspections/${handle.id}${suffix}`, {
      method,
      headers: {Authorization: `Bearer ${handle.token}`},
      keepalive,
    });
    if (response.status === 204) return null;
    const body = await response.json();
    if (!response.ok) {
      const error = new Error(body.detail || "The local inspection request failed.");
      error.status = response.status;
      throw error;
    }
    return body;
  }

  function showResult(result) {
    resultList.replaceChildren();
    const fields = [
      ["Decoded frames", String(result.decoded_frames)],
      ["Source size", `${result.source_dimensions[0]} × ${result.source_dimensions[1]} px`],
      ["Last frame time", `${result.last_timestamp_seconds.toFixed(3)} s`],
      ["FPS fallback frames", String(result.fps_fallback_frames)],
    ];
    if (result.camera_motion) {
      const camera = result.camera_motion;
      const labels = {movement_detected: "Movement detected", no_movement_detected: "Review alignment", uncertain: "Inconclusive"};
      fields.push(["Camera check", labels[camera.status] || "Inconclusive"]);
      fields.push(["Calibration reuse", camera.calibration_reuse === "blocked" ? "Frame-local only" : "Review required"]);
    }
    if (result.tracking) {
      fields.push(["Associated observations", String(result.tracking.status_counts.observed || 0)]);
      fields.push(["Unobserved predictions", String(result.tracking.status_counts.predicted || 0)]);
    }
    for (const [label, value] of fields) {
      const item = document.createElement("div");
      const term = document.createElement("dt");
      const description = document.createElement("dd");
      term.textContent = label;
      description.textContent = value;
      item.append(term, description);
      resultList.append(item);
    }
    resultList.hidden = false;
  }

  function renderState(handle, state) {
    if (job !== handle) return;
    handle.status = state.status;
    refreshButton.hidden = true;
    const cleanupNote = state.cleanup_pending ? " Temporary file cleanup is pending; the server will retry." : "";
    if (state.status === "completed") {
      const cameraNote = state.result.camera_motion ? ` ${state.result.camera_motion.message}` : "";
      let trackingNote = " Ball tracking was not run.";
      if (state.result.tracking) {
        trackingNote = state.result.tracking.status_counts.observed > 0 ?
          " Experimental 2D associations are ready. Contacts and rallies were not evaluated." :
          " No observations were confirmed. Review the unobserved intervals. Contacts and rallies were not evaluated.";
      }
      setMessage(`${state.decoded_frames} frames inspected.${cameraNote}${trackingNote}${cleanupNote}`);
      showResult(state.result);
      if (state.result.tracking && !handle.trackingPublished) {
        handle.trackingPublished = true;
        document.dispatchEvent(new CustomEvent("replay:tracking-ready", {detail: {result: state.result}}));
      }
    } else if (state.status === "failed") {
      setMessage(`Inspection failed: ${state.error}${cleanupNote}`);
    } else if (state.status === "cancelled") {
      setMessage(`Inspection cancelled. The temporary video copy was removed.${cleanupNote}`);
      if (state.cleanup_pending) setMessage(`Inspection cancelled.${cleanupNote}`);
    } else if (state.status === "cancelling") {
      setMessage("Stopping inspection. Waiting for the worker before removing its files…");
    } else if (state.status === "receiving") {
      setMessage("Copying this video to the local server…");
    } else {
      const timestamp = state.timestamp_seconds === null ? "" : ` Source time ${state.timestamp_seconds.toFixed(3)} s.`;
      setMessage(`Reading video: ${state.decoded_frames} frames decoded.${timestamp}`);
    }
    updateControls();
  }

  async function poll(handle) {
    if (job !== handle || handle.polling) return;
    handle.polling = true;
    clearTimeout(handle.timer);
    try {
      const state = await jobRequest(handle);
      if (job !== handle) return;
      renderState(handle, state);
      if (!terminalStates.has(state.status)) {
        handle.timer = setTimeout(() => poll(handle), 250);
      }
    } catch (error) {
      if (job !== handle) return;
      if (error.status === 404) {
        job = null;
        document.dispatchEvent(new CustomEvent("replay:tracking-cleared"));
        resultList.hidden = true;
        setMessage("This inspection expired or the server restarted. You can inspect the clip again.");
        updateControls();
      } else {
        setMessage("Could not read inspection status. Retry status or cancel the inspection.");
        refreshButton.hidden = false;
      }
    } finally {
      handle.polling = false;
    }
  }

  async function release(handle) {
    clearTimeout(handle.timer);
    handle.upload?.abort();
    try {
      let state = await jobRequest(handle, "/cancel", "POST", true);
      for (let attempt = 0; attempt < 20; attempt += 1) {
        if (terminalStates.has(state.status)) {
          await jobRequest(handle, "", "DELETE", true);
          return;
        }
        await new Promise(resolve => setTimeout(resolve, 250));
        state = await jobRequest(handle, "", "GET", true);
      }
      // The server still finalizes cancellation if the tab closes during polling.
    } catch {
      // Unreachable servers still enforce their reservation/retention deadlines.
    }
  }

  document.addEventListener("replay:table-checked", event => {
    trackingRegion = [...event.detail.region];
    updateControls();
  });
  document.addEventListener("replay:table-cleared", () => {
    trackingRegion = null;
    updateControls();
  });

  document.addEventListener("replay:clip-ready", event => {
    file = event.detail.file;
    setMessage("Ready to inspect this clip.");
    updateControls();
  });

  document.addEventListener("replay:clip-cleared", () => {
    generation += 1;
    file = null;
    trackingRegion = null;
    reserving = false;
    const previous = job;
    job = null;
    if (previous) release(previous);
    resultList.replaceChildren();
    resultList.hidden = true;
    refreshButton.hidden = true;
    setMessage("Choose a video before inspecting.");
    updateControls();
  });

  async function startAnalysis(mode) {
    if (!file || job || reserving || (mode === "track" && !trackingRegion)) return;
    const currentGeneration = generation;
    const selectedFile = file;
    const options = mode === "track" ? {mode, search_region: [...trackingRegion]} : {mode};
    let handle = null;
    reserving = true;
    updateControls();
    setMessage("Preparing local inspection…");
    try {
      const reservation = await fetch("/api/inspections", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(options),
      });
      const body = await reservation.json();
      if (!reservation.ok) throw new Error(body.detail || "Could not start local inspection.");
      handle = {...body, upload: new AbortController(), timer: null};
      if (currentGeneration !== generation) {
        await release(handle);
        return;
      }
      job = handle;
      updateControls();
      setMessage("Copying this video to the local server…");
      const response = await fetch(`/api/inspections/${handle.id}/video`, {
        method: "PUT",
        headers: {Authorization: `Bearer ${handle.token}`, "Content-Type": selectedFile.type || "application/octet-stream"},
        body: selectedFile,
        signal: handle.upload.signal,
      });
      const state = await response.json();
      if (currentGeneration !== generation || job !== handle) return;
      if (!response.ok) {
        setMessage(state.detail || "Video transfer failed.");
        await poll(handle);
        return;
      }
      renderState(handle, state);
      await poll(handle);
    } catch (error) {
      if (currentGeneration !== generation) return;
      if (handle && job === handle) {
        if (error.name !== "AbortError") setMessage("Video transfer was interrupted. Checking cleanup…");
        await poll(handle);
      } else {
        setMessage(error.message || "The local server could not be reached.");
      }
    } finally {
      if (currentGeneration === generation) {
        reserving = false;
        updateControls();
      }
    }
  }

  startButton.addEventListener("click", () => startAnalysis("inspect"));
  trackButton.addEventListener("click", () => startAnalysis("track"));

  cancelButton.addEventListener("click", async () => {
    const current = job;
    if (!current) return;
    current.status = "cancelling";
    clearTimeout(current.timer);
    current.upload?.abort();
    updateControls();
    setMessage("Requesting cancellation…");
    try {
      const state = await jobRequest(current, "/cancel", "POST");
      renderState(current, state);
      await poll(current);
    } catch {
      if (job === current) {
        setMessage("Cancellation could not be confirmed. Retry status.");
        refreshButton.hidden = false;
      }
    }
  });

  deleteButton.addEventListener("click", async () => {
    const current = job;
    if (!current) return;
    deleteButton.disabled = true;
    try {
      await jobRequest(current, "", "DELETE");
      if (job !== current) return;
      clearTimeout(current.timer);
      job = null;
      document.dispatchEvent(new CustomEvent("replay:tracking-cleared"));
      resultList.replaceChildren();
      resultList.hidden = true;
      setMessage("The local video copy and inspection result were removed.");
      updateControls();
    } catch (error) {
      if (job === current) setMessage(error.message);
    } finally {
      deleteButton.disabled = false;
    }
  });

  refreshButton.addEventListener("click", () => {
    if (job) poll(job);
  });
})();
