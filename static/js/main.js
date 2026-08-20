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

  // 2. Mobile Menu Toggle
  const mobileToggle = document.querySelector('.mobile-nav-toggle');
  const mainNav = document.querySelector('.main-nav');
  if (mobileToggle && mainNav) {
    mobileToggle.addEventListener('click', () => {
      mainNav.classList.toggle('active');
    });
  }

  // 3. Guest Auth Prompt Modal Controls
  setupGuestAuthPrompt();

  // 4. Quick Single-Product Inquiry Modal Logic
  setupQuickInquiryModal();
});

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

    modalOverlay.classList.add('active');
  };

  // Open modal from product buttons
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-quick-inquire');
    if (btn) {
      e.preventDefault();
      const isLoggedIn = document.body.dataset.loggedIn === 'true';
      const guestModal = document.getElementById('guestAuthPromptModal');

      // If guest and prompt exists and haven't chosen to skip yet
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
      message: document.getElementById('inqMessage')?.value || ''
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
        showToast(resData.message || 'Failed to submit inquiry.', 'error');
      }
    } catch (err) {
      showToast('Network error while submitting inquiry.', 'error');
    } finally {
      submitBtn.innerHTML = originalText;
      submitBtn.disabled = false;
    }
  });
}
