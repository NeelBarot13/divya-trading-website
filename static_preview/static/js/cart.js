/**
 * DIVYA TRADING CO. - Quote Cart Management System
 * Allows users to add multiple spare parts to an inquiry list and request a combined quote.
 */

const CART_STORAGE_KEY = 'dtc_quote_cart';

const QuoteCart = {
  items: [],

  init() {
    this.load();
    this.updateBadge();
    this.setupEventListeners();
    this.render();
  },

  load() {
    try {
      const stored = localStorage.getItem(CART_STORAGE_KEY);
      this.items = stored ? JSON.parse(stored) : [];
    } catch (e) {
      this.items = [];
    }
  },

  save() {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(this.items));
    this.updateBadge();
    this.render();
  },

  addItem(product) {
    const existingIndex = this.items.findIndex(item => item.id == product.id);
    if (existingIndex > -1) {
      this.items[existingIndex].quantity += (product.quantity || 1);
    } else {
      this.items.push({
        id: product.id,
        name: product.name,
        part_number: product.part_number,
        image_url: product.image_url || '/static/images/hero_parts.jpg',
        quantity: product.quantity || 1,
        notes: product.notes || ''
      });
    }
    this.save();
    showToast(`Added "${product.name}" to Quote List!`, 'success');
  },

  removeItem(productId) {
    this.items = this.items.filter(item => item.id != productId);
    this.save();
  },

  updateQuantity(productId, quantity) {
    const item = this.items.find(item => item.id == productId);
    if (item) {
      item.quantity = Math.max(1, parseInt(quantity) || 1);
      this.save();
    }
  },

  updateNotes(productId, notes) {
    const item = this.items.find(item => item.id == productId);
    if (item) {
      item.notes = notes;
      this.save();
    }
  },

  clear() {
    this.items = [];
    this.save();
  },

  getTotalCount() {
    return this.items.reduce((total, item) => total + (item.quantity || 1), 0);
  },

  updateBadge() {
    const badges = document.querySelectorAll('.cart-badge, .cart-badge-count, #stickyCartBadge');
    const count = this.items.length;
    badges.forEach(badge => {
      badge.textContent = count;
      if (count > 0) {
        badge.classList.add('has-items');
      } else {
        badge.classList.remove('has-items');
      }
    });
  },

  openDrawer() {
    const drawer = document.getElementById('cartDrawer');
    const overlay = document.getElementById('cartOverlay');
    drawer?.classList.add('active');
    overlay?.classList.add('active');
    this.render();
  },

  closeDrawer() {
    const drawer = document.getElementById('cartDrawer');
    const overlay = document.getElementById('cartOverlay');
    drawer?.classList.remove('active');
    overlay?.classList.remove('active');
  },

  render() {
    const container = document.getElementById('cartItemsList');
    const formSection = document.getElementById('cartInquiryFormContainer');
    const emptyState = document.getElementById('cartEmptyState');
    
    if (!container) return;

    if (this.items.length === 0) {
      container.innerHTML = '';
      if (emptyState) emptyState.style.display = 'block';
      if (formSection) formSection.style.display = 'none';
      return;
    }

    if (emptyState) emptyState.style.display = 'none';
    if (formSection) formSection.style.display = 'block';

    container.innerHTML = this.items.map(item => `
      <div class="cart-item-card">
        <img src="${item.image_url}" alt="${item.name}" class="cart-item-thumb">
        <div class="cart-item-info">
          <h4>${item.name}</h4>
          ${item.part_number ? `<span class="cart-item-part">Part No: ${item.part_number}</span>` : ''}
          <div class="cart-item-qty-row">
            <span style="font-size: 0.75rem; color: #64748b;">Qty:</span>
            <div class="qty-input-group">
              <button class="qty-btn" onclick="QuoteCart.updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
              <input type="number" class="qty-input" value="${item.quantity}" min="1" onchange="QuoteCart.updateQuantity(${item.id}, this.value)">
              <button class="qty-btn" onclick="QuoteCart.updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
            </div>
          </div>
          <input type="text" class="form-control" style="margin-top:6px; font-size:0.75rem; padding:4px 8px;" 
            placeholder="Repeat size / requirement note (e.g. 64R)" 
            value="${item.notes || ''}" 
            onchange="QuoteCart.updateNotes(${item.id}, this.value)">
        </div>
        <button class="cart-item-remove" onclick="QuoteCart.removeItem(${item.id})" title="Remove item">✕</button>
      </div>
    `).join('');
  },

  setupEventListeners() {
    // Open / Close Cart triggers
    document.querySelectorAll('.btn-open-quote-cart').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        this.openDrawer();
      });
    });

    document.getElementById('cartCloseBtn')?.addEventListener('click', () => this.closeDrawer());
    document.getElementById('cartOverlay')?.addEventListener('click', () => this.closeDrawer());

    // Add to Cart buttons on product cards
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-add-quote-cart');
      if (btn) {
        e.preventDefault();
        const product = {
          id: btn.dataset.productId,
          name: btn.dataset.productName,
          part_number: btn.dataset.partNumber,
          image_url: btn.dataset.productImage,
          quantity: parseInt(btn.dataset.quantity || 1)
        };
        this.addItem(product);
      }
    });

    // Handle Cart Multi-Product Submission
    const form = document.getElementById('cartInquirySubmitForm');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (this.items.length === 0) {
          showToast('Please add items to your quote list first.', 'error');
          return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = 'Submitting Request...';
        submitBtn.disabled = true;

        const payload = {
          customer: {
            name: document.getElementById('cartCustomerName').value,
            company: document.getElementById('cartCompanyName').value,
            email: document.getElementById('cartEmail').value,
            phone: document.getElementById('cartPhone').value,
            country: document.getElementById('cartCountry')?.value || 'India',
            machine_model: document.getElementById('cartMachineModel')?.value || '',
            message: document.getElementById('cartMessage')?.value || ''
          },
          items: this.items
        };

        try {
          const res = await fetch('/api/inquiry-cart/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const result = await res.json();

          if (result.success) {
            showToast(result.message, 'success');
            this.clear();
            form.reset();
            this.closeDrawer();
          } else {
            showToast(result.message || 'Failed to submit quote request.', 'error');
          }
        } catch (err) {
          showToast('Error submitting quote request. Please try again.', 'error');
        } finally {
          submitBtn.innerHTML = originalText;
          submitBtn.disabled = false;
        }
      });
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  QuoteCart.init();
});
