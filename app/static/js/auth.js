/**
 * =============================================================================
 * NEXSTREAM — JavaScript de Autenticación
 * =============================================================================
 * Archivo: app/static/js/auth.js
 * Descripción: Lógica de los formularios de autenticación.
 *
 * Funcionalidades:
 *   - Toggle mostrar/ocultar contraseña
 *   - Indicador de fortaleza de contraseña en tiempo real
 *   - Validación de coincidencia de contraseñas
 *   - Verificación de username disponible (AJAX con debounce)
 *   - Verificación de email disponible (AJAX con debounce)
 *   - Animaciones de estados de los inputs
 *   - Prevención de doble submit
 * =============================================================================
 */

'use strict';

/* ─── Toggle mostrar/ocultar contraseña ──────────────────────────────────────── */

/**
 * Inicializar botones de toggle de contraseña.
 * Busca pares (botón, input) por convención de IDs.
 */
const initPasswordToggles = () => {
  const pairs = [
    ['toggleLoginPwd',   'loginPassword'],
    ['toggleRegPwd',     'registerPassword'],
    ['toggleRegPwd2',    'registerPassword2'],
    ['toggleResetPwd',   'resetPassword'],
    ['toggleResetPwd2',  'resetPassword2'],
  ];

  pairs.forEach(([btnId, inputId]) => {
    const btn   = document.getElementById(btnId);
    const input = document.getElementById(inputId);
    if (!btn || !input) return;

    btn.addEventListener('click', () => {
      const isText  = input.type === 'text';
      input.type    = isText ? 'password' : 'text';
      btn.textContent = isText ? '👁' : '🙈';
      btn.setAttribute('aria-label', isText ? 'Mostrar contraseña' : 'Ocultar contraseña');
      input.focus();
    });
  });
};


/* ─── Indicador de fortaleza de contraseña ───────────────────────────────────── */

/**
 * Analiza una contraseña y retorna un objeto con su fortaleza.
 * @param {string} password
 * @returns {{ score: number, level: string, rules: object }}
 */
const analyzePassword = (password) => {
  const rules = {
    length: password.length >= 8,
    upper:  /[A-Z]/.test(password),
    lower:  /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };

  const score = Object.values(rules).filter(Boolean).length;

  let level;
  if (score <= 1)     level = 'weak';
  else if (score <= 2) level = 'fair';
  else if (score <= 3) level = 'good';
  else                 level = 'strong';

  return { score, level, rules };
};

/**
 * Actualizar UI del indicador de fortaleza.
 */
const updateStrengthIndicator = (password) => {
  const container = document.getElementById('pwdStrength');
  const fill      = document.getElementById('pwdStrengthFill');
  if (!container || !fill) return;

  if (!password) {
    container.style.display = 'none';
    return;
  }

  container.style.display = 'block';
  const { level, rules } = analyzePassword(password);

  // Actualizar barra
  fill.className = `nex-pwd-strength__fill ${level}`;

  // Actualizar reglas individuales
  const ruleMap = {
    'rule-length': rules.length,
    'rule-upper':  rules.upper,
    'rule-lower':  rules.lower,
    'rule-number': rules.number,
  };

  Object.entries(ruleMap).forEach(([id, met]) => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('met', met);
  });
};

const initPasswordStrength = () => {
  // Puede estar en el form de registro o de reset
  const pwdInput = document.getElementById('registerPassword') ||
                   document.getElementById('resetPassword');
  if (!pwdInput) return;

  pwdInput.addEventListener('input', (e) => {
    updateStrengthIndicator(e.target.value);
  });
};


/* ─── Validación de coincidencia de contraseñas ──────────────────────────────── */

const initPasswordMatch = () => {
  const pwd1 = document.getElementById('registerPassword') ||
               document.getElementById('resetPassword');
  const pwd2 = document.getElementById('registerPassword2') ||
               document.getElementById('resetPassword2');
  const msg  = document.getElementById('pwdMatchMsg');

  if (!pwd1 || !pwd2 || !msg) return;

  const check = () => {
    const v1 = pwd1.value;
    const v2 = pwd2.value;

    if (!v2) {
      msg.textContent = '';
      msg.className = 'nex-auth-field-msg';
      pwd2.classList.remove('is-valid', 'is-invalid');
      return;
    }

    if (v1 === v2) {
      msg.textContent = '✓ Las contraseñas coinciden';
      msg.className = 'nex-auth-field-msg success';
      pwd2.classList.add('is-valid');
      pwd2.classList.remove('is-invalid');
    } else {
      msg.textContent = '✗ Las contraseñas no coinciden';
      msg.className = 'nex-auth-field-msg error';
      pwd2.classList.add('is-invalid');
      pwd2.classList.remove('is-valid');
    }
  };

  pwd1.addEventListener('input', check);
  pwd2.addEventListener('input', check);
};


/* ─── Verificación de username en tiempo real (AJAX) ─────────────────────────── */

const initUsernameCheck = () => {
  const input  = document.getElementById('registerUsername');
  const status = document.getElementById('usernameStatus');
  if (!input || !status) return;

  let debounceTimer = null;
  let lastChecked   = '';

  const check = async (username) => {
    if (username === lastChecked) return;
    lastChecked = username;

    if (username.length < 3) {
      status.textContent = '';
      input.classList.remove('is-valid', 'is-invalid');
      return;
    }

    // Indicar que está verificando
    status.textContent = 'Verificando...';
    status.style.color = 'var(--color-text-muted)';
    input.classList.remove('is-valid', 'is-invalid');

    try {
      const res  = await fetch(`/auth/check-username?username=${encodeURIComponent(username)}`);
      const data = await res.json();

      if (data.available) {
        status.textContent = '✓ ' + data.message;
        status.style.color = '#10b981';
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
      } else {
        status.textContent = '✗ ' + data.message;
        status.style.color = '#ef4444';
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
      }
    } catch {
      status.textContent = '';
    }
  };

  input.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => check(e.target.value.trim().toLowerCase()), 400);
  });
};


/* ─── Verificación de email en tiempo real (AJAX) ────────────────────────────── */

const initEmailCheck = () => {
  const input  = document.getElementById('registerEmail');
  const status = document.getElementById('emailStatus');
  if (!input || !status) return;

  let debounceTimer = null;

  const check = async (email) => {
    if (!email.includes('@') || !email.includes('.')) {
      status.textContent = '';
      input.classList.remove('is-valid', 'is-invalid');
      return;
    }

    try {
      const res  = await fetch(`/auth/check-email?email=${encodeURIComponent(email)}`);
      const data = await res.json();

      if (data.available) {
        status.textContent = '';
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
      } else {
        status.textContent = '✗ ' + data.message;
        status.style.color = '#ef4444';
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
      }
    } catch {
      status.textContent = '';
    }
  };

  input.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => check(e.target.value.trim().toLowerCase()), 500);
  });
};


/* ─── Prevención de doble submit ─────────────────────────────────────────────── */

const initFormSubmit = () => {
  document.querySelectorAll('form[id$="Form"]').forEach(form => {
    const submitBtn = form.querySelector('[type="submit"]');
    if (!submitBtn) return;

    form.addEventListener('submit', (e) => {
      // Verificar validación HTML5 nativa
      if (!form.checkValidity()) return;

      // Verificar que las contraseñas coinciden (si aplica)
      const pwd2 = form.querySelector('#registerPassword2, #resetPassword2');
      if (pwd2 && pwd2.classList.contains('is-invalid')) {
        e.preventDefault();
        pwd2.focus();
        return;
      }

      // Deshabilitar botón para prevenir doble submit
      submitBtn.disabled = true;
      submitBtn.classList.add('loading');
      const btnText = submitBtn.querySelector('.btn-text');
      if (btnText) {
        btnText.textContent = 'Procesando...';
      }

      // Re-habilitar si el servidor tarda más de 10s (fallback)
      setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
        if (btnText) btnText.textContent = submitBtn.dataset.originalText || 'Enviar';
      }, 10000);
    });

    // Guardar texto original del botón
    const btnText = submitBtn.querySelector('.btn-text');
    if (btnText) submitBtn.dataset.originalText = btnText.textContent;
  });
};


/* ─── Animación de inputs ────────────────────────────────────────────────────── */

const initInputAnimations = () => {
  document.querySelectorAll('.nex-auth-input').forEach(input => {
    // Añadir clase al tener valor (para floating labels si se implementan)
    const checkValue = () => {
      input.classList.toggle('has-value', input.value.length > 0);
    };

    input.addEventListener('input', checkValue);
    input.addEventListener('change', checkValue);
    checkValue(); // Verificar al cargar (útil con autocompletado)
  });
};


/* ─── Inicialización ─────────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  initPasswordToggles();
  initPasswordStrength();
  initPasswordMatch();
  initUsernameCheck();
  initEmailCheck();
  initFormSubmit();
  initInputAnimations();

  console.log('%cNEXSTREAM Auth ✓', 'color:#10b981; font-weight:700;');
});
