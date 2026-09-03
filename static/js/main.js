/**
 * DIVYA TRADING CO. - Main Frontend JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Header scroll shadow
  const header = document.querySelector('.site-header');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      header?.classList.add('scrolled');
    } else {
      header?.classList.remove('scrolled');
    }
  });

  // 2. Modern Mobile Drawer Navigation Setup
  setupMobileDrawer();

  // 3. Guest Auth Prompt Modal Controls
  setupGuestAuthPrompt();

  // 4. Quick Single-Product Inquiry Modal Logic
  setupQuickInquiryModal();

  // 5. Client-Side Catalog Search & URL Filter Handler (for Static / GitHub Pages Mode)
  setupClientSideCatalogFilter();
});

/**
 * Mobile Drawer Navigation and Accordion Submenu Controller
 */
function setupMobileDrawer() {
  const toggleBtn = document.getElementById('mobileNavToggle');
  const drawer = document.getElementById('mobileDrawer');
  const overlay = document.getElementById('mobileDrawerOverlay');
  const closeBtn = document.getElementById('mobileDrawerCloseBtn');

  if (!toggleBtn || !drawer) return;

  const openDrawer = () => {
    drawer.classList.add('active');
    overlay?.classList.add('active');
    toggleBtn.classList.add('active');
    document.body.classList.add('drawer-open');
  };

  const closeDrawer = () => {
    drawer.classList.remove('active');
    overlay?.classList.remove('active');
    toggleBtn.classList.remove('active');
    document.body.classList.remove('drawer-open');
  };

  toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (drawer.classList.contains('active')) {
      closeDrawer();
    } else {
      openDrawer();
    }
  });

  closeBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    closeDrawer();
  });

  overlay?.addEventListener('click', (e) => {
    e.preventDefault();
    closeDrawer();
  });

  // Close drawer on clicking navigation links inside drawer
  drawer.querySelectorAll('.mobile-nav-row, .mobile-accordion-item, .btn-mobile-auth-login, .btn-mobile-auth-register, .btn-mobile-myquotes').forEach(link => {
    link.addEventListener('click', () => {
      closeDrawer();
    });
  });

  // Close drawer on ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer.classList.contains('active')) {
      closeDrawer();
    }
  });

  // Mobile Accordions inside Drawer
  const accordionHeaders = drawer.querySelectorAll('.mobile-accordion-header');
  accordionHeaders.forEach(header => {
    header.addEventListener('click', (e) => {
      e.stopPropagation();
      const parent = header.closest('.mobile-drawer-accordion');
      const isOpen = parent.classList.contains('open');
      
      // Close other accordions
      accordionHeaders.forEach(h => {
        h.closest('.mobile-drawer-accordion')?.classList.remove('open');
      });

      if (!isOpen) {
        parent.classList.add('open');
      }
    });
  });
}

/**
 * Toast Notification Utility
 */
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? '✓' : '⚠️';
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

let pendingInquiryAction = null;

/**
 * Guest Auth Suggestion Modal
 */
function setupGuestAuthPrompt() {
  const modal = document.getElementById('guestAuthPromptModal');
  const closeBtn = document.getElementById('closeGuestAuthModalBtn');
  const continueGuestBtn = document.getElementById('continueAsGuestBtn');

  if (!modal) return;

  const closeModal = () => modal.classList.remove('active');
  closeBtn?.addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  continueGuestBtn?.addEventListener('click', () => {
    closeModal();
    if (pendingInquiryAction) {
      pendingInquiryAction();
      pendingInquiryAction = null;
    }
  });
}

/**
 * Setup Single-Product Quick Inquiry Modal
 */
function setupQuickInquiryModal() {
  const modalOverlay = document.getElementById('quickInquiryModal');
  const closeBtn = document.getElementById('closeInquiryModalBtn');
  const form = document.getElementById('quickInquiryForm');

  if (!modalOverlay || !form) return;

  async function loadModalCaptcha() {
    try {
      const res = await fetch('/api/captcha/generate');
      const data = await res.json();
      const qEl = document.getElementById('quickInqCaptchaQ');
      if (qEl) qEl.textContent = data.question;
    } catch (e) {}
  }
  window.loadModalCaptcha = loadModalCaptcha;

  const openInquiryModalForProduct = (btn) => {
    const productId = btn.dataset.productId || '';
    const productName = btn.dataset.productName || 'Precision Spare Part';
    const partNumber = btn.dataset.partNumber || '';
    const repeatSizes = btn.dataset.repeatSizes || '';

    document.getElementById('inqProductId').value = productId;
    document.getElementById('inqProductNameDisplay').textContent = productName;
    document.getElementById('inqPartNoDisplay').textContent = partNumber ? `Part No: ${partNumber}` : '';
    
    const repeatNotesField = document.getElementById('inqRepeatNotes');
    if (repeatNotesField && repeatSizes) {
      repeatNotesField.placeholder = `e.g. ${repeatSizes}`;
    }

    loadModalCaptcha();
    modalOverlay.classList.add('active');
  };

  // Open modal from product buttons
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-quick-inquire');
    if (btn) {
      e.preventDefault();
      const isLoggedIn = document.body.dataset.loggedIn === 'true';
      const guestModal = document.getElementById('guestAuthPromptModal');

      if (!isLoggedIn && guestModal && !sessionStorage.getItem('dtc_guest_prompt_seen')) {
        sessionStorage.setItem('dtc_guest_prompt_seen', '1');
        pendingInquiryAction = () => openInquiryModalForProduct(btn);
        guestModal.classList.add('active');
      } else {
        openInquiryModalForProduct(btn);
      }
    }
  });

  // Close modal
  const closeModal = () => modalOverlay.classList.remove('active');
  closeBtn?.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) closeModal();
  });

  // Submit single inquiry
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = 'Sending Inquiry...';
    submitBtn.disabled = true;

    const payload = {
      product_id: document.getElementById('inqProductId').value,
      customer_name: document.getElementById('inqCustomerName').value,
      company_name: document.getElementById('inqCompanyName').value,
      email: document.getElementById('inqEmail').value,
      phone: document.getElementById('inqPhone').value,
      quantity: document.getElementById('inqQuantity').value || 1,
      repeat_notes: document.getElementById('inqRepeatNotes')?.value || '',
      message: document.getElementById('inqMessage')?.value || '',
      captcha: document.getElementById('quickInqCaptchaInput')?.value || ''
    };

    try {
      const response = await fetch('/api/inquire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const resData = await response.json();

      if (resData.success) {
        showToast(resData.message, 'success');
        form.reset();
        closeModal();
      } else {
        showToast(resData.message || 'Error sending inquiry.', 'error');
        loadModalCaptcha();
      }
    } catch (err) {
      showToast('Network error submitting quote request. Please retry.', 'error');
    } finally {
      submitBtn.innerHTML = originalText;
      submitBtn.disabled = false;
    }
  });
}

/**
 * Client-Side Catalog Search and Filter Handler
 * Enables responsive live search across all visible product cards in the catalog
 */
function setupClientSideCatalogFilter() {
  const productsGrid = document.querySelector('.products-grid');
  const searchInput = document.querySelector('input[name="q"]');
  if (!productsGrid || !searchInput) return;

  const productCards = Array.from(productsGrid.querySelectorAll('.product-card'));
  if (productCards.length === 0) return;

  const filterCards = () => {
    const query = searchInput.value.toLowerCase().trim();
    let visibleCount = 0;

    productCards.forEach(card => {
      const text = card.textContent.toLowerCase();
      const match = !query || text.includes(query);

      if (match) {
        card.style.display = '';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    const countHeader = document.querySelector('.catalog-results-bar span, .catalog-header-bar p');
    if (countHeader && query) {
      countHeader.innerHTML = `Showing <strong>${visibleCount}</strong> matching spare parts`;
    }
  };

  // Search input live handler (filters live as user types)
  searchInput.addEventListener('input', filterCards);
}

// Global Modal & Overlay Close Handlers (Backdrop click and ESC key)
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.active, .cart-overlay.active, .mobile-drawer-overlay.active').forEach(el => {
      el.classList.remove('active');
    });
    document.querySelectorAll('.modal-overlay, .cart-drawer, .mobile-drawer').forEach(el => {
      el.classList.remove('active');
    });
    document.body.classList.remove('drawer-open');
  }
});
