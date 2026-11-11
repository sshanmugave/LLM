// ══════════════════════════════════════════════════════════════════
// Flyover Pier Extractor — Clean Modern App Controller (v2)
// ══════════════════════════════════════════════════════════════════

let appState = {
  activePage: 'page-docs',
  piers: [],
  cornerPoints: [],
  stats: {},
  crs: {},
  reviewItems: [],
  selectedReviewItem: null,
  statusPollInterval: null,
};

// ── DOM Ready ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupUpload();
  setupPipeline();
  setupFilters();
  setupAI();
  setupCRS();
  setupClearActive();

  // If new browser session, reset active view so screen starts clean.
  // Uploaded documents & past run archives remain safely stored.
  if (!sessionStorage.getItem('fp_session_active')) {
    sessionStorage.setItem('fp_session_active', '1');
    try {
      await fetch('/api/pipeline/session-reset', { method: 'POST' });
    } catch (e) {
      console.warn('Session reset error:', e);
    }
  }

  // Load initial data
  loadCRS();
  loadUploadedDocs();
  loadStats();
  checkPipelineStatus();
});

// ── Navigation ─────────────────────────────────────────────────
function setupNavigation() {
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const pageId = btn.dataset.page;
      navigateTo(pageId);
    });
  });

  // Top Tabs Navigation
  document.querySelectorAll('.top-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const pageId = btn.dataset.page;
      navigateTo(pageId);
    });
  });

  // Short-cuts
  document.getElementById('btn-go-pipeline')?.addEventListener('click', () => {
    navigateTo('page-pipeline');
  });
}

const pageTitles = {
  'page-docs':     { title: 'Documents & Ingestion',   sub: 'Upload engineering drawings, Excel workbooks & JSON datasets' },
  'page-pipeline': { title: 'Extraction Pipeline',     sub: 'Run autonomous CAD table parsing, geometry reconstruction & 3D solid extrusion' },
  'page-piers':    { title: '3D Pier Master Catalog', sub: 'Parametric centroids, coordinates, skew azimuths & verification matrix' },
  'page-points':   { title: 'Footing Polygon Vertices',sub: '3D corner vertices extracted for solid CAD/BIM extrusions' },
  'page-deck':     { title: 'CAD Cross-Sections',      sub: 'Deck geometry, roadway widths, slopes & girder typologies (Sections 1-1 & 2-2)' },
  'page-geo':      { title: 'Geotechnical Strata',     sub: 'Borehole logs BH-20 to BH-30 & foundation embedment depth Df' },
  'page-ai':       { title: 'Engineering AI Assistant',sub: 'Offline drawing intelligence, technical Q&A & 3D conversion brief' },
  'page-history':  { title: 'Pipeline Run Archives',   sub: 'Archived pipeline runs — inspect or restore anytime with one click' },
  'page-review':   { title: 'Quality Review & QC',     sub: 'Side-by-side CAD drawing verification & discrepancy resolution' },
  'page-crs':      { title: 'Geodetic CRS Settings',   sub: 'Coordinate Reference System configuration & real-time recomputation' },
  'page-export':   { title: 'Export Deliverables',     sub: 'Download 7-sheet Master Excel workbook & Civil 3D alignment CSVs' },
};

function navigateTo(pageId) {
  // Update sidebar active state
  document.querySelectorAll('.nav-item').forEach(b => {
    b.classList.toggle('active', b.dataset.page === pageId);
  });

  // Update top tabs active state
  document.querySelectorAll('.top-tab-btn').forEach(tb => {
    tb.classList.toggle('active', tb.dataset.page === pageId);
  });

  // Update workflow steps active state
  document.querySelectorAll('.workflow-step').forEach(ws => {
    const fn = ws.getAttribute('onclick') || '';
    ws.classList.toggle('active', fn.includes(`'${pageId}'`));
  });

  // Update sub-tabs active state
  document.querySelectorAll('.data-tab-btn').forEach(tb => {
    const fn = tb.getAttribute('onclick') || '';
    tb.classList.toggle('active', fn.includes(`'${pageId}'`));
  });

  // Update page visibility
  document.querySelectorAll('.page').forEach(p => {
    p.classList.toggle('active', p.id === pageId);
  });

  // Update topbar titles
  const info = pageTitles[pageId] || { title: 'FLYOVER 3D STUDIO', sub: 'Civil Infrastructure Extractor' };
  document.getElementById('topbar-title').innerText = info.title;
  document.getElementById('topbar-sub').innerText   = info.sub;

  appState.activePage = pageId;

  // Lazy-load page data
  if (pageId === 'page-piers')   loadPiers();
  if (pageId === 'page-points')  loadPoints();
  if (pageId === 'page-deck')    loadDeckSections();
  if (pageId === 'page-geo')     loadBoreholes();
  if (pageId === 'page-ai')      loadInsights();
  if (pageId === 'page-history') loadHistory();
  if (pageId === 'page-review')  loadReviewItems();
  if (pageId === 'page-crs')     loadCRS();
}

window.navigateTo = navigateTo;

// ── Upload Feature (US-LLM-001..004 + Delete + Double-click Preview) ──────────
function setupUpload() {
  const dropzone      = document.getElementById('dropzone');
  const fileInput     = document.getElementById('file-input');
  const browseTrigger = document.getElementById('browse-trigger');
  const btnScan       = document.getElementById('btn-scan-workspace');
  const btnRefresh    = document.getElementById('btn-refresh-docs');

  // Open file picker
  dropzone.addEventListener('click', (e) => {
    if (e.target.id !== 'browse-trigger') fileInput.click();
  });
  browseTrigger?.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  // Drag & drop
  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) uploadFiles(fileInput.files);
  });

  // Scan workspace
  btnScan?.addEventListener('click', async () => {
    btnScan.disabled = true;
    btnScan.innerHTML = '⏳ Scanning…';
    try {
      const res = await fetch('/api/upload/load-existing', { method: 'POST' });
      const data = await res.json();
      const failedCount = (data.failed || []).length;
      const validCount = (data.registered || []).length;
      const msg = `Scanned workspace: ${validCount} valid file(s) registered${failedCount ? `, ${failedCount} invalid file(s) flagged` : ''}.`;
      showToast(failedCount ? 'warning' : 'success', msg);
      appendLog(`[INGEST] Registered ${validCount} valid file(s)${failedCount ? `, flagged ${failedCount} invalid file(s)` : ''}.`);
      loadUploadedDocs();
    } catch (err) {
      showToast('error', `Error scanning workspace: ${err.message}`);
    } finally {
      btnScan.disabled = false;
      btnScan.innerHTML = '🗂 Scan Workspace';
    }
  });

  // Refresh
  btnRefresh?.addEventListener('click', loadUploadedDocs);
}

async function uploadFiles(fileList) {
  if (!fileList || !fileList.length) return;
  const formData = new FormData();
  for (const f of fileList) formData.append('files', f);

  try {
    const res = await fetch('/api/upload/files', { method: 'POST', body: formData });
    const data = await res.json();

    const accepted = data.uploaded || [];
    const rejected = data.rejected || [];

    let msg = '';
    if (accepted.length) {
      msg += accepted.map(f =>
        `<div class="toast-line">✅ <strong>${f.filename}</strong> — ID #${f.document_id} · ${(f.size_bytes/1024).toFixed(1)} KB</div>`
      ).join('');
    }
    if (rejected.length) {
      msg += rejected.map(r =>
        `<div class="toast-line">❌ <strong>${r.filename}</strong> — ${r.reason}</div>`
      ).join('');
    }

    const toastType = rejected.length && !accepted.length ? 'error' : rejected.length ? 'warning' : 'success';
    showToast(toastType, msg);

    // Terminal log
    accepted.forEach(f => appendLog(`[UPLOAD] ✅ ${f.filename} (${f.file_type?.toUpperCase()}) → ID #${f.document_id}`));
    rejected.forEach(r => appendLog(`[UPLOAD] ❌ ${r.filename} — ${r.reason}`));

    loadUploadedDocs();
  } catch (err) {
    showToast('error', `Upload failed: ${err.message}`);
  }
}

function showToast(type, html) {
  const toast = document.getElementById('upload-toast');
  if (!toast) return;
  toast.className = `toast toast-${type}`;
  toast.innerHTML = html;
  toast.style.display = 'block';
  setTimeout(() => { toast.style.display = 'none'; }, 7000);
}

async function loadUploadedDocs() {
  try {
    const res = await fetch('/api/upload/list');
    const data = await res.json();
    renderDocsList(data.files || []);
  } catch (err) {
    console.error('Error loading documents:', err);
  }
}

function renderDocsList(files) {
  const container = document.getElementById('docs-list-container');
  const countBadge = document.getElementById('docs-count');
  const hint       = document.getElementById('docs-hint');

  if (countBadge) countBadge.innerText = files.length;
  if (hint) hint.style.display = files.length ? 'block' : 'none';

  if (!files.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📁</div>
        <p>No documents yet. Upload files or scan the workspace folder.</p>
      </div>`;
    return;
  }

  const icons = { pdf: '📄', excel: '📊', json: '📋' };
  const iconClasses = { pdf: 'doc-icon-pdf', excel: 'doc-icon-excel', json: 'doc-icon-json' };

  container.innerHTML = `
    <div class="docs-list">
      ${files.map(f => {
        const icon = icons[f.file_type] || '📎';
        const iconClass = iconClasses[f.file_type] || '';
        const sizeKB = f.file_size_bytes ? (f.file_size_bytes / 1024).toFixed(1) + ' KB' : '—';

        let meta = '';
        if (f.file_type === 'excel' && f.meta?.sheets?.length) {
          meta = `${f.meta.sheets.length} sheet${f.meta.sheets.length > 1 ? 's' : ''}: ${f.meta.sheets.map(s => s.sheet).join(', ')}`;
        } else if (f.file_type === 'json' && f.meta) {
          if (f.meta.type === 'array') meta = `Array · ${f.meta.count || f.meta.element_count} items`;
          else if (f.meta.keys) meta = `Object · keys: ${f.meta.keys.slice(0, 4).join(', ')}`;
        } else if (f.file_type === 'pdf') {
          const pgCount = f.meta?.page_count;
          meta = pgCount ? `PDF Drawing (${pgCount} pages)` : 'PDF Engineering Drawing';
        }

        let statusBadge = '<span class="badge badge-green">✓ Valid</span>';
        if (f.status === 'password_protected') {
          statusBadge = '<span class="badge badge-amber" title="Password-Protected File (US-LLM-007)">🔒 Encrypted</span>';
        } else if (f.status === 'failed' || f.status === 'corrupted' || f.is_valid === 0) {
          statusBadge = '<span class="badge badge-red" title="Corrupted / Unreadable File (US-LLM-006)">❌ Corrupted</span>';
        } else if (f.status === 'unsupported') {
          statusBadge = '<span class="badge badge-amber" title="Unsupported Format (US-LLM-008)">⚠️ Unsupported</span>';
        }

        const errorHtml = f.error_message
          ? `<div style="font-size:11px;color:var(--color-rose);margin-top:3px;font-weight:500;">⚠️ ${escapeHtml(f.error_message)}</div>`
          : '';

        return `
          <div class="doc-row" id="doc-row-${f.id}"
               ondblclick="previewDocument(${f.id}, '${escapeHtml(f.filename)}', '${f.file_type}')"
               title="Double-click to open preview">
            <div class="doc-row-icon ${iconClass}">${icon}</div>
            <div class="doc-row-info">
              <div class="doc-name">${escapeHtml(f.filename)}</div>
              <div class="doc-meta">${(f.file_type || '').toUpperCase()} · ${sizeKB}${meta ? ' · ' + meta : ''}</div>
              ${errorHtml}
            </div>
            ${statusBadge}
            <span class="doc-id-badge">ID #${f.id}</span>
            <div class="doc-actions">
              <button class="btn btn-ghost btn-icon" onclick="previewDocument(${f.id}, '${escapeHtml(f.filename)}', '${f.file_type}')" title="Preview file">👁</button>
              <button class="btn btn-danger btn-icon" onclick="confirmDeleteDoc(event, ${f.id}, '${escapeHtml(f.filename)}')" title="Delete file">🗑</button>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

// Delete document
function confirmDeleteDoc(e, id, filename) {
  e.stopPropagation();
  const row = document.getElementById(`doc-row-${id}`);
  if (!row) return;

  const overlay = document.createElement('div');
  overlay.className = 'confirm-overlay';
  overlay.innerHTML = `
    <span style="font-size:12px;color:var(--text);font-weight:600;">Delete ${escapeHtml(filename)}?</span>
    <button class="btn btn-danger btn-sm" onclick="executeDeleteDoc(${id})">Yes, delete</button>
    <button class="btn btn-secondary btn-sm" onclick="this.parentElement.remove()">Cancel</button>
  `;
  row.appendChild(overlay);
}

async function executeDeleteDoc(id) {
  try {
    const res = await fetch(`/api/upload/files/${id}`, { method: 'DELETE' });
    const data = await res.json();
    showToast('success', `Deleted document: ${data.filename}`);
    appendLog(`[DELETE] Document #${id} (${data.filename}) removed.`);
    loadUploadedDocs();
  } catch (err) {
    showToast('error', `Failed to delete document: ${err.message}`);
  }
}

// Preview document (Double-click or 👁 button)
async function openValidationLogsModal() {
  const modal      = document.getElementById('preview-modal');
  const modalTitle = document.getElementById('preview-modal-title');
  const modalBody  = document.getElementById('preview-modal-body');

  modalTitle.innerText = '📋 File Validation Audit Trail (LLM-DOD-02)';
  modalBody.innerHTML  = '<div style="padding:40px;text-align:center;color:var(--text-muted);">Fetching validation logs…</div>';
  modal.style.display  = 'flex';

  try {
    const res = await fetch('/api/upload/validation-logs');
    const data = await res.json();
    const logs = data.validation_logs || [];

    if (!logs.length) {
      modalBody.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📋</div>
          <p>No file validation logs recorded yet. Upload files or scan the workspace to trigger validation.</p>
        </div>
      `;
      return;
    }

    modalBody.innerHTML = `
      <div style="margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:12px;color:var(--text-muted);">
          Pre-processing integrity and format verification records (US-LLM-005, US-LLM-006, US-LLM-007, US-LLM-008).
        </span>
        <span class="badge badge-neutral">${logs.length} Log Entries</span>
      </div>
      <div style="max-height:60vh;overflow-y:auto;border:1px solid var(--border-default);border-radius:var(--radius-md);">
        <table style="font-size:12px;">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Status</th>
              <th>Filename</th>
              <th>Log Details / Diagnostics</th>
            </tr>
          </thead>
          <tbody>
            ${logs.map(l => {
              const badgeClass = l.level === 'INFO' ? 'badge-green' : (l.level === 'WARNING' ? 'badge-amber' : 'badge-red');
              return `
                <tr>
                  <td class="mono text-dim" style="font-size:11px;">${escapeHtml(l.timestamp)}</td>
                  <td><span class="badge ${badgeClass}">${escapeHtml(l.level)}</span></td>
                  <td class="mono fw-bold" style="font-size:11.5px;color:var(--color-primary);">${escapeHtml(l.filename || '—')}</td>
                  <td style="white-space:normal;line-height:1.45;">${escapeHtml(l.message)}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div class="toast toast-error">Failed to fetch validation logs: ${escapeHtml(err.message)}</div>`;
  }
}
window.openValidationLogsModal = openValidationLogsModal;

async function previewDocument(id, filename, fileType) {
  const modal      = document.getElementById('preview-modal');
  const modalTitle = document.getElementById('preview-modal-title');
  const modalBody  = document.getElementById('preview-modal-body');

  modalTitle.innerText = `${filename}`;
  modalBody.innerHTML  = '<div style="padding:40px;text-align:center;color:var(--text-dim);">Loading preview…</div>';
  modal.style.display  = 'flex';

  try {
    const res = await fetch(`/api/upload/preview-data/${id}`);
    const data = await res.json();

    if (fileType === 'pdf') {
      modalBody.innerHTML = `
        <div class="preview-iframe-wrap">
          <iframe src="${data.preview_url}" title="${escapeHtml(filename)}"></iframe>
        </div>
      `;
    } else if (fileType === 'json') {
      modalBody.innerHTML = `
        <div class="json-viewer">${escapeHtml(JSON.stringify(data.data, null, 2))}</div>
      `;
    } else if (fileType === 'excel') {
      const sheetNames = Object.keys(data.sheets || {});
      if (!sheetNames.length) {
        modalBody.innerHTML = '<div style="padding:20px;color:var(--text-dim);">No sheets found in workbook.</div>';
        return;
      }
      modalBody.innerHTML = `
        <div class="excel-sheet-tabs" id="preview-sheet-tabs">
          ${sheetNames.map((name, i) => `
            <button class="sheet-tab ${i === 0 ? 'active' : ''}" onclick="switchPreviewSheet('${escapeHtml(name)}')">
              ${escapeHtml(name)}
            </button>
          `).join('')}
        </div>
        <div class="excel-table-wrap" id="preview-sheet-content">
          ${renderSheetTable(data.sheets[sheetNames[0]])}
        </div>
      `;
      window._currentExcelSheets = data.sheets;
    }
  } catch (err) {
    modalBody.innerHTML = `<div style="padding:30px;color:var(--red);">Failed to load preview: ${err.message}</div>`;
  }
}

function switchPreviewSheet(sheetName) {
  document.querySelectorAll('#preview-sheet-tabs .sheet-tab').forEach(t => {
    t.classList.toggle('active', t.innerText.trim() === sheetName);
  });
  const container = document.getElementById('preview-sheet-content');
  if (container && window._currentExcelSheets) {
    container.innerHTML = renderSheetTable(window._currentExcelSheets[sheetName]);
  }
}

function renderSheetTable(rows) {
  if (!rows || !rows.length) return '<div style="padding:20px;color:var(--text-dim);">Sheet is empty.</div>';
  const header = rows[0];
  const dataRows = rows.slice(1);
  return `
    <table>
      <thead>
        <tr>${header.map(c => `<th>${escapeHtml(c || '')}</th>`).join('')}</tr>
      </thead>
      <tbody>
        ${dataRows.map(r => `
          <tr>${r.map(c => `<td>${escapeHtml(c || '')}</td>`).join('')}</tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function closePreviewModal() {
  document.getElementById('preview-modal').style.display = 'none';
  window._currentExcelSheets = null;
}

// ── Pipeline ───────────────────────────────────────────────────
function setupPipeline() {
  const btnRun = document.getElementById('btn-run-pipeline');
  btnRun?.addEventListener('click', startPipeline);
}

async function startPipeline() {
  const btnRun = document.getElementById('btn-run-pipeline');
  btnRun.disabled = true;
  btnRun.innerText = '⚙️ Running Pipeline…';

  try {
    const res = await fetch('/api/pipeline/run', { method: 'POST' });
    const data = await res.json();
    appendLog(`[PIPELINE] Initiated: ${data.message}`);

    if (appState.statusPollInterval) clearInterval(appState.statusPollInterval);
    appState.statusPollInterval = setInterval(checkPipelineStatus, 1500);
  } catch (err) {
    appendLog(`[PIPELINE] Error starting: ${err.message}`);
    btnRun.disabled = false;
    btnRun.innerText = '⚡ Run Pipeline';
  }
}

async function checkPipelineStatus() {
  try {
    const res = await fetch('/api/pipeline/status');
    const d = await res.json();

    const fill  = document.getElementById('progress-fill');
    const pct   = document.getElementById('progress-pct');
    const stage = document.getElementById('pipeline-stage-text');
    const btn   = document.getElementById('btn-run-pipeline');

    if (fill) fill.style.width = `${d.progress_percent}%`;
    if (pct) pct.innerText = `${d.progress_percent}%`;
    if (stage) stage.innerText = d.message || d.current_stage;

    if (d.status === 'completed') {
      clearInterval(appState.statusPollInterval);
      if (btn) { btn.disabled = false; btn.innerText = '⚡ Run Pipeline'; }
      appendLog('✅ Pipeline complete!');
      await loadStats();
      // Show stats row on pipeline page
      const psRow = document.getElementById('pipeline-stats-row');
      if (psRow) psRow.style.display = 'grid';
    } else if (d.status === 'error') {
      clearInterval(appState.statusPollInterval);
      if (btn) { btn.disabled = false; btn.innerText = '⚡ Run Pipeline'; }
      appendLog(`❌ Pipeline error: ${d.message}`);
    }
  } catch (err) {
    console.error('Error polling pipeline:', err);
  }
}

function appendLog(msg) {
  const term = document.getElementById('terminal');
  if (!term) return;
  const time = new Date().toLocaleTimeString();
  term.innerHTML += `[${time}] ${msg}\n`;
  term.scrollTop = term.scrollHeight;
}

// ── Clear Active View & History Controls ──────────────────────
function setupClearActive() {
  document.getElementById('btn-topbar-clear')?.addEventListener('click', async () => {
    if (!confirm('Clear active catalog tables? (Your uploaded documents and run archives will remain completely safe).')) return;
    try {
      await fetch('/api/pipeline/clear-active', { method: 'POST' });
      showToast('success', 'Active view cleared. Run the pipeline anytime to re-populate.');
      await loadStats();
      if (appState.activePage === 'page-piers')  loadPiers();
      if (appState.activePage === 'page-points') loadPoints();
      if (appState.activePage === 'page-deck')   loadDeckSections();
      if (appState.activePage === 'page-geo')    loadBoreholes();
    } catch (err) {
      showToast('error', 'Failed to clear view: ' + err.message);
    }
  });

  document.getElementById('btn-refresh-history')?.addEventListener('click', loadHistory);
}

async function loadHistory() {
  const container = document.getElementById('history-list-container');
  if (!container) return;
  try {
    const res = await fetch('/api/pipeline/history');
    const data = await res.json();
    const runs = data.history || [];

    const nbHistory = document.getElementById('nb-history');
    if (nbHistory) nbHistory.innerText = runs.length;
    const ttHistory = document.getElementById('tt-history');
    if (ttHistory) ttHistory.innerText = runs.length;

    if (!runs.length) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📜</div>
          <p>No archived runs found yet. Run the extraction pipeline to create an archive.</p>
        </div>`;
      return;
    }

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:12px;">
        ${runs.map(r => `
          <div class="card" style="margin-bottom:0;display:flex;flex-direction:column;gap:10px;background:rgba(255,255,255,.02);border:1px solid var(--border-soft);">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
              <div>
                <strong style="font-size:13.5px;color:var(--text);">${escapeHtml(r.label || r.run_id)}</strong>
                <span class="mono" style="font-size:11px;color:var(--accent-lite);margin-left:8px;">${r.run_id}</span>
                <div style="font-size:11px;color:var(--text-dim);margin-top:2px;">
                  Archived on: ${new Date(r.timestamp + 'Z').toLocaleString()}
                </div>
              </div>
              <div style="display:flex;gap:8px;align-items:center;">
                <button class="btn btn-primary btn-sm" onclick="restoreRun('${r.run_id}')">
                  📥 Load into Catalog
                </button>
                <button class="btn btn-danger btn-sm" onclick="deleteHistoryRun('${r.run_id}')">
                  🗑 Delete
                </button>
              </div>
            </div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;border-top:1px solid var(--border-soft);padding-top:8px;">
              <span class="stat-chip amber">Piers: <strong>${r.total_piers}</strong></span>
              <span class="stat-chip">Points: <strong>${r.total_points}</strong></span>
              <span class="stat-chip">Sections: <strong>${r.total_sections}</strong></span>
              <span class="stat-chip">Boreholes: <strong>${r.total_boreholes}</strong></span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="padding:20px;color:var(--red);">Failed to load history: ${err.message}</div>`;
  }
}

async function restoreRun(runId) {
  try {
    const res = await fetch(`/api/pipeline/restore/${encodeURIComponent(runId)}`, { method: 'POST' });
    const data = await res.json();
    showToast('success', `Archived run ${runId} restored into active catalog!`);
    await loadStats();
    navigateTo('page-piers');
  } catch (err) {
    showToast('error', `Failed to restore run: ${err.message}`);
  }
}

async function deleteHistoryRun(runId) {
  if (!confirm(`Delete archive ${runId}?`)) return;
  try {
    await fetch(`/api/pipeline/history/${encodeURIComponent(runId)}`, { method: 'DELETE' });
    showToast('success', `Deleted archive ${runId}`);
    loadHistory();
    loadStats();
  } catch (err) {
    showToast('error', `Failed to delete archive: ${err.message}`);
  }
}

// ── Stats ──────────────────────────────────────────────────────
async function loadStats() {
  try {
    const res = await fetch('/api/results/stats');
    const d = await res.json();
    appState.stats = d;

    // Topbar chips
    document.getElementById('tc-piers').innerText  = d.total_piers  || 0;
    document.getElementById('tc-points').innerText = d.total_points || 0;

    // Sidebar badges
    const nbPiers  = document.getElementById('nb-piers');
    const nbPoints = document.getElementById('nb-points');
    const nbFlags  = document.getElementById('nb-flags');
    if (nbPiers)  nbPiers.innerText  = d.total_piers  || 0;
    if (nbPoints) nbPoints.innerText = d.total_points || 0;

    // Top Tab badges
    const ttPiers  = document.getElementById('tt-piers');
    const ttPoints = document.getElementById('tt-points');
    const ttFlags  = document.getElementById('tt-flags');
    if (ttPiers)  ttPiers.innerText  = d.total_piers  || 0;
    if (ttPoints) ttPoints.innerText = d.total_points || 0;

    // Flags
    const flagsCount = (d.points_needing_review || 0) + (d.unresolved_conflicts || 0);
    if (ttFlags) {
      ttFlags.innerText = flagsCount;
      ttFlags.style.display = flagsCount > 0 ? 'inline-flex' : 'none';
    }
    const tcFlagsChip = document.getElementById('tc-flags-chip');
    if (flagsCount > 0) {
      if (tcFlagsChip) { tcFlagsChip.style.display = 'inline-flex'; }
      document.getElementById('tc-flags').innerText = flagsCount;
      if (nbFlags) { nbFlags.style.display = 'inline-block'; nbFlags.innerText = flagsCount; }
    } else {
      if (tcFlagsChip) tcFlagsChip.style.display = 'none';
      if (nbFlags) nbFlags.style.display = 'none';
    }

    // Pipeline page stats
    const psPiers  = document.getElementById('ps-piers');
    const psPoints = document.getElementById('ps-points');
    const psFlags  = document.getElementById('ps-flags');
    const psDocs   = document.getElementById('ps-docs');
    if (psPiers)  psPiers.innerText  = d.total_piers  || 0;
    if (psPoints) psPoints.innerText = d.total_points || 0;
    if (psFlags)  psFlags.innerText  = flagsCount;
    if (psDocs)   psDocs.innerText   = document.getElementById('docs-count')?.innerText || 0;

    // History count badge
    try {
      const hRes = await fetch('/api/pipeline/history');
      const hData = await hRes.json();
      const nbHistory = document.getElementById('nb-history');
      if (nbHistory) nbHistory.innerText = (hData.history || []).length;
    } catch (e) {}

  } catch (err) {
    console.error('Error loading stats:', err);
  }
}

// ── Piers Catalog ──────────────────────────────────────────────
function setupFilters() {
  const cwFilter     = document.getElementById('filter-cw');
  const statusFilter = document.getElementById('filter-status');
  const searchInput  = document.getElementById('search-pier');

  const reload = () => loadPiers();
  cwFilter?.addEventListener('change', reload);
  statusFilter?.addEventListener('change', reload);

  let debounce;
  searchInput?.addEventListener('input', () => {
    clearTimeout(debounce);
    debounce = setTimeout(reload, 250);
  });
}

async function loadPiers() {
  const cw     = document.getElementById('filter-cw')?.value || 'All';
  const status = document.getElementById('filter-status')?.value || 'All';
  const search = document.getElementById('search-pier')?.value || '';

  const params = new URLSearchParams({ carriageway: cw, status: status, search: search });
  try {
    const res = await fetch(`/api/results/piers?${params}`);
    const data = await res.json();
    appState.piers = data.piers;
    renderPiersTable(data.piers);
  } catch (err) {
    console.error('Error loading piers:', err);
  }
}

function renderPiersTable(piers) {
  const tbody = document.getElementById('piers-tbody');
  if (!tbody) return;

  if (!piers.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="15" class="text-dim" style="text-align:center;padding:36px;">
          <div style="font-size:24px;margin-bottom:8px;">🏗️</div>
          <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:4px;">No active pier data in catalog</div>
          <p style="font-size:11.5px;color:var(--text-dim);margin-bottom:12px;">Run the pipeline to extract fresh pier coordinates, or load a saved run from Run History.</p>
          <div style="display:flex;gap:8px;justify-content:center;">
            <button class="btn btn-primary btn-sm" onclick="navigateTo('page-pipeline')">⚡ Run Pipeline</button>
            <button class="btn btn-secondary btn-sm" onclick="navigateTo('page-history')">📜 View Run History</button>
          </div>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = piers.map(p => {
    const badgeClass = p.status === 'Verified' ? 'badge-green' : p.status === 'Review Required' ? 'badge-amber' : 'badge-red';
    const latStr   = p.latitude  !== null ? p.latitude.toFixed(6)  : '—';
    const lonStr   = p.longitude !== null ? p.longitude.toFixed(6) : '—';
    const ceStr    = p.centre_easting  !== null ? p.centre_easting.toFixed(3)  : '—';
    const cnStr    = p.centre_northing !== null ? p.centre_northing.toFixed(3) : '—';
    const skewStr  = p.skew_angle_deg  !== null ? `${p.skew_angle_deg.toFixed(1)}°` : '—';
    const spanStr  = p.span_length     !== null ? `${(p.span_length/1000).toFixed(0)}m` : '—';
    const capStr   = p.pier_cap_width   !== null ? `${p.pier_cap_width.toFixed(0)}mm` : '—';
    const shaftStr = p.pier_shaft_width !== null ? `${p.pier_shaft_width.toFixed(0)}mm` : '—';
    const footStr  = (p.footing_length && p.footing_width) ? `${p.footing_length.toFixed(1)}×${p.footing_width.toFixed(1)}m` : '—';

    return `
      <tr>
        <td><strong>${escapeHtml(p.carriageway)}</strong></td>
        <td>
          <a href="javascript:void(0)" onclick="openPierModal('${escapeHtml(p.carriageway)}', '${escapeHtml(p.pier_id)}')"
             style="font-weight:700;color:var(--accent-lite);text-decoration:none;">
            ${escapeHtml(p.pier_id)}
          </a>
        </td>
        <td><code>${escapeHtml(p.point_range || '—')}</code></td>
        <td class="mono">${ceStr}</td>
        <td class="mono">${cnStr}</td>
        <td class="mono text-dim">${latStr}</td>
        <td class="mono text-dim">${lonStr}</td>
        <td class="text-amber fw-bold">${skewStr}</td>
        <td>${spanStr}</td>
        <td>${capStr}</td>
        <td>${shaftStr}</td>
        <td>${footStr}</td>
        <td><span class="badge ${badgeClass}">${p.status}</span></td>
        <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;" title="${escapeHtml(p.notes || '')}">
          <small class="text-dim">${escapeHtml(p.notes || '—')}</small>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openPierModal('${escapeHtml(p.carriageway)}', '${escapeHtml(p.pier_id)}')">
            3D Dims
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// ── Pier Detail Modal ──────────────────────────────────────────
async function openPierModal(carriageway, pierId) {
  try {
    const res = await fetch(`/api/results/piers/${encodeURIComponent(carriageway)}/${encodeURIComponent(pierId)}`);
    const d = await res.json();

    document.getElementById('modal-pier-title').innerText = `Pier ${d.pier_id} (${d.carriageway})`;
    const statusBadge = document.getElementById('modal-pier-status');
    if (statusBadge) {
      statusBadge.innerText = d.status || 'Verified';
      statusBadge.className = `badge ${d.status === 'Verified' ? 'badge-green' : d.status === 'Review Required' ? 'badge-amber' : 'badge-red'}`;
    }

    document.getElementById('modal-easting').innerText  = d.centre_easting  !== null ? d.centre_easting.toFixed(3)  : '—';
    document.getElementById('modal-northing').innerText = d.centre_northing !== null ? d.centre_northing.toFixed(3) : '—';
    const latStr = d.latitude  !== null ? d.latitude.toFixed(6)  : '—';
    const lonStr = d.longitude !== null ? d.longitude.toFixed(6) : '—';
    document.getElementById('modal-latlon').innerText = `${latStr}, ${lonStr}`;
    document.getElementById('modal-skew').innerText   = d.skew_angle_deg !== null ? `${d.skew_angle_deg.toFixed(1)}°` : '0.0° (Perpendicular)';

    const shaftW = d.pier_shaft_width     || 5000;
    const shaftT = d.pier_shaft_thickness || 2500;
    document.getElementById('modal-shaft').innerText = `Width: ${shaftW.toLocaleString()} mm | Thickness: ${shaftT.toLocaleString()} mm`;

    const capW = d.pier_cap_width || 13600;
    document.getElementById('modal-cap').innerText = `Width: ${capW.toLocaleString()} mm | Cantilever: 3,000 mm`;

    const footL = d.footing_length ? `${d.footing_length.toFixed(1)} m` : '12.0 m';
    const footW = d.footing_width  ? `${d.footing_width.toFixed(1)} m`  : '8.0 m';
    document.getElementById('modal-footing').innerText = `Envelope: ${footL} × ${footW}`;

    // Points table
    const ptsTbody = document.getElementById('modal-points-tbody');
    if (ptsTbody && d.points) {
      ptsTbody.innerHTML = d.points.map(pt => `
        <tr>
          <td style="font-weight:600;color:var(--accent-lite);">${escapeHtml(pt.point_id)}</td>
          <td class="mono">${pt.easting?.toFixed(3)  || '—'}</td>
          <td class="mono">${pt.northing?.toFixed(3) || '—'}</td>
          <td><span class="badge ${pt.status === 'Verified' ? 'badge-green' : 'badge-amber'}" style="font-size:10px;">${pt.status}</span></td>
        </tr>
      `).join('');
    }

    const revBtn = document.getElementById('modal-review-btn');
    if (revBtn) {
      revBtn.onclick = () => {
        closePierModal();
        navigateTo('page-review');
        inspectPier(d.carriageway, d.pier_id);
      };
    }

    document.getElementById('pier-modal').style.display = 'flex';
  } catch (err) {
    console.error('Error opening pier modal:', err);
  }
}

function closePierModal() {
  document.getElementById('pier-modal').style.display = 'none';
}

// ── Points Table ───────────────────────────────────────────────
async function loadPoints() {
  try {
    const res = await fetch('/api/results/corner_points');
    const data = await res.json();
    const tbody = document.getElementById('points-tbody');
    if (!tbody) return;

    if (!data.corner_points.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-dim" style="text-align:center;padding:28px;">No corner points extracted yet. Run the pipeline first.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.corner_points.map(pt => {
      const badgeClass = pt.status === 'Verified' ? 'badge-green' : 'badge-amber';
      return `
        <tr>
          <td><strong>${escapeHtml(pt.point_id)}</strong></td>
          <td style="color:var(--accent-lite);font-weight:600;">${escapeHtml(pt.pier_id)}</td>
          <td>${escapeHtml(pt.carriageway)}</td>
          <td class="mono">${pt.easting.toFixed(3)}</td>
          <td class="mono">${pt.northing.toFixed(3)}</td>
          <td><small>${escapeHtml(pt.source_pdf)}</small></td>
          <td>p. ${pt.source_page}</td>
          <td><span class="badge ${badgeClass}">${pt.status}</span></td>
          <td><small class="text-dim">${escapeHtml(pt.notes || '—')}</small></td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Error loading points:', err);
  }
}

// ── Deck Sections ──────────────────────────────────────────────
async function loadDeckSections() {
  try {
    const res = await fetch('/api/results/deck-sections');
    const data = await res.json();
    const tbody = document.getElementById('deck-tbody');
    if (!tbody) return;

    if (!data.sections.length) {
      tbody.innerHTML = `<tr><td colspan="11" class="text-dim" style="text-align:center;padding:28px;">Run the pipeline to load deck sections.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.sections.map(s => `
      <tr>
        <td><strong style="color:var(--accent-lite);">${escapeHtml(s.section_name)}</strong></td>
        <td><small>${escapeHtml(s.description || '—')}</small></td>
        <td><strong>${s.carriageway_deck_width ? s.carriageway_deck_width + ' mm' : '—'}</strong></td>
        <td>${s.roadway_width ? s.roadway_width + ' mm' : '—'}</td>
        <td>${s.median_gap ? s.median_gap + ' mm' : '—'}</td>
        <td>${s.deck_slab_thk ? s.deck_slab_thk + ' mm' : '—'}</td>
        <td>${s.wearing_coat_thk ? s.wearing_coat_thk + ' mm' : '—'}</td>
        <td class="text-green fw-bold">${s.cross_slope_pct ? s.cross_slope_pct + '%' : '—'}</td>
        <td>${s.crash_barrier_width ? s.crash_barrier_width + ' mm' : '—'}</td>
        <td><small>${escapeHtml(s.girder_type || '—')}</small></td>
        <td><span class="badge badge-green">${escapeHtml(s.concrete_grade || '—')}</span></td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading deck sections:', err);
  }
}

// ── Geotechnical ───────────────────────────────────────────────
async function loadBoreholes() {
  try {
    const res = await fetch('/api/results/boreholes');
    const data = await res.json();
    const tbody = document.getElementById('geo-tbody');
    if (!tbody) return;

    if (!data.boreholes.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-dim" style="text-align:center;padding:28px;">Run the pipeline to load borehole logs.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.boreholes.map(b => `
      <tr>
        <td><strong style="color:var(--blue);">${escapeHtml(b.borehole_id)}</strong></td>
        <td>${escapeHtml(b.chainage || '—')}</td>
        <td class="mono">${b.depth_from.toFixed(2)}</td>
        <td class="mono">${b.depth_to.toFixed(2)}</td>
        <td><small>${escapeHtml(b.strata_description)}</small></td>
        <td class="text-amber fw-bold">${escapeHtml(b.spt_n_value || '—')}</td>
        <td>${b.water_table_m ? b.water_table_m.toFixed(2) + ' m' : '—'}</td>
        <td><strong>${b.foundation_depth_df ? b.foundation_depth_df.toFixed(2) + ' m' : '—'}</strong></td>
        <td><small class="text-dim">${escapeHtml(b.sheet_number || '—')}</small></td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading boreholes:', err);
  }
}

// ── AI Assistant ───────────────────────────────────────────────
function setupAI() {
  const btn = document.getElementById('btn-ask-ai');
  const input = document.getElementById('ai-input');
  btn?.addEventListener('click', runAIQuery);
  input?.addEventListener('keydown', (e) => { if (e.key === 'Enter') runAIQuery(); });
}

async function runAIQuery() {
  const input = document.getElementById('ai-input');
  const query = input?.value?.trim();
  if (!query) return;

  const btn     = document.getElementById('btn-ask-ai');
  const box     = document.getElementById('ai-answer');
  const label   = document.getElementById('ai-answer-label');
  const text    = document.getElementById('ai-answer-text');
  const cite    = document.getElementById('ai-citations');

  try {
    btn.disabled = true;
    btn.innerText = 'Analyzing…';
    box.style.display = 'block';
    label.innerText = `Question: "${query}"`;
    text.innerHTML = '<span class="text-dim">Consulting offline civil engineering engine…</span>';
    cite.innerText = '';

    const res = await fetch('/api/results/ai/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    });
    const d = await res.json();

    label.innerText = `${d.engine || 'Civil Expert Engine'} (Confidence: ${(d.confidence * 100).toFixed(0)}%)`;
    text.innerText  = d.answer;
    if (d.references?.length) cite.innerText = `Source drawings: ${d.references.join(', ')}`;
  } catch (err) {
    text.innerText = `Error: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.innerText = 'Ask AI';
  }
}

window.quickPrompt = function(q) {
  const input = document.getElementById('ai-input');
  if (input) { input.value = q; runAIQuery(); }
};

async function loadInsights() {
  try {
    const res = await fetch('/api/results/insights');
    const data = await res.json();
    const container = document.getElementById('ai-insights-container');
    if (!container) return;

    if (!data.insights.length) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🧠</div>
          <p>Run the extraction pipeline to generate AI insights.</p>
        </div>`;
      return;
    }

    container.innerHTML = data.insights.map(item => `
      <div style="background:rgba(255,255,255,.025);border:1px solid var(--border-soft);border-radius:var(--r);padding:14px;margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <div style="font-size:13.5px;font-weight:700;color:var(--text);">${escapeHtml(item.title)}</div>
          <span class="badge badge-blue">${escapeHtml(item.category)}</span>
        </div>
        <p style="color:#cbd5e1;font-size:12.5px;line-height:1.6;white-space:pre-line;">${escapeHtml(item.content)}</p>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading insights:', err);
  }
}

// ── Review Screen ──────────────────────────────────────────────
async function loadReviewItems() {
  try {
    const piersRes = await fetch('/api/results/piers?status=Review Required');
    const piersData = await piersRes.json();
    const confRes = await fetch('/api/results/conflicts');
    const confData = await confRes.json();

    const items = [
      ...piersData.piers.map(p => ({ type: 'Pier', id: p.pier_id, cw: p.carriageway, item: p })),
      ...confData.conflicts.map(c => ({ type: 'Conflict', id: c.point_id, cw: c.carriageway, item: c }))
    ];
    appState.reviewItems = items;

    const list = document.getElementById('review-list');
    if (!list) return;

    if (!items.length) {
      list.innerHTML = '<div class="empty-state" style="padding:20px 10px;"><p>No flagged items — all records verified.</p></div>';
      return;
    }

    list.innerHTML = items.map((it, idx) => `
      <div class="review-item" onclick="selectReviewItem(${idx})">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
          <strong style="font-size:12.5px;">${it.type}: ${escapeHtml(it.id)}</strong>
          <span class="badge badge-amber">${escapeHtml(it.cw)}</span>
        </div>
        <div style="font-size:11px;color:var(--text-dim);">${escapeHtml(it.item.notes || it.item.resolution_notes || 'Requires verification')}</div>
      </div>
    `).join('');

    selectReviewItem(0);
  } catch (err) {
    console.error('Error loading review items:', err);
  }
}

function selectReviewItem(idx) {
  const selected = appState.reviewItems[idx];
  if (!selected) return;
  appState.selectedReviewItem = selected;

  document.querySelectorAll('.review-item').forEach((el, i) => {
    el.classList.toggle('selected', i === idx);
  });

  document.getElementById('review-selected-label').innerText = `${selected.type} ${selected.id} (${selected.cw})`;

  if (selected.type === 'Pier') {
    const p = selected.item;
    document.getElementById('edit-height').value = p.pier_height || '';
    document.getElementById('edit-width').value  = p.pier_width  || '';
    document.getElementById('edit-notes').value  = p.notes       || '';
    inspectPier(p.carriageway, p.pier_id);
  }
}

async function inspectPier(carriageway, pierId) {
  try {
    const res = await fetch(`/api/results/piers/${encodeURIComponent(carriageway)}/${encodeURIComponent(pierId)}`);
    const d = await res.json();

    const img = document.getElementById('drawing-img');
    const lbl = document.getElementById('drawing-label');
    if (d.source_images?.length) {
      img.src = d.source_images[0].image_path;
      lbl.innerText = `${d.source_images[0].filename} (p. ${d.source_images[0].page_number})`;
    } else {
      img.src = '/page_images/GAD_1_2_1_pg0.png';
      lbl.innerText = 'General Arrangement Drawing';
    }
  } catch (err) {
    console.error('Error inspecting pier drawing:', err);
  }
}

async function savePierReview() {
  if (!appState.selectedReviewItem || appState.selectedReviewItem.type !== 'Pier') return;
  const p = appState.selectedReviewItem.item;
  const height = parseFloat(document.getElementById('edit-height').value) || null;
  const width  = parseFloat(document.getElementById('edit-width').value)  || null;
  const notes  = document.getElementById('edit-notes').value;

  try {
    await fetch('/api/results/pier/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        carriageway: p.carriageway,
        pier_id:     p.pier_id,
        pier_height: height,
        pier_width:  width,
        status:      'Verified',
        notes:       notes
      })
    });
    alert(`Pier ${p.pier_id} marked as Verified!`);
    loadReviewItems();
    loadStats();
  } catch (err) {
    alert(`Failed to save: ${err.message}`);
  }
}

// ── CRS ────────────────────────────────────────────────────────
async function loadCRS() {
  try {
    const res = await fetch('/api/crs');
    const crs = await res.json();
    appState.crs = crs;

    document.getElementById('crs-epsg').innerText   = `EPSG:${crs.epsg_code}`;
    document.getElementById('crs-name').innerText   = crs.name;
    document.getElementById('crs-source').innerText = crs.detection_source || '—';
    document.getElementById('sidebar-crs').innerText= `EPSG:${crs.epsg_code}`;

    const badge = document.getElementById('crs-status-badge');
    if (badge) {
      badge.innerHTML = crs.is_verified
        ? '<span class="badge badge-green">Verified CRS</span>'
        : '<span class="badge badge-amber">Assumed (Unverified)</span>';
    }
  } catch (err) {
    console.error('Error loading CRS:', err);
  }
}

function setupCRS() {
  const btn = document.getElementById('btn-apply-crs');
  btn?.addEventListener('click', async () => {
    const sel = document.getElementById('select-crs');
    const custom = document.getElementById('custom-epsg')?.value;
    const epsg = custom ? parseInt(custom) : parseInt(sel.value);

    try {
      btn.disabled = true;
      btn.innerText = 'Applying & Recomputing…';
      await fetch('/api/crs/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ epsg_code: epsg, is_verified: true })
      });
      appendLog(`[CRS] Updated to EPSG:${epsg}. Coordinates recomputed.`);
      await loadCRS();
      await loadStats();
      await loadPiers();
      alert(`CRS successfully updated to EPSG:${epsg}!`);
    } catch (err) {
      alert(`Error updating CRS: ${err.message}`);
    } finally {
      btn.disabled = false;
      btn.innerText = 'Apply CRS & Recompute All Coordinates';
    }
  });
}

// ── Helpers ────────────────────────────────────────────────────
function escapeHtml(str) {
  if (typeof str !== 'string') return str ?? '';
  return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
}

// Global modal close on click outside
window.addEventListener('click', (e) => {
  const pierModal = document.getElementById('pier-modal');
  const prevModal = document.getElementById('preview-modal');
  if (e.target === pierModal) closePierModal();
  if (e.target === prevModal) closePreviewModal();
});
