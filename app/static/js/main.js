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

    // Chamado Picker — abrir
    if (e.target.closest('#chamado-picker-trigger')) {
      openChamadoPicker();
    }

    // Chamado Picker — fechar overlay
    if (e.target.closest('#chamado-picker-close')) {
      closeChamadoPicker();
    }

    // Chamado Picker — fechar ao clicar no fundo (overlay)
    if (e.target.id === 'chamado-picker-overlay') {
      closeChamadoPicker();
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

  // Auto-expand on HTMX swap e inicialização de componentes
  document.body.addEventListener('htmx:afterSwap', function(evt) {
    const target = evt.detail.target;
    
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
  });

  // HTMX Helper: Handle 400 and 422 errors globally
  document.body.addEventListener('htmx:beforeOnLoad', function (evt) {
    const status = evt.detail.xhr.status;
    if (status === 400 || status === 422) {
      const errorDiv = document.getElementById('form-error');
      if (errorDiv) {
        if (status === 422) {
          errorDiv.innerText = "Dados inválidos: verifique os formatos de hora (00:00 - 23:59).";
        } else {
          errorDiv.innerText = evt.detail.xhr.responseText;
        }
        errorDiv.style.display = 'block';
        
        // Reset loading button if needed
        const submitBtn = document.querySelector('form button[type="submit"]');
        if (submitBtn) submitBtn.classList.remove('htmx-request');
      }
    }
  }, true);

  // Listener para fechar o modal via trigger do servidor (HX-Trigger: closeModal)
  document.body.addEventListener('closeModal', function() {
    const modal = document.getElementById('global-modal');
    if (modal) modal.classList.remove('active');
  });

  // HTMX Helper: Handle 400 errors globally
  document.body.addEventListener('htmx:beforeOnLoad', function (evt) {
    if (evt.detail.xhr.status === 400) {
      const errorDiv = document.getElementById('form-error');
      if (errorDiv) {
        errorDiv.innerText = evt.detail.xhr.responseText;
        errorDiv.style.display = 'block';
      }
    }
  });

  // Global Keydown: Focus Trap for active modals
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
      // Busca todos os overlays que estão ativos/visíveis
      const overlays = Array.from(document.querySelectorAll('.modal-overlay.active, .chamado-picker-overlay')).filter(el => {
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
// Chamado Picker — funções globais
// =============================================================================

function openChamadoPicker() {
  const overlay = document.getElementById('chamado-picker-overlay');
  if (!overlay) return;

  overlay.style.display = 'flex';

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
  const overlay = document.getElementById('chamado-picker-overlay');
  if (overlay) overlay.style.display = 'none';
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
