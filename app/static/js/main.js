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

  // Auto-expand on HTMX swap
  document.body.addEventListener('htmx:afterSwap', function(evt) {
    const textareas = evt.detail.target.querySelectorAll('textarea.form-control');
    textareas.forEach(autoExpandTextarea);
  });
});

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
