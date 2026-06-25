(function () {
  'use strict';

  let currentModel = 'gpt-4o';

  const state = {
    a: { messages: [], source: null, pending: false, metrics: null },
    b: { messages: [], source: null, pending: false, metrics: null },
  };

  /* ── Helpers ── */

  function $(id) { return document.getElementById(id); }

  function formatNum(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
    return String(n);
  }

  function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  /* ── SSE ── */

  function connectSSE(sessionId) {
    if (state[sessionId].source) state[sessionId].source.close();

    const es = new EventSource('/events?session=' + sessionId);

    es.addEventListener('metrics', function (e) {
      try {
        const d = JSON.parse(e.data);
        state[sessionId].metrics = d;
        updateMetrics(sessionId, d);
        updateComparison();
      } catch (_) {}
    });

    es.addEventListener('message', function (e) {
      try {
        const d = JSON.parse(e.data);
        appendMessage(sessionId, d.role, d.content, false);
      } catch (_) {}
    });

    es.addEventListener('reset', function () {
      state[sessionId].messages = [];
      clearChat(sessionId);
    });

    es.onerror = function () {};

    state[sessionId].source = es;
  }

  /* ── Metrics Update ── */

  function updateMetrics(sessionId, d) {
    $('input-val-' + sessionId).textContent = formatNum(d.prompt_tokens);
    $('output-val-' + sessionId).textContent = formatNum(d.completion_tokens);
    $('total-val-' + sessionId).textContent = formatNum(d.total_tokens);
    $('avg-val-' + sessionId).textContent = formatNum(d.avg_tpa);
    $('actions-val-' + sessionId).textContent = d.actions;

    const pct = Math.min(d.pct, 100);
    const fluid = $('fluid-' + sessionId);
    fluid.style.height = pct + '%';
    $('pct-' + sessionId).textContent = pct.toFixed(1) + '%';

    if (d.model) $('model-' + sessionId).textContent = d.model;
  }

  /* ── Comparison Chart ── */

  function updateComparison() {
    const mA = state.a.metrics;
    const mB = state.b.metrics;
    const tA = mA ? mA.total_tokens : 0;
    const tB = mB ? mB.total_tokens : 0;
    const max = Math.max(tA, tB, 1);

    $('compare-fill-a').style.width = (tA / max * 100) + '%';
    $('compare-fill-b').style.width = (tB / max * 100) + '%';
    $('compare-value-a').textContent = formatNum(tA);
    $('compare-value-b').textContent = formatNum(tB);

    const diffEl = $('compare-diff');
    if (tA === 0 && tB === 0) {
      diffEl.textContent = 'Awaiting data…';
      diffEl.style.color = '';
    } else if (tA === tB) {
      diffEl.textContent = 'Both sessions even';
      diffEl.style.color = 'var(--text-secondary)';
    } else {
      const less = tA < tB ? 'A' : 'B';
      const more = tA < tB ? 'B' : 'A';
      const lessTok = Math.min(tA, tB);
      const moreTok = Math.max(tA, tB);
      const saved = Math.round((1 - lessTok / moreTok) * 100);
      diffEl.textContent = 'Session ' + less + ' uses ' + saved + '% fewer tokens';
      diffEl.style.color = less === 'A' ? 'var(--accent-a)' : 'var(--accent-b)';
    }
  }

  /* ── Chat ── */

  function appendMessage(sessionId, role, content, isLocal) {
    const chat = $('chat-' + sessionId);
    const empty = chat.querySelector('.chat-empty');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = 'msg msg-' + role;

    const roleLabel = document.createElement('span');
    roleLabel.className = 'msg-role';
    roleLabel.textContent = role === 'user' ? 'You' : (role === 'assistant' ? 'OpenCode' : role);
    div.appendChild(roleLabel);

    const contentSpan = document.createElement('span');
    contentSpan.className = 'msg-content';
    contentSpan.textContent = content;
    div.appendChild(contentSpan);

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  function clearChat(sessionId) {
    const chat = $('chat-' + sessionId);
    chat.innerHTML = '<div class="chat-empty">Messages appear here</div>';
  }

  function setPending(sessionId, p) {
    state[sessionId].pending = p;
    const btn = $('send-' + sessionId);
    btn.disabled = p;
    btn.textContent = p ? '…' : 'Send';
  }

  /* ── Send Message ── */

  async function sendMessage(sessionId) {
    const input = $('input-' + sessionId);
    const text = input.value.trim();
    if (!text || state[sessionId].pending) return;

    input.value = '';
    const s = state[sessionId];
    s.messages.push({ role: 'user', content: text });
    appendMessage(sessionId, 'user', text, true);
    setPending(sessionId, true);

    try {
      const resp = await fetch('/session/' + sessionId + '/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: currentModel,
          messages: s.messages,
          stream: false,
        }),
      });

      const data = await resp.json();
      const choice = data.choices && data.choices[0];
      if (choice && choice.message) {
        s.messages.push(choice.message);
        appendMessage(sessionId, choice.message.role, choice.message.content, true);
      } else if (data.error) {
        appendMessage(sessionId, 'system', 'API error: ' + (data.error.detail || data.error), true);
      }
    } catch (err) {
      appendMessage(sessionId, 'system', 'Request failed: ' + err.message, true);
    } finally {
      setPending(sessionId, false);
      input.focus();
    }
  }

  /* ── Reset ── */

  async function resetSession(sessionId) {
    try {
      await fetch('/sessions/' + sessionId + '/reset', { method: 'POST' });
    } catch (_) {}
    state[sessionId].messages = [];
    clearChat(sessionId);
    $('fluid-' + sessionId).style.height = '0%';
    $('pct-' + sessionId).textContent = '0%';
    ['input-val-', 'output-val-', 'total-val-', 'avg-val-', 'actions-val-'].forEach(function (p) {
      $(p + sessionId).textContent = '0';
    });
    updateComparison();
  }

  /* ── Model Fetch ── */

  async function initModel() {
    try {
      const resp = await fetch('/session/a/v1/models');
      const data = await resp.json();
      if (data.data && data.data.length > 0) {
        currentModel = data.data[0].id;
      }
    } catch (_) {
      currentModel = 'gpt-4o';
    }
  }

  /* ── Keyboard ── */

  function handleKeydown(e, sessionId) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(sessionId);
    }
  }

  /* ── Init ── */

  function init() {
    initModel();
    connectSSE('a');
    connectSSE('b');

    $('send-a').addEventListener('click', function () { sendMessage('a'); });
    $('send-b').addEventListener('click', function () { sendMessage('b'); });
    $('input-a').addEventListener('keydown', function (e) { handleKeydown(e, 'a'); });
    $('input-b').addEventListener('keydown', function (e) { handleKeydown(e, 'b'); });

    document.querySelectorAll('.reset-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        resetSession(btn.dataset.session);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
