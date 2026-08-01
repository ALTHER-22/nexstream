/**
 * =============================================================================
 * NEXSTREAM — JavaScript Principal
 * =============================================================================
 * Archivo: app/static/js/nexstream.js
 * Descripción: Motor JavaScript de la plataforma NEXSTREAM.
 *              ES2026 moderno, sin dependencias externas.
 *
 * Módulos incluidos:
 *   1. NexApp         — Controlador principal (init)
 *   2. NexTheme       — Dark/Light mode con localStorage
 *   3. NexNavbar      — Navbar scroll behavior y mobile menu
 *   4. NexSearch      — Overlay de búsqueda con debounce
 *   5. NexToast       — Sistema de notificaciones toast
 *   6. NexReveal      — Intersection Observer para animaciones
 *   7. NexSlider      — Sliders de contenido horizontales
 *   8. NexBackToTop   — Botón volver arriba
 *   9. NexFlash       — Auto-dismiss de flash messages
 *  10. NexCSRF        — Inyectar token CSRF en peticiones AJAX
 * =============================================================================
 */

'use strict';

/* ─────────────────────────────────────────────────────────────────────────────
   1. NexTheme — Sistema de temas Dark/Light
   ───────────────────────────────────────────────────────────────────────────── */

const NexTheme = (() => {
  const init = () => {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('nex-theme', 'dark');
  };
  return { init, apply: () => {}, toggle: () => {}, getCurrent: () => 'dark' };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   2. NexNavbar — Comportamiento de la navbar al hacer scroll
   ───────────────────────────────────────────────────────────────────────────── */

const NexNavbar = (() => {
  let navbar = null;
  let lastScrollY = 0;
  let ticking = false;

  /** Actualizar clases de la navbar según el scroll */
  const _updateNavbar = () => {
    const scrollY = window.scrollY;

    if (scrollY > 80) {
      navbar.classList.remove('transparent');
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.add('transparent');
      navbar.classList.remove('scrolled');
    }

    // Ocultar navbar al hacer scroll down rápido (opcional)
    // if (scrollY > lastScrollY && scrollY > 200) {
    //   navbar.style.transform = 'translateY(-100%)';
    // } else {
    //   navbar.style.transform = 'translateY(0)';
    // }

    lastScrollY = scrollY;
    ticking = false;
  };

  /** Inicializar menú mobile */
  const _initMobileMenu = () => {
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const closeBtn  = document.getElementById('mobileMenuClose');
    const menu      = document.getElementById('mobileMenu');
    const overlay   = document.getElementById('globalOverlay');

    if (!toggleBtn || !menu) return;

    const open = () => {
      menu.classList.add('open');
      toggleBtn.classList.add('open');
      overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      toggleBtn.setAttribute('aria-expanded', 'true');
      menu.setAttribute('aria-hidden', 'false');
      // Focus trap: enfocar el primer elemento del menú
      menu.querySelector('a, button')?.focus();
    };

    const close = () => {
      menu.classList.remove('open');
      toggleBtn.classList.remove('open');
      overlay.classList.remove('active');
      document.body.style.overflow = '';
      toggleBtn.setAttribute('aria-expanded', 'false');
      menu.setAttribute('aria-hidden', 'true');
    };

    toggleBtn.addEventListener('click', open);
    closeBtn?.addEventListener('click', close);
    overlay.addEventListener('click', close);

    // Cerrar con ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && menu.classList.contains('open')) close();
    });
  };

  /** Inicializar dropdown de usuario */
  const _initDropdowns = () => {
    document.querySelectorAll('.nex-dropdown').forEach(dropdown => {
      const toggle = dropdown.querySelector('button');
      const menu   = dropdown.querySelector('.nex-dropdown__menu');
      if (!toggle || !menu) return;

      toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = dropdown.classList.contains('active');
        // Cerrar todos los demás dropdowns
        document.querySelectorAll('.nex-dropdown.active').forEach(d => d.classList.remove('active'));
        if (!isOpen) {
          dropdown.classList.add('active');
          toggle.setAttribute('aria-expanded', 'true');
        }
      });
    });

    // Cerrar dropdowns al hacer click fuera
    document.addEventListener('click', () => {
      document.querySelectorAll('.nex-dropdown.active').forEach(d => {
        d.classList.remove('active');
        d.querySelector('button')?.setAttribute('aria-expanded', 'false');
      });
    });
  };

  const init = () => {
    navbar = document.getElementById('mainNavbar');
    if (!navbar) return;

    // Scroll listener optimizado con requestAnimationFrame
    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(_updateNavbar);
        ticking = true;
      }
    }, { passive: true });

    // Estado inicial
    _updateNavbar();
    _initMobileMenu();
    _initDropdowns();
  };

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   3. NexSearch — Overlay de búsqueda con debounce y resultados en tiempo real
   ───────────────────────────────────────────────────────────────────────────── */

const NexSearch = (() => {
  let overlay, input, results, hint, clearBtn;
  let searchTimeout = null;
  const MIN_CHARS = 2;
  const DEBOUNCE_MS = 300;

  /** Abrir el overlay de búsqueda */
  const open = () => {
    overlay.classList.add('active');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    // Pequeño delay para que la transición se vea
    setTimeout(() => input?.focus(), 100);
    document.getElementById('searchToggle')?.setAttribute('aria-expanded', 'true');
  };

  /** Cerrar el overlay */
  const close = () => {
    overlay.classList.remove('active');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (input) input.value = '';
    _clearResults();
    document.getElementById('searchToggle')?.setAttribute('aria-expanded', 'false');
  };

  /** Ejecutar búsqueda en la API */
  const _search = async (query) => {
    if (query.length < MIN_CHARS) {
      _clearResults();
      return;
    }

    // Mostrar skeleton mientras carga
    _showSkeleton();

    try {
      // Obtener token CSRF
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

      const response = await fetch(`/api/v1/search?q=${encodeURIComponent(query)}`, {
        headers: {
          'X-CSRF-TOKEN': csrfToken || '',
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      _renderResults(data, query);

    } catch (error) {
      console.warn('Error en búsqueda:', error);
      _renderError();
    }
  };

  /** Renderizar resultados */
  const _renderResults = (data, query) => {
    const total = (data.series?.length || 0) + (data.movies?.length || 0);

    if (total === 0) {
      results.innerHTML = `
        <div class="nex-search-overlay__empty">
          <p>Sin resultados para "<strong>${_escapeHtml(query)}</strong>"</p>
          <p style="font-size:0.875rem; color:var(--color-text-muted); margin-top:0.5rem;">
            Intenta con otro término o revisa la ortografía.
          </p>
        </div>`;
      return;
    }

    let html = `<div class="nex-search-overlay__count">${total} resultado${total !== 1 ? 's' : ''} para "<strong>${_escapeHtml(query)}</strong>"</div>`;

    if (data.series?.length) {
      html += `<div class="nex-search-overlay__section-title">Series</div>`;
      html += `<div class="nex-search-overlay__list">`;
      data.series.forEach(item => { html += _renderResultItem(item, 'series'); });
      html += `</div>`;
    }

    if (data.movies?.length) {
      html += `<div class="nex-search-overlay__section-title">Películas</div>`;
      html += `<div class="nex-search-overlay__list">`;
      data.movies.forEach(item => { html += _renderResultItem(item, 'movie'); });
      html += `</div>`;
    }

    results.innerHTML = html;
    hint.style.display = 'none';
  };

  /** Renderizar un ítem de resultado */
  const _renderResultItem = (item, type) => `
    <a href="/${type === 'series' ? 'serie' : 'pelicula'}/${item.slug}" class="nex-search-result-item" onclick="NexSearch.close()">
      <div class="nex-search-result-item__img">
        <img src="${item.cover_url || '/static/images/default-cover.webp'}"
             alt="${_escapeHtml(item.title)}" loading="lazy" width="40" height="60">
      </div>
      <div class="nex-search-result-item__info">
        <span class="nex-search-result-item__title">${_escapeHtml(item.title)}</span>
        <span class="nex-search-result-item__meta">
          ${item.year || ''}
          ${item.year && item.rating_avg ? ' · ' : ''}
          ${item.rating_avg ? `⭐ ${Number(item.rating_avg).toFixed(1)}` : ''}
        </span>
      </div>
      <span class="nex-badge nex-badge--${type === 'series' ? 'primary' : 'hd'}" style="flex-shrink:0;">
        ${type === 'series' ? 'Serie' : 'Película'}
      </span>
    </a>`;

  const _showSkeleton = () => {
    results.innerHTML = Array(4).fill(0).map(() => `
      <div class="nex-search-result-item">
        <div class="skeleton" style="width:40px;height:60px;border-radius:4px;flex-shrink:0;"></div>
        <div style="flex:1;display:flex;flex-direction:column;gap:8px;">
          <div class="skeleton" style="height:14px;width:60%;border-radius:4px;"></div>
          <div class="skeleton" style="height:12px;width:40%;border-radius:4px;"></div>
        </div>
      </div>`).join('');
    hint.style.display = 'none';
  };

  const _clearResults = () => {
    results.innerHTML = '';
    hint.style.display = 'block';
  };

  const _renderError = () => {
    results.innerHTML = `<div class="nex-search-overlay__empty"><p>Error al buscar. Intenta de nuevo.</p></div>`;
  };

  /** Escapar HTML para prevenir XSS */
  const _escapeHtml = (str) => {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str || ''));
    return div.innerHTML;
  };

  const init = () => {
    overlay  = document.getElementById('searchOverlay');
    input    = document.getElementById('searchInput');
    results  = document.getElementById('searchResults');
    hint     = document.getElementById('searchHint');
    clearBtn = document.getElementById('searchClear');

    if (!overlay || !input) return;

    // Botón de abrir búsqueda
    document.getElementById('searchToggle')?.addEventListener('click', open);
    document.getElementById('searchClose')?.addEventListener('click', close);

    // Input con debounce
    input.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      clearBtn.style.display = query ? 'block' : 'none';
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => _search(query), DEBOUNCE_MS);
    });

    // Botón limpiar
    clearBtn?.addEventListener('click', () => {
      input.value = '';
      clearBtn.style.display = 'none';
      _clearResults();
      input.focus();
    });

    // Cerrar con ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && overlay.classList.contains('active')) close();
      // Abrir búsqueda con Ctrl+K o /
      if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && document.activeElement.tagName !== 'INPUT')) {
        e.preventDefault();
        open();
      }
    });

    // Cerrar al hacer click fuera del contenido
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });
  };

  return { init, open, close };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   4. NexToast — Sistema de notificaciones toast
   ───────────────────────────────────────────────────────────────────────────── */

const NexToast = (() => {
  let container = null;

  const ICONS = {
    success: '✅',
    error:   '❌',
    warning: '⚠️',
    info:    'ℹ️',
  };

  /**
   * Mostrar un toast
   * @param {string} message - Mensaje a mostrar
   * @param {string} type    - 'success' | 'error' | 'warning' | 'info'
   * @param {number} duration - Duración en ms (0 = permanente)
   */
  const show = (message, type = 'info', duration = 5000) => {
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `nex-toast nex-toast--${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML = `
      <div class="nex-toast__icon" aria-hidden="true">${ICONS[type] || ICONS.info}</div>
      <div class="nex-toast__body">
        <p class="nex-toast__message">${message}</p>
      </div>
      <button class="nex-toast__close" onclick="this.closest('.nex-toast').remove()" aria-label="Cerrar notificación">✕</button>`;

    container.appendChild(toast);

    // Auto-dismiss
    if (duration > 0) {
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
      }, duration);
    }
  };

  const success = (msg, duration) => show(msg, 'success', duration);
  const error   = (msg, duration) => show(msg, 'error',   duration);
  const warning = (msg, duration) => show(msg, 'warning', duration);
  const info    = (msg, duration) => show(msg, 'info',    duration);

  const init = () => {
    // Crear o usar contenedor existente
    container = document.querySelector('.nex-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'nex-toast-container';
      container.setAttribute('aria-label', 'Notificaciones');
      document.body.appendChild(container);
    }
  };

  return { init, show, success, error, warning, info };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   5. NexReveal — Intersection Observer para animaciones al hacer scroll
   ───────────────────────────────────────────────────────────────────────────── */

const NexReveal = (() => {
  let observer = null;

  const init = () => {
    // Respetar preferencia de reducción de movimiento
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.querySelectorAll('.reveal').forEach(el => el.classList.add('revealed'));
      return;
    }

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            observer.unobserve(entry.target); // Animar solo una vez
          }
        });
      },
      {
        threshold: 0.1,    // 10% del elemento visible
        rootMargin: '0px 0px -50px 0px', // Trigger 50px antes del viewport
      }
    );

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
  };

  /** Observar nuevos elementos añadidos dinámicamente */
  const observe = (element) => {
    observer?.observe(element);
  };

  return { init, observe };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   6. NexSlider — Sliders horizontales de contenido
   ───────────────────────────────────────────────────────────────────────────── */

const NexSlider = (() => {

  const _initSlider = (slider) => {
    const track   = slider.querySelector('.nex-slider__track');
    const prevBtn = slider.querySelector('.nex-slider__btn--prev');
    const nextBtn = slider.querySelector('.nex-slider__btn--next');

    if (!track) return;

    /** Calcular cantidad de scroll por click (75% del ancho visible) */
    const getScrollAmount = () => track.clientWidth * 0.75;

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        track.scrollBy({ left: -getScrollAmount(), behavior: 'smooth' });
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        track.scrollBy({ left: getScrollAmount(), behavior: 'smooth' });
      });
    }

    // Actualizar visibilidad de botones según la posición del scroll
    const updateButtons = () => {
      if (prevBtn) prevBtn.style.opacity = track.scrollLeft > 0 ? '1' : '0';
      if (nextBtn) {
        const atEnd = track.scrollLeft >= track.scrollWidth - track.clientWidth - 10;
        nextBtn.style.opacity = atEnd ? '0' : '1';
      }
    };

    track.addEventListener('scroll', updateButtons, { passive: true });
    updateButtons();

    // Soporte para scroll con mouse wheel horizontal eliminado por problemas de UX (bloqueaba el scroll vertical de la página)
  };

  const init = () => {
    document.querySelectorAll('.nex-slider').forEach(_initSlider);
  };

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   7. NexBackToTop — Botón volver arriba
   ───────────────────────────────────────────────────────────────────────────── */

const NexBackToTop = (() => {
  let btn = null;
  let ticking = false;

  const init = () => {
    btn = document.getElementById('backToTop');
    if (!btn) return;

    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          btn.classList.toggle('visible', window.scrollY > 400);
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });

    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  };

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   8. NexFlash — Auto-dismiss de mensajes flash de Flask
   ───────────────────────────────────────────────────────────────────────────── */

const NexFlash = (() => {
  const init = () => {
    document.querySelectorAll('[data-auto-dismiss]').forEach(toast => {
      const delay = parseInt(toast.dataset.autoDismiss, 10) || 5000;
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
      }, delay);
    });
  };

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   9. NexCSRF — Inyectar token CSRF en todas las peticiones AJAX
   ───────────────────────────────────────────────────────────────────────────── */

const NexCSRF = (() => {
  let token = null;

  const getToken = () => {
    if (!token) {
      token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }
    return token;
  };

  /**
   * Wrapper de fetch con CSRF automático
   * Úsalo en lugar de fetch() para peticiones POST/PUT/PATCH/DELETE
   */
  const fetchWithCSRF = (url, options = {}) => {
    const csrfToken = getToken();
    const headers = {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...options.headers,
    };

    if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method?.toUpperCase())) {
      headers['X-CSRFToken'] = csrfToken;
    }

    return fetch(url, { ...options, headers });
  };

  const init = () => {
    // Hacer disponible globalmente para formularios y componentes
    window.nexFetch = fetchWithCSRF;
  };

  return { init, getToken, fetchWithCSRF };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   10. NexLazyLoad — Lazy loading de imágenes con IntersectionObserver
   ───────────────────────────────────────────────────────────────────────────── */

const NexLazyLoad = (() => {
  let observer = null;

  const init = () => {
    // Usar loading="lazy" nativo si está disponible (Chrome, Firefox, Edge)
    if ('loading' in HTMLImageElement.prototype) {
      document.querySelectorAll('img[data-src]').forEach(img => {
        img.src = img.dataset.src;
        if (img.dataset.srcset) img.srcset = img.dataset.srcset;
      });
      return;
    }

    // Fallback: IntersectionObserver
    observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
          }
          if (img.dataset.srcset) {
            img.srcset = img.dataset.srcset;
            img.removeAttribute('data-srcset');
          }
          img.classList.add('loaded');
          observer.unobserve(img);
        }
      });
    }, { rootMargin: '200px 0px' }); // Cargar 200px antes de entrar en pantalla

    document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
  };

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────────────────
   NEXAPP — Controlador Principal
   Inicializa todos los módulos cuando el DOM esté listo.
   ───────────────────────────────────────────────────────────────────────────── */

const NexApp = (() => {

  const init = () => {
    // Orden importante: tema primero para evitar flash
    NexTheme.init();
    NexNavbar.init();
    NexSearch.init();
    NexToast.init();
    NexReveal.init();
    NexSlider.init();
    NexBackToTop.init();
    NexFlash.init();
    NexCSRF.init();
    NexLazyLoad.init();

    console.log('%cNEXSTREAM v2.0.0 🎬', 'color:#e50914; font-weight:900; font-size:16px;');
  };

  return { init };
})();

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', NexApp.init);
} else {
  NexApp.init(); // DOM ya está listo
}

// Exponer módulos globalmente para uso en templates y otros scripts
window.NexStream = {
  Theme:      NexTheme,
  Navbar:     NexNavbar,
  Search:     NexSearch,
  Toast:      NexToast,
  Reveal:     NexReveal,
  Slider:     NexSlider,
  BackToTop:  NexBackToTop,
  Flash:      NexFlash,
  CSRF:       NexCSRF,
  LazyLoad:   NexLazyLoad,
};
