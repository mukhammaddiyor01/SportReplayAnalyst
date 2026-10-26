// Source-frame review navigation. Gaps describe evidence, not sports events.
(() => {
  const video = document.querySelector('#video');
  const panel = document.querySelector('#tracking-review');
  const count = document.querySelector('#review-count');
  const explanation = document.querySelector('#review-explanation');
  const list = document.querySelector('#review-gaps');
  const position = document.querySelector('#review-position');
  let selectedGap = null;
  const labels = {
    between_observations: 'Between observations',
    clip_start: 'Before first observation',
    clip_end: 'After last observation',
    entire_clip: 'No observations in this clip',
  };

  function clear() {
    selectedGap = null;
    panel.hidden = true;
    list.replaceChildren();
    count.textContent = '';
    position.textContent = '';
  }

  function time(seconds) {
    const minutes = Math.floor(seconds / 60);
    return `${String(minutes).padStart(2, '0')}:${(seconds % 60).toFixed(3).padStart(6, '0')}`;
  }

  function seek(seconds, gap, button) {
    video.pause();
    selectedGap = gap;
    video.currentTime = seconds;
    list.querySelectorAll('[aria-current]').forEach(item => item.removeAttribute('aria-current'));
    button.setAttribute('aria-current', 'true');
    position.textContent = `Reviewing frames ${gap.start_frame}–${gap.end_frame}.`;
  }

  document.addEventListener('replay:tracking-ready', event => {
    clear();
    const result = event.detail.result;
    panel.hidden = false;
    if (result.fps_fallback_frames > 0 || result.source_dimensions[0] !== video.videoWidth ||
        result.source_dimensions[1] !== video.videoHeight) {
      explanation.textContent = 'Review navigation unavailable: source timing or dimensions differ from playback.';
      return;
    }
    const gaps = result.tracking.review_gaps;
    if (!Array.isArray(gaps)) {
      explanation.textContent = 'Run tracking again to prepare gap review.';
      return;
    }
    count.textContent = `${gaps.length} ${gaps.length === 1 ? 'interval' : 'intervals'}`;
    explanation.textContent = gaps.length ?
      'These frames have no associated observation. Review the video to check what happened.' :
      'Every decoded frame has an associated candidate. This does not verify ball identity.';
    for (const gap of gaps) {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'review-gap';
      const timing = document.createElement('span');
      timing.className = 'review-gap-time';
      timing.textContent = gap.frame_count === 1 ? time(gap.start_seconds) :
        `${time(gap.start_seconds)} – ${time(gap.end_seconds)}`;
      const detail = document.createElement('span');
      detail.textContent = `${labels[gap.position]} · ${gap.frame_count} ${gap.frame_count === 1 ? 'frame' : 'frames'}`;
      const action = document.createElement('span');
      action.className = 'review-gap-action';
      action.textContent = 'Review';
      button.append(timing, detail, action);
      button.addEventListener('click', () => seek(gap.start_seconds, gap, button));
      item.append(button);
      list.append(item);
    }
  });
  function updateSelection() {
    if (!selectedGap) return;
    const limit = selectedGap.resume_seconds ?? video.duration;
    if (video.currentTime + .00001 >= selectedGap.start_seconds && video.currentTime < limit) return;
    list.querySelectorAll('[aria-current]').forEach(item => item.removeAttribute('aria-current'));
    selectedGap = null;
    position.textContent = '';
  }
  video.addEventListener('seeked', updateSelection);
  video.addEventListener('timeupdate', updateSelection);
  document.addEventListener('replay:clip-ready', clear);
  document.addEventListener('replay:clip-cleared', clear);
  document.addEventListener('replay:tracking-cleared', clear);
})();
