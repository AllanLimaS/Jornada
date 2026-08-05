document.addEventListener('DOMContentLoaded', () => {
  const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");

  const updateFlatpickrTheme = (theme) => {
    const lightLink = document.getElementById("flatpickr-light-theme");
    const darkLink = document.getElementById("flatpickr-dark-theme");
    if (lightLink && darkLink) {
      if (theme === "dark") {
        darkLink.disabled = false;
        lightLink.disabled = true;
      } else {
        lightLink.disabled = false;
        darkLink.disabled = true;
      }
    }
  };

  const currentTheme = localStorage.getItem("theme");
  if (currentTheme == "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
    updateFlatpickrTheme("dark");
  } else if (currentTheme == "light") {
    document.documentElement.setAttribute("data-theme", "light");
    updateFlatpickrTheme("light");
  } else if (prefersDarkScheme.matches) {
    document.documentElement.setAttribute("data-theme", "dark");
    updateFlatpickrTheme("dark");
  } else {
    updateFlatpickrTheme("light");
  }

  // Event delegation to survive HTMX DOM swaps
  document.addEventListener('click', function(e) {
    // Theme toggle
    const themeToggle = e.target.closest('#theme-toggle');
    if (themeToggle) {
      let theme = document.documentElement.getAttribute("data-theme");
      if (theme === "dark") {
        document.documentElement.setAttribute("data-theme", "light");
        localStorage.setItem("theme", "light");
        updateFlatpickrTheme("light");
      } else {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
        updateFlatpickrTheme("dark");
      }
    }

    // Encerrar servidor
    if (e.target.closest('#shutdown-btn')) {
      if (confirm('Encerrar o servidor do Jornada? A janela vai fechar.')) {
        fetch('/api/shutdown', { method: 'POST' })
          .catch(() => {})  // a conexao cai quando o processo morre; ignora
          .finally(() => {
            document.documentElement.innerHTML =
              '<body style="display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:Inter,sans-serif;color:#64748b;background:#f8fafc">' +
              '<div style="text-align:center"><h2 style="margin:0 0 .5rem">Jornada encerrado</h2>' +
              '<p style="margin:0">Pode fechar esta janela.</p></div></body>';
            setTimeout(() => { window.close(); }, 800);
          });
      }
    }

    // Chamado Picker — abrir
    if (e.target.closest('#chamado-picker-trigger')) {
      openChamadoPicker();
    }

    // Chamado Picker — fechar overlay
    if (e.target.closest('#chamado-picker-close')) {
      closeChamadoPicker();
    }

    // Chamado Picker — fechar ao clicar fora
    const popup = document.getElementById('chamado-picker-popup');
    const trigger = document.getElementById('chamado-picker-trigger');
    if (popup && popup.style.display !== 'none') {
      if (!popup.contains(e.target) && (!trigger || !trigger.contains(e.target))) {
        closeChamadoPicker();
      }
    }

    // Chamado Picker — limpar seleção
    if (e.target.closest('#chamado-clear-btn')) {
      clearChamado();
    }

    // Chamado Picker — selecionar item
    const pickerItem = e.target.closest('.chamado-picker-item');
    if (pickerItem) {
      const id = pickerItem.dataset.id;
      const numero = pickerItem.dataset.numero;
      const titulo = pickerItem.dataset.titulo;
      selectChamado(id, numero, titulo);
    }

    // Botão Copiar Atividade (Delegado)
    const copyBtn = e.target.closest('.copy-btn');
    if (copyBtn) {
      e.preventDefault();
      handleCopyToClipboard(copyBtn);
    }
  });

  // HTMX Helper: Reset form target after successful submit
  document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
      const form = evt.target;
      if (form.tagName === 'FORM' && form.classList.contains('js-reset-on-success')) {
        form.reset();
        
        // Reset timestamp for 'hora_inicio' to whatever the previous 'hora_fim' was, to make flow faster.
        const prevEnd = form.querySelector('[name="hora_fim"]')?.value;
        if (prevEnd) {
           const inputStart = form.querySelector('[name="hora_inicio"]');
           if (inputStart) inputStart.value = prevEnd;
        }

        // Reset chamado picker visual
        clearChamado();
      }
    }
  });

  // Fechar picker com Escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeChamadoPicker();
    }
  });

  // Acessibilidade: Abrir picker com Enter/Espaço quando focado via Tab
  document.addEventListener('keydown', function(e) {
    const trigger = e.target.closest('#chamado-picker-trigger');
    if (trigger && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      openChamadoPicker();
    }
  });

  // Auto-expand textarea
  document.addEventListener('input', function(e) {
    const textarea = e.target.closest('textarea.form-control');
    if (textarea) {
      autoExpandTextarea(textarea);
    }
  });

  // Initial auto-expand on page load
  document.querySelectorAll('textarea.form-control').forEach(autoExpandTextarea);

  // Inicializar datepickers no formulário (Flatpickr)
  const initFormDatepickers = (container = document) => {
    container.querySelectorAll('.js-datepicker').forEach(el => {
      if (!el || !el.parentNode) return;
      flatpickr(el, {
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        locale: "pt",
        allowInput: true
      });
    });
  };

  // Inicializa na carga da página
  initFormDatepickers();

  // Task 3: Auto-complete time on blur
  document.addEventListener('blur', function(e) {
    if (e.target.classList.contains('js-time-mask')) {
      let v = e.target.value;
      if (!v) return;

      // Normalize common entries
      if (/^\d{1,2}$/.test(v)) {
        v = v.padStart(2, '0') + ':00';
      } else if (/^\d{1,2}:\d$/.test(v)) {
        let parts = v.split(':');
        v = parts[0].padStart(2, '0') + ':' + parts[1] + '0';
      }
      
      // Cleanup invalid garbage
      if (!/^\d{2}:\d{2}$/.test(v)) {
        if (!/^\d{1,2}:\d{1,2}$/.test(v)) v = '';
      }

      e.target.value = v;
      // Trigger input event to ensure any listeners (like autosave) catch the change
      e.target.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }, true);

  // Auto-expand on HTMX swap e inicialização de componentes
  document.body.addEventListener('htmx:afterSwap', function(evt) {
    const target = evt.detail.target;
    
    // Task 1: Garantir que HTMX processe novos elementos (corrige botões que param de funcionar)
    htmx.process(target);

    // Auto-ajuste de textarea (no elemento ou em seus filhos)
    const textareas = target.querySelectorAll('textarea.form-control');
    textareas.forEach(autoExpandTextarea);
    if (target.tagName === 'TEXTAREA' && target.classList.contains('form-control')) {
      autoExpandTextarea(target);
    }

    initFormDatepickers(target);

    // Global Modal: Auto-open and focus
    if (target.id === 'global-modal-body') {
      const modal = document.getElementById('global-modal');
      if (modal) {
        modal.classList.add('active');
        // Prioriza focar na Hora de Início, senão pega o primeiro campo disponível
        let firstInput = target.querySelector('input[name="hora_inicio"]');
        if (!firstInput) {
          firstInput = target.querySelector('input:not([type="hidden"]), textarea, select');
        }
        
        if (firstInput) {
          setTimeout(() => firstInput.focus(), 150);
        }
      }
    }

    // Task 2: Restore Chamado Draft
    if (target.querySelector('.js-chamado-form')) {
       restoreChamadoDraft(target.querySelector('.js-chamado-form'));
    }

    // Inline Calendar Re-initialization (para navegação via HTMX/SPA)
    if (document.getElementById('inline-calendar')) {
      setTimeout(initInlineCalendar, 20);
    } else if (currentCalendarFp && document.body.contains(currentCalendarFp.calendarContainer)) {
      updateCalendarTooltips(currentCalendarFp);
    }
  });

  // Executa inicialização no carregamento inicial da página
  if (document.getElementById('inline-calendar')) {
    setTimeout(initInlineCalendar, 20);
  }

  // Feedback visual do expediente
  document.body.addEventListener('showExpedienteFeedback', function() {
    const feedback = document.getElementById('expediente-save-feedback');
    if (feedback) {
      feedback.classList.add('visible');
      setTimeout(() => feedback.classList.remove('visible'), 2200);
    }
  });

  // Mascara de Horário Restritiva (HH:MM)
  document.addEventListener('input', function(e) {
    if (e.target.classList.contains('js-time-mask')) {
      let v = e.target.value.replace(/\D/g, '').substring(0, 4);
      
      // Validação básica de horas (00-23)
      if (v.length >= 1 && parseInt(v[0]) > 2) v = '';
      if (v.length >= 2 && parseInt(v.substring(0, 2)) > 23) v = v[0];
      
      // Validação básica de minutos (00-59)
      if (v.length >= 3 && parseInt(v[2]) > 5) v = v.substring(0, 2);
      
      if (v.length >= 3) {
        v = v.substring(0, 2) + ':' + v.substring(2);
      }
      e.target.value = v;
    }

    // Task 2: Autosave Chamado Draft
    const chamadoForm = e.target.closest('.js-chamado-form');
    if (chamadoForm) {
      debounce(() => saveChamadoDraft(chamadoForm), 500)();
    }
  });

  // HTMX Helper: Handle 400 and 422 errors globally with granular messages
  document.body.addEventListener('htmx:beforeOnLoad', function (evt) {
    const xhr = evt.detail.xhr;
    const status = xhr.status;
    
    if (status >= 400 && status < 600) {
      const errorDiv = document.getElementById('form-error');
      if (!errorDiv) return;

      let message = "Ocorreu um erro ao processar a requisição (Erro " + status + ").";
      
      try {
        const response = JSON.parse(xhr.responseText);
        if (response.detail) {
          if (Array.isArray(response.detail)) {
            // Formato standard do FastAPI/Pydantic para erros de validação
            message = response.detail.map(err => {
              const field = err.loc[err.loc.length - 1];
              const fieldName = field === 'hora_inicio' ? 'Hora Início' : 
                               field === 'hora_fim' ? 'Hora Fim' : 
                               field === 'data_referencia' ? 'Data' : field;
              return `${fieldName}: ${err.msg}`;
            }).join('<br>');
          } else {
            message = response.detail;
          }
        }
      } catch (e) {
        // Se não for JSON, usa o texto puro (fallback para PlainTextResponse)
        message = xhr.responseText || message;
      }

      errorDiv.innerHTML = message;
      errorDiv.style.display = 'block';
      
      // Unlock submit button
      const submitBtn = document.querySelector('form button[type="submit"]');
      if (submitBtn) submitBtn.classList.remove('htmx-request');
    }
  }, true);

  // Limpar erros ao iniciar nova requisição
  document.body.addEventListener('htmx:beforeRequest', function(evt) {
    const errorDiv = document.getElementById('form-error');
    if (errorDiv) {
      errorDiv.style.display = 'none';
      errorDiv.innerHTML = '';
    }
  });

  // Listener para fechar o modal via trigger do servidor (HX-Trigger: closeModal)
  document.body.addEventListener('closeModal', function() {
    document.querySelectorAll('.modal-overlay.active').forEach(modal => {
      modal.classList.remove('active');
    });
    const globalModalDialog = document.getElementById('global-modal-dialog');
    if (globalModalDialog) globalModalDialog.classList.remove('modal-lg');
  });

  // Task 2: Clear draft on success
  document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful && evt.detail.xhr.status === 200) {
      const form = evt.target.closest('.js-chamado-form');
      if (form) {
        clearTimeout(debounceTimer); // Evita o race condition do save pós-submit
        const chamadoId = form.dataset.chamadoId || 'novo';
        localStorage.removeItem(`jornada_draft_chamado_${chamadoId}`);
        form.reset(); // Limpa visualmente o form que está num modal oculto
      }
    }
  });

  // Global Keydown: Focus Trap for active modals
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
      // Busca todos os overlays que estão ativos/visíveis
      const overlays = Array.from(document.querySelectorAll('.modal-overlay.active, #chamado-picker-popup')).filter(el => {
        return el.classList.contains('active') || el.style.display === 'flex' || el.style.display === 'block';
      });
      
      // Pega o último da lista (o mais profundo no DOM, que geralmente está "por cima")
      const activeModal = overlays.pop();
      
      if (activeModal) {
        trapFocus(e, activeModal);
      }
    }
    
    if (e.key === 'Escape') {
      // Fechar modal global também com Escape
      const globalModal = document.getElementById('global-modal');
      if (globalModal && globalModal.classList.contains('active')) {
        globalModal.classList.remove('active');
      }
      closeChamadoPicker();
    }
  });
});

// Helper para travar o foco (Focus Trap)
function trapFocus(e, container) {
  const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  // Filtramos apenas os elementos que estão visíveis na tela
  const focusableElements = Array.from(container.querySelectorAll(focusableSelectors)).filter(el => {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  });
  
  const firstFocusableElement = focusableElements[0];
  const lastFocusableElement = focusableElements[focusableElements.length - 1];

  if (!firstFocusableElement) return;

  if (e.shiftKey) { // Shift + Tab
    if (document.activeElement === firstFocusableElement) {
      lastFocusableElement.focus();
      e.preventDefault();
    }
  } else { // Tab
    if (document.activeElement === lastFocusableElement) {
      firstFocusableElement.focus();
      e.preventDefault();
    }
  }
}

// Helper para auto-expandir textarea
function autoExpandTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = (textarea.scrollHeight + 2) + 'px';
}

// =============================================================================
// Task 2: Chamado Autosave Helpers
// =============================================================================

function saveChamadoDraft(form) {
  const chamadoId = form.dataset.chamadoId || 'novo';
  const formData = new FormData(form);
  const data = {};
  formData.forEach((value, key) => data[key] = value);
  localStorage.setItem(`jornada_draft_chamado_${chamadoId}`, JSON.stringify(data));
  
  const indicator = form.querySelector('.js-draft-indicator');
  if (indicator) {
    const now = new Date();
    const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
    indicator.textContent = `Rascunho salvo • ${timeStr}`;
    indicator.style.opacity = '1';
  }
}

function restoreChamadoDraft(form) {
  const chamadoId = form.dataset.chamadoId || 'novo';
  const saved = localStorage.getItem(`jornada_draft_chamado_${chamadoId}`);
  if (saved) {
    const data = JSON.parse(saved);
    Object.keys(data).forEach(key => {
      const input = form.querySelector(`[name="${key}"]`);
      if (input && data[key]) {
        input.value = data[key];
        if (input.tagName === 'TEXTAREA') autoExpandTextarea(input);
      }
    });
    
    const indicator = form.querySelector('.js-draft-indicator');
    if (indicator) {
      indicator.textContent = 'Rascunho restaurado';
      indicator.style.opacity = '1';
      setTimeout(() => indicator.style.opacity = '0.7', 2000);
    }
  }
}

let debounceTimer;
function debounce(func, delay) {
  return function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => func(), delay);
  }
}

// =============================================================================
// Chamado Picker — funções globais
// =============================================================================

function openChamadoPicker() {
  const popup = document.getElementById('chamado-picker-popup');
  if (!popup) return;

  popup.style.display = 'block';

  // Carrega resultados iniciais via HTMX
  const resultsDiv = document.getElementById('chamado-picker-results');
  if (resultsDiv) {
    htmx.ajax('GET', '/htmx/chamado-picker', {target: '#chamado-picker-results', swap: 'innerHTML'});
  }

  // Foca no campo de busca
  setTimeout(() => {
    const searchInput = document.getElementById('chamado-picker-search-input');
    if (searchInput) {
      searchInput.value = '';
      searchInput.focus();
    }
  }, 100);
}

function closeChamadoPicker() {
  const popup = document.getElementById('chamado-picker-popup');
  if (popup) popup.style.display = 'none';
}

function selectChamado(id, numero, titulo) {
  // Atualiza o hidden input
  const hiddenInput = document.getElementById('chamado-id-input');
  if (hiddenInput) hiddenInput.value = id;

  // Atualiza o display visual
  const display = document.getElementById('chamado-display');
  if (display) {
    display.className = 'chamado-picker-selected';
    display.innerHTML = `
      <span class="badge badge-chamado">#${numero}</span>
      <span class="chamado-picker-selected-title">${titulo}</span>
    `;
  }

  closeChamadoPicker();
}

function clearChamado() {
  const hiddenInput = document.getElementById('chamado-id-input');
  if (hiddenInput) hiddenInput.value = '';

  const display = document.getElementById('chamado-display');
  if (display) {
    display.className = 'chamado-picker-placeholder';
    display.textContent = 'Selecionar chamado...';
  }
}

// Copiar para a área de transferência de forma robusta e com feedback visual
function handleCopyToClipboard(button) {
  const text = button.getAttribute('data-clipboard-text');
  if (!text) return;

  const svg = button.querySelector('svg');
  if (!svg) return;

  // Guarda o SVG original para restaurar depois
  if (!button.dataset.originalSvg) {
    button.dataset.originalSvg = svg.innerHTML;
  }

  const performCopy = () => {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    } else {
      // Fallback para contextos não seguros (sem HTTPS ou localhost)
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      textArea.style.left = "-999999px";
      textArea.style.top = "-999999px";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
        document.body.removeChild(textArea);
        return Promise.resolve();
      } catch (err) {
        document.body.removeChild(textArea);
        return Promise.reject(err);
      }
    }
  };

  performCopy().then(() => {
    // Feedback visual: ícone de checkmark
    svg.innerHTML = '<polyline points="20 6 9 17 4 12"></polyline>';
    button.classList.add('copied');

    if (button.copyTimeout) {
      clearTimeout(button.copyTimeout);
    }

    button.copyTimeout = setTimeout(() => {
      svg.innerHTML = button.dataset.originalSvg;
      button.classList.remove('copied');
      button.copyTimeout = null;
    }, 1000);
  }).catch(err => {
    console.error('Erro ao copiar para a área de transferência: ', err);
  });
}

// =============================================================================
// Calendário & Tooltips Globais (Navegação SPA/HTMX)
// =============================================================================

let currentCalendarFp = null;

async function updateCalendarTooltips(fp) {
  if (!fp || !fp.calendarContainer || !document.body.contains(fp.calendarContainer)) return;
  currentCalendarFp = fp;
  
  const year = fp.currentYear;
  const month = fp.currentMonth + 1;
  
  try {
    const res = await fetch(`/api/v1/atividades/resumo-calendario?year=${year}&month=${month}`);
    if (!res.ok) return;
    const stats = await res.json();
    
    const dayElems = fp.calendarContainer.querySelectorAll('.flatpickr-day');
    dayElems.forEach(dayElem => {
      if (!dayElem.dateObj) return;
      
      const d = dayElem.dateObj;
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const dayStr = String(d.getDate()).padStart(2, '0');
      const dateKey = `${y}-${m}-${dayStr}`;
      
      const dayData = stats[dateKey];
      let tooltipText = "";
      let tooltipHtml = "";
      if (dayData && dayData.total_atividades > 0) {
        const totalMins = dayData.minutos || 0;
        const h = Math.floor(totalMins / 60);
        const minRem = totalMins % 60;
        
        let horasStr = "";
        if (h > 0 && minRem > 0) {
          horasStr = `${h}h ${minRem}m`;
        } else if (h > 0) {
          horasStr = `${h}h`;
        } else {
          horasStr = `${minRem}m`;
        }
        
        const atvStr = dayData.total_atividades === 1 ? "1 atividade" : `${dayData.total_atividades} atividades`;
        
        let statusBadge = "";
        if (dayData.nao_lancadas > 0) {
          const naoLancStr = dayData.nao_lancadas === 1 ? "1 pendente" : `${dayData.nao_lancadas} pendentes`;
          statusBadge = `<span class="tooltip-badge tooltip-badge-warning">${naoLancStr}</span>`;
        } else {
          statusBadge = `<span class="tooltip-badge tooltip-badge-success">Lançado</span>`;
        }
        
        tooltipHtml = `
          <div class="tooltip-header">
            <span class="tooltip-time">⏱️ ${horasStr}</span>
            <span class="tooltip-count">• ${atvStr}</span>
          </div>
          <div class="tooltip-footer">
            ${statusBadge}
          </div>
        `;
        tooltipText = `${horasStr}, ${atvStr}`;
      } else {
        tooltipHtml = `<div class="tooltip-empty">Sem atividades</div>`;
        tooltipText = "0h, 0 atividades";
      }
      
      dayElem.setAttribute('data-tooltip-html', tooltipHtml);
      dayElem.setAttribute('data-tooltip', tooltipText);
      dayElem.setAttribute('title', tooltipText);

      // Fundo colorido do dia de acordo com o status dos lançamentos
      dayElem.classList.remove('day-status-pending', 'day-status-launched');
      if (dayData && dayData.total_atividades > 0) {
        if (dayData.nao_lancadas > 0) {
          dayElem.classList.add('day-status-pending');
        } else {
          dayElem.classList.add('day-status-launched');
        }
      }
    });
  } catch(e) {
    console.error("Erro ao carregar tooltips do calendário:", e);
  }
}

function refreshExpediente(dateStr) {
  if (window.htmx && document.getElementById('expediente-container')) {
    htmx.ajax('GET', '/htmx/expediente', {
      values: { data_ref: dateStr },
      target: '#expediente-container'
    });
  }
}

function initInlineCalendar() {
  const input = document.getElementById("inline-calendar");
  if (!input || !input.parentNode) return;

  if (input._flatpickr && input._flatpickr.calendarContainer && document.body.contains(input._flatpickr.calendarContainer)) {
    updateCalendarTooltips(input._flatpickr);
    return;
  }

  const defaultDateVal = input.value || "today";

  const fp = flatpickr(input, {
    inline: true,
    locale: "pt",
    defaultDate: defaultDateVal,
    onReady: function(selectedDates, dateStr, instance) {
      let currentVal = input.value;
      if (!currentVal && selectedDates.length > 0) {
        currentVal = instance.formatDate(selectedDates[0], "Y-m-d");
        input.value = currentVal;
      }
      if (currentVal && window.htmx) {
        htmx.ajax('GET', '/htmx/atividades/calendario', {
          values: { data_ref: currentVal },
          target: '#timeline-list'
        });
        refreshExpediente(currentVal);
      }
      updateCalendarTooltips(instance);
    },
    onChange: function(selectedDates, dateStr, instance) {
      input.value = dateStr;
      if (window.htmx) {
        htmx.ajax('GET', '/htmx/atividades/calendario', {
          values: { data_ref: dateStr },
          target: '#timeline-list'
        });
        refreshExpediente(dateStr);
      }
    },
    onMonthChange: function(selectedDates, dateStr, instance) {
      updateCalendarTooltips(instance);
    },
    onYearChange: function(selectedDates, dateStr, instance) {
      updateCalendarTooltips(instance);
    }
  });

  currentCalendarFp = fp;
}

window.initInlineCalendar = initInlineCalendar;
window.refreshExpediente = refreshExpediente;

// Visual Tooltip popup element & position handler
let calendarTooltipEl = null;

function getOrCreateCalendarTooltip() {
  if (!calendarTooltipEl) {
    calendarTooltipEl = document.createElement('div');
    calendarTooltipEl.className = 'calendar-day-tooltip';
    document.body.appendChild(calendarTooltipEl);
  }
  return calendarTooltipEl;
}

document.addEventListener('mouseover', function(e) {
  const dayElem = e.target.closest('.flatpickr-day');
  if (dayElem && (dayElem.hasAttribute('data-tooltip-html') || dayElem.hasAttribute('data-tooltip'))) {
    const html = dayElem.getAttribute('data-tooltip-html') || dayElem.getAttribute('data-tooltip');
    if (!html) return;
    
    const tooltip = getOrCreateCalendarTooltip();
    tooltip.innerHTML = html;
    tooltip.style.display = 'block';
    
    const rect = dayElem.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
    let top = rect.top - tooltipRect.height - 8;
    
    if (left < 10) left = 10;
    if (left + tooltipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tooltipRect.width - 10;
    }
    if (top < 10) {
      top = rect.bottom + 8;
    }
    
    tooltip.style.left = `${left + window.scrollX}px`;
    tooltip.style.top = `${top + window.scrollY}px`;
  }
});

document.addEventListener('mouseout', function(e) {
  const dayElem = e.target.closest('.flatpickr-day');
  if (dayElem && calendarTooltipEl) {
    calendarTooltipEl.style.display = 'none';
  }
});

