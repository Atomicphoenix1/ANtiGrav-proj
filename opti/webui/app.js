let state = {
  opMode: 'Whisper + Gemini',
  scope: 'Singular',
  splitMode: '10 min',
  pipelineRunning: false,
  eventSource: null,
  lastLog: '',
  settings: {}
};

const $ = (id) => document.getElementById(id);
const qs = (sel, ctx) => (ctx || document).querySelector(sel);
const qsa = (sel, ctx) => (ctx || document).querySelectorAll(sel);

function getTheme() {
  return localStorage.getItem('pipeline-theme') || 'alchemist';
}

function setTheme(theme) {
  localStorage.setItem('pipeline-theme', theme);
  document.getElementById('theme-css').disabled = theme !== 'alchemist';
  document.getElementById('theme-biopunk').disabled = theme !== 'biopunk';
  document.getElementById('theme-retroluxe').disabled = theme !== 'retroluxe';
}

function domReady() {
  initStarfield();
  setTheme(getTheme());
  loadSettings();
  bindEvents();
  updateVisibility();
  lucide.createIcons();
}

document.addEventListener('DOMContentLoaded', domReady);

async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    state.settings = await res.json();
    applySettings();
  } catch (e) {
    console.warn('Could not load settings', e);
  }
}

function applySettings() {
  const s = state.settings;
  if (s.gemini_api_key) {
    $('api-key-input').value = s.gemini_api_key;
    $('settings-api-key').value = s.gemini_api_key;
  }
  if (s.n8n_webhook_url) {
    $('n8n-url-input').value = s.n8n_webhook_url;
    $('settings-n8n-url').value = s.n8n_webhook_url;
  }
  if (s.n8n_log_bridge_enabled !== undefined) {
    $('n8n-toggle').checked = s.n8n_log_bridge_enabled;
  }
  if (s.last_device) $('device-select').value = s.last_device;
  if (s.last_model) $('model-select').value = s.last_model;
  if (s.last_split_mode) {
    setPill('split-mode-group', s.last_split_mode);
    state.splitMode = s.last_split_mode;
  }
  if (s.last_scope) {
    setPill('scope-group', s.last_scope);
    state.scope = s.last_scope;
  }
  if (s.last_operation) {
    setPill('op-mode-group', s.last_operation);
    state.opMode = s.last_operation;
  }
  if (s.theme) {
    $('settings-theme').value = s.theme;
    setTheme(s.theme);
  } else {
    $('settings-theme').value = getTheme();
  }
}

function setPill(groupId, value) {
  const pills = qsa('.radio-pill', $(groupId));
  pills.forEach(p => {
    p.classList.toggle('active', p.dataset.value === value);
  });
}

function bindEvents() {
  bindRadioGroups();
  bindFileInputs();
  bindButtons();
  bindSettings();
  bindTerminal();
}

function bindRadioGroups() {
  bindPills('op-mode-group', (val) => {
    state.opMode = val;
    updateVisibility();
  });
  bindPills('scope-group', (val) => {
    state.scope = val;
    updateVisibility();
  });
  bindPills('split-mode-group', (val) => {
    state.splitMode = val;
    $('custom-seconds-group').classList.toggle('hidden', val !== 'Custom');
    updateVisibility();
  });
}

function bindPills(groupId, onChange) {
  const pills = qsa('.radio-pill', $(groupId));
  pills.forEach(p => {
    p.addEventListener('click', () => {
      setPill(groupId, p.dataset.value);
      onChange(p.dataset.value);
    });
  });
}

function bindFileInputs() {
  bindFileZone('single-audio-input', 'single-audio-zone', 'single-audio-label');
  bindFileZone('multi-audio-input', 'multi-audio-zone', 'multi-audio-label');
  bindFileZone('single-txt-input', 'single-txt-zone', 'single-txt-label');
  bindFileZone('multi-txt-input', 'multi-txt-zone', 'multi-txt-label');
  bindFileZone('srt-txt-input', 'srt-txt-zone');
  bindFileZone('srt-json-input', 'srt-json-zone');
}

function bindFileZone(inputId, zoneId, labelId) {
  const input = $(inputId);
  const zone = $(zoneId);
  if (!input || !zone) return;
  input.addEventListener('change', () => {
    const files = input.files;
    if (files && files.length > 0) {
      zone.classList.add('has-file');
      if (labelId) {
        const names = Array.from(files).map(f => f.name).join(', ');
        $(labelId).textContent = names.length > 60 ? names.substring(0, 57) + '...' : names;
      }
    } else {
      zone.classList.remove('has-file');
      if (labelId) $(labelId).textContent = zone.dataset.placeholder || 'Click to upload';
    }
  });
}

function bindButtons() {
  $('run-btn').addEventListener('click', runPipeline);
  $('cancel-btn').addEventListener('click', cancelPipeline);
  $('browse-btn').addEventListener('click', browseFolder);
}

function bindSettings() {
  $('settings-btn').addEventListener('click', () => {
    $('settings-api-key').value = $('api-key-input').value;
    $('settings-n8n-url').value = $('n8n-url-input').value;
    $('settings-modal').classList.add('active');
  });
  $('close-settings-btn').addEventListener('click', closeSettings);
  $('settings-cancel-btn').addEventListener('click', closeSettings);
  $('settings-save-btn').addEventListener('click', saveSettings);
  $('settings-modal').addEventListener('click', (e) => {
    if (e.target === $('settings-modal')) closeSettings();
  });
  $('n8n-toggle').addEventListener('change', () => {
    updateN8nToggle();
  });
  $('settings-theme').addEventListener('change', (e) => {
    setTheme(e.target.value);
  });
}

function closeSettings() {
  $('settings-modal').classList.remove('active');
}

async function saveSettings() {
  const apiKey = $('settings-api-key').value.trim();
  const n8nUrl = $('settings-n8n-url').value.trim();
  const body = {};
  if (apiKey) body.gemini_api_key = apiKey;
  else body.gemini_api_key = '';
  body.n8n_webhook_url = n8nUrl;
  body.n8n_log_bridge_enabled = $('n8n-toggle').checked;
  body.last_model = $('model-select').value;
  body.last_device = $('device-select').value;
  body.last_split_mode = state.splitMode;
  body.last_scope = state.scope;
  body.last_operation = state.opMode;
  body.theme = $('settings-theme').value;

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    state.settings = data;
    applySettings();
    appendLog('✦ Settings saved successfully.');
    closeSettings();
  } catch (e) {
    appendLog('✖ Failed to save settings: ' + e.message);
  }
}

async function updateN8nToggle() {
  const enabled = $('n8n-toggle').checked;
  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ n8n_log_bridge_enabled: enabled })
    });
  } catch (e) {
    console.warn('Failed to update n8n toggle', e);
  }
}

function bindTerminal() {
  $('clear-terminal-btn').addEventListener('click', () => {
    $('terminal-output').innerHTML = '<span class="dim">✦ Terminal cleared.</span>';
    state.lastLog = '';
  });
  $('copy-logs-btn').addEventListener('click', () => {
    const text = $('terminal-output').textContent;
    navigator.clipboard.writeText(text).catch(() => {});
  });
}

function updateVisibility() {
  const op = state.opMode;
  const scope = state.scope;
  const isAudioSing = ['Whisper Only', 'MP3 Splitter', 'Whisper + Gemini'].includes(op) && scope === 'Singular';
  const isAudioBulk = ['Whisper Only', 'MP3 Splitter'].includes(op) && scope === 'Bulk';
  const isGeminiSing = op === 'Gemini Only' && scope === 'Singular';
  const isGeminiBulk = op === 'Gemini Only' && scope === 'Bulk';
  const isFolderBulk = ['MP3 Splitter', 'Whisper + Gemini'].includes(op) && scope === 'Bulk';
  const isSplitterOp = ['MP3 Splitter', 'Whisper + Gemini'].includes(op);
  const isSrtAlign = op === 'SRT Alignment';

  $('single-audio-zone').classList.toggle('hidden', !isAudioSing);
  $('multi-audio-zone').classList.toggle('hidden', !isAudioBulk);
  $('text-inputs').classList.toggle('hidden', !(isGeminiSing || isGeminiBulk));
  $('single-txt-zone').classList.toggle('hidden', !isGeminiSing);
  $('multi-txt-zone').classList.toggle('hidden', !isGeminiBulk);
  $('srt-inputs').classList.toggle('hidden', !isSrtAlign);
  $('splitter-controls').classList.toggle('hidden', !isSplitterOp);
  $('bulk-folder-row').classList.toggle('hidden', !isFolderBulk);
  if (isGeminiSing || isGeminiBulk) {
    $('splitter-controls').classList.add('hidden');
  }
}

function appendLog(msg) {
  const term = $('terminal-output');
  const lines = term.innerHTML.split('\n');
  if (lines.length > 200) {
    lines.splice(0, 50);
  }
  if (term.innerHTML === '<span class="dim">✦ Pipeline Forge ready. Configure and run.</span>' ||
      term.innerHTML === '<span class="dim">✦ Terminal cleared.</span>') {
    term.innerHTML = '';
  }
  const escaped = msg.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  term.innerHTML += escaped + '\n';
  term.scrollTop = term.scrollHeight;
}

function setTerminalStatus(status, text) {
  const dot = $('terminal-dot');
  dot.className = 'terminal-dot ' + status;
  $('terminal-status-text').textContent = text;
}

function setStatusBar(text, isOk) {
  if (isOk) {
    $('status-left').innerHTML = '<i data-lucide="check-circle-2" style="width:12px;height:12px;"></i> ' + text;
  } else {
    $('status-left').innerHTML = text;
  }
  lucide.createIcons();
}

async function browseFolder() {
  try {
    const res = await fetch('/api/browse-folder', { method: 'POST' });
    const data = await res.json();
    if (data.path) {
      $('folder-input').value = data.path;
    }
  } catch (e) {
    appendLog('✖ Browse cancelled or failed.');
  }
}

async function runPipeline() {
  if (state.pipelineRunning) return;

  state.pipelineRunning = true;
  $('run-btn').disabled = true;
  $('run-btn').innerHTML = '<i data-lucide="loader" class="spin-slow"></i> Running...';
  $('cancel-btn').classList.remove('hidden');
  setTerminalStatus('running', 'Pipeline Active');
  setStatusBar('Pipeline running...', true);
  appendLog('');
  appendLog('═'.repeat(50));
  appendLog('🚀 PIPELINE STARTED — ' + new Date().toLocaleTimeString());
  appendLog('═'.repeat(50));
  state.lastLog = '';

  const formData = new FormData();
  formData.append('op_mode', state.opMode);
  formData.append('scope', state.scope);
  formData.append('device', $('device-select').value);
  formData.append('gemini_model', $('model-select').value);
  formData.append('split_mode', state.splitMode);
  formData.append('custom_seconds', parseInt($('custom-seconds').value) || 600);
  formData.append('text_box', $('text-box').value);
  formData.append('folder_input', $('folder-input').value);

  const appendFile = (inputId, fieldName) => {
    const input = $(inputId);
    if (input && input.files && input.files.length > 0) {
      for (let i = 0; i < input.files.length; i++) {
        formData.append(fieldName, input.files[i]);
      }
    }
  };

  appendFile('single-audio-input', 'single_audio');
  const multiAudio = $('multi-audio-input');
  if (multiAudio && multiAudio.files && multiAudio.files.length > 0) {
    for (let i = 0; i < multiAudio.files.length; i++) {
      formData.append('multi_audio', multiAudio.files[i]);
    }
  }
  appendFile('single-txt-input', 'single_txt');
  const multiTxt = $('multi-txt-input');
  if (multiTxt && multiTxt.files && multiTxt.files.length > 0) {
    for (let i = 0; i < multiTxt.files.length; i++) {
      formData.append('multi_txt', multiTxt.files[i]);
    }
  }
  appendFile('srt-txt-input', 'srt_txt_file');
  appendFile('srt-json-input', 'srt_json_file');

  try {
    const response = await fetch('/api/pipeline', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const err = await response.text();
      appendLog('✖ Pipeline launch failed: ' + err);
      finishPipeline(false);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.log) {
              const newContent = data.log;
              const prevLen = state.lastLog.length;
              const newText = newContent.slice(prevLen);
              if (newText) {
                appendLog(newText.replace(/\n$/, ''));
              }
              state.lastLog = newContent;
            } else if (data.status === 'completed') {
              appendLog('');
              appendLog('═'.repeat(50));
              appendLog('🎉 PIPELINE COMPLETED');
              appendLog('═'.repeat(50));
              finishPipeline(true);
            } else if (data.status === 'cancelled') {
              appendLog('');
              appendLog('═'.repeat(50));
              appendLog('⚠️ PIPELINE CANCELLED');
              appendLog('═'.repeat(50));
              finishPipeline(false);
            } else if (data.error) {
              appendLog('✖ ERROR: ' + data.error);
              finishPipeline(false);
            }
          } catch (e) {
            // ignore parse errors for heartbeat lines
          }
        }
      }
    }
  } catch (e) {
    appendLog('✖ Connection lost: ' + e.message);
    finishPipeline(false);
  }
}

function finishPipeline(success) {
  state.pipelineRunning = false;
  state.lastLog = '';
  $('run-btn').disabled = false;
  $('run-btn').innerHTML = '<i data-lucide="zap"></i> Run Pipeline';
  $('cancel-btn').classList.add('hidden');
  if (success) {
    setTerminalStatus('success', 'Complete');
    setStatusBar('Pipeline completed successfully', true);
  } else {
    setTerminalStatus('idle', 'Idle');
    setStatusBar('Pipeline finished', false);
  }
  lucide.createIcons();
}

async function cancelPipeline() {
  try {
    await fetch('/api/pipeline/cancel', { method: 'POST' });
    if (state.eventSource) {
      state.eventSource.close();
      state.eventSource = null;
    }
    appendLog('⚠️ Cancellation requested...');
  } catch (e) {
    appendLog('✖ Cancel failed: ' + e.message);
  }
}
