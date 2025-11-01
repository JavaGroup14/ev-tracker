'use strict';

(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const form = $('#registrationForm');
  const successEl = $('#formSuccess');
  const yearEl = $('#year');
  const passwordInput = $('#password');
  const confirmPasswordInput = $('#confirmPassword');
  const passwordStrengthBar = $('#passwordStrength');
  const roleInput = $('#role');

  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  /* ================= Page Transition Overlay ================= */
  function ensureTransitionEl() {
    let el = $('#pageTransition');
    if (!el) {
      el = document.createElement('div');
      el.id = 'pageTransition';
      document.body.appendChild(el);
    }
    return el;
  }
  const transitionEl = ensureTransitionEl();
  function startTransition(x, y) {
    if (transitionEl) {
      if (typeof x === 'number' && typeof y === 'number') {
        transitionEl.style.setProperty('--tx', x + 'px');
        transitionEl.style.setProperty('--ty', y + 'px');
      }
      transitionEl.classList.add('active');
    }
  }
  function endTransition() {
    if (!transitionEl) return;
    transitionEl.classList.remove('active');
  }
  // End transition on DOM ready
  window.addEventListener('pageshow', () => setTimeout(endTransition, 50));
  document.addEventListener('DOMContentLoaded', () => {
    // enter animation
    document.body.classList.add('page-fade-enter');
    requestAnimationFrame(() => {
      document.body.classList.add('page-fade-enter-active');
    });
    setTimeout(() => {
      document.body.classList.remove('page-fade-enter', 'page-fade-enter-active');
    }, 380);
  });
  // Intercept navigations on buttons/links with [data-soft-nav]
  document.addEventListener('click', (e) => {
    const anchor = e.target.closest('a[data-soft-nav], button[data-soft-nav], form[data-soft-nav] button[type="submit"]');
    if (!anchor) return;
    const x = e.clientX, y = e.clientY;
    const href = anchor.getAttribute('href') || anchor.dataset.href;
    if (!href || href.startsWith('#')) return;
    e.preventDefault();
    startTransition(x, y);
    setTimeout(() => { window.location.href = href; }, 250);
  });

  // Role card selection
  const roleCards = $$('.role-card');
  roleCards.forEach((card) => {
    card.addEventListener('click', () => {
      // Remove selected state from all cards
      roleCards.forEach((c) => {
        c.classList.remove('ring-2', 'ring-primary-500/60', 'border-primary-500/60', 'bg-primary-500/10');
        const icon = c.querySelector('.w-12');
        icon.classList.remove('bg-primary-500/20', 'text-primary-400');
        icon.classList.add('bg-slate-500/20', 'text-slate-400');
      });

      // Add selected state to clicked card
      card.classList.add('ring-2', 'ring-primary-500/60', 'border-primary-500/60', 'bg-primary-500/10');
      const icon = card.querySelector('.w-12');
      icon.classList.remove('bg-slate-500/20', 'text-slate-400');
      icon.classList.add('bg-primary-500/20', 'text-primary-400');

      // Set the role value
      const role = card.getAttribute('data-role');
      if (roleInput) {
        roleInput.value = role;
      }

      // Clear any role validation errors
      clearError(roleInput);
    });
  });

  // Toggle password visibility
  $$('button[data-toggle-password]').forEach((btn) => {
    const target = btn.getAttribute('data-toggle-password');
    const input = target ? $(target) : null;
    if (!input) return;
    btn.addEventListener('click', () => {
      const isPassword = input.getAttribute('type') === 'password';
      input.setAttribute('type', isPassword ? 'text' : 'password');
      btn.setAttribute('aria-pressed', String(isPassword));
    });
  });

  // Basic validator helpers
  function setError(input, message) {
    const msg = document.querySelector(`[data-error-for="${input.id}"]`);
    if (msg) {
      msg.textContent = message;
      msg.classList.remove('hidden');
    }
    input.classList.add('ring-2', 'ring-rose-500/60', 'border-rose-500/60');
  }

  function clearError(input) {
    const msg = document.querySelector(`[data-error-for="${input.id}"]`);
    if (msg) {
      msg.textContent = '';
      msg.classList.add('hidden');
    }
    input.classList.remove('ring-2', 'ring-rose-500/60', 'border-rose-500/60');
  }

  function validateEmail(value) {
    // Checks for a general email pattern: local-part@domain
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(value);
  }

  function passwordScore(value) {
    let score = 0;
    if (!value) return 0;
    if (value.length >= 8) score += 1;
    if (/[A-Z]/.test(value)) score += 1;
    if (/[a-z]/.test(value)) score += 1;
    if (/[0-9]/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;
    return score; // 0-5
  }

  function updatePasswordStrength() {
    const value = passwordInput.value;
    const score = passwordScore(value);
    const widths = ['0%', '20%', '40%', '60%', '80%', '100%'];
    const colors = ['bg-rose-500', 'bg-rose-500', 'bg-amber-500', 'bg-yellow-500', 'bg-emerald-500', 'bg-emerald-600'];

    // Remove prior color classes
    passwordStrengthBar.classList.remove('bg-rose-500', 'bg-amber-500', 'bg-yellow-500', 'bg-emerald-500', 'bg-emerald-600');
    passwordStrengthBar.style.width = widths[score];
    passwordStrengthBar.classList.add(colors[score]);
  }

  function validateField(input) {
    clearError(input);
    const value = (input.value || '').trim();

    if (input.id === 'firstName' || input.id === 'lastName' || input.id === 'username') {
      if (value.length === 0) {
        setError(input, 'This field is required.');
        return false;
      }
      if (value.length < 2) {
        setError(input, 'Please enter at least 2 characters.');
        return false;
      }
      return true;
    }

    if (input.id === 'email') {
      if (!validateEmail(value)) {
        setError(input, 'Use a valid email');
        return false;
      }
      return true;
    }

    if (input.id === 'password') {
      if (value.length < 8) {
        setError(input, 'Password must be at least 8 characters long.');
        return false;
      }
      if (passwordScore(value) < 3) {
        setError(input, 'Use upper/lowercase, numbers and a symbol for strength.');
        return false;
      }
      return true;
    }

    if (input.id === 'confirmPassword') {
      if (value !== passwordInput.value) {
        setError(input, 'Passwords do not match.');
        return false;
      }
      return true;
    }

    if (input.id === 'role') {
      if (!value || value.trim() === '') {
        setError(input, 'Please select a role.');
        return false;
      }
      return true;
    }

    if (input.id === 'tos') {
      if (!input.checked) {
        setError(input, 'You must agree to continue.');
        return false;
      }
      return true;
    }

    return true;
  }

  if (passwordInput) {
    passwordInput.addEventListener('input', updatePasswordStrength);
  }

  // Live validation on blur
  $$('#registrationForm input, #registrationForm select').forEach((input) => {
    input.addEventListener('blur', () => validateField(input));
    input.addEventListener('input', () => clearError(input));
  });

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const inputs = [
        $('#username'),
        $('#password'),
        $('#confirmPassword'),
        $('#role')
      ].filter(Boolean);

      let valid = true;
      inputs.forEach((input) => {
        if (!validateField(input)) valid = false;
      });

      if (!valid) return;

      // Simulate submit latency
      const submitBtn = form.querySelector('button[type="submit"]');
      const prevText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M22 12a10 10 0 0 1-10 10"/></svg> Creating account...';

      try {
        await new Promise((res) => setTimeout(res, 900));
        
        // Show success message
        successEl?.classList.remove('hidden');
        form.reset();
        updatePasswordStrength();
        
        // Reset after showing success message
        setTimeout(() => {
          successEl?.classList.add('hidden');
        }, 3000);
      } catch (err) {
        console.error(err);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = prevText;
      }
    });
  }
})();

