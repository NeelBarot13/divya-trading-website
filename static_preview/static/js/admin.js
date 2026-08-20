/**
 * DIVYA TRADING CO. - Admin Panel JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  // Inquiry Detail Modal & Status Updates
  setupInquiryDetailsModal();
  
  // Product Edit Modal
  setupProductEditModal();
});

function setupInquiryDetailsModal() {
  const modal = document.getElementById('inquiryDetailModal');
  if (!modal) return;

  const closeBtn = document.getElementById('closeInquiryDetailBtn');
  closeBtn?.addEventListener('click', () => modal.classList.remove('active'));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });

  // Open & populate
  document.querySelectorAll('.btn-view-inquiry').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const inqId = btn.dataset.inquiryId;
      
      try {
        const res = await fetch(`/admin/inquiries/${inqId}`);
        const data = await res.json();
        
        document.getElementById('modalInqRef').textContent = `#${data.inquiry_number}`;
        document.getElementById('modalInqCustomer').textContent = data.customer_name;
        document.getElementById('modalInqCompany').textContent = data.company_name || 'N/A';
        document.getElementById('modalInqEmail').textContent = data.email;
        document.getElementById('modalInqPhone').textContent = data.phone;
        document.getElementById('modalInqPhone').href = `tel:${data.phone}`;
        document.getElementById('modalInqWhatsApp').href = `https://wa.me/${data.phone.replace(/[^0-9]/g, '')}`;
        document.getElementById('modalInqMachine').textContent = data.machine_model || 'Not specified';
        document.getElementById('modalInqDate').textContent = data.created_at;
        document.getElementById('modalInqMessage').textContent = data.message || 'No additional message.';
        
        const statusSelect = document.getElementById('modalInqStatus');
        if (statusSelect) statusSelect.value = data.status;
        
        const notesInput = document.getElementById('modalInqNotes');
        if (notesInput) notesInput.value = data.admin_notes || '';
        
        // Populate items table
        const tbody = document.getElementById('modalInqItemsBody');
        tbody.innerHTML = data.items.map((item, idx) => `
          <tr>
            <td style="font-weight:600;">#${idx + 1}</td>
            <td>
              <strong>${item.product_name}</strong>
              ${item.part_number ? `<br><span style="font-size:0.75rem; color:#64748b;">Part No: ${item.part_number}</span>` : ''}
            </td>
            <td style="text-align:center; font-weight:700; color:#0052cc;">${item.quantity}</td>
            <td style="font-size:0.8rem; color:#475569;">${item.notes || '-'}</td>
          </tr>
        `).join('');

        // Form submit to update status
        const updateForm = document.getElementById('inquiryUpdateForm');
        updateForm.onsubmit = async (evt) => {
          evt.preventDefault();
          const updateRes = await fetch(`/admin/inquiries/${data.id}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              status: statusSelect.value,
              admin_notes: notesInput.value
            })
          });
          const updateData = await updateRes.json();
          if (updateData.success) {
            alert('Inquiry status updated!');
            window.location.reload();
          }
        };

        modal.classList.add('active');
      } catch (err) {
        console.error('Error fetching inquiry details:', err);
      }
    });
  });
}

function setupProductEditModal() {
  const modal = document.getElementById('productEditModal');
  if (!modal) return;

  const closeBtn = document.getElementById('closeProductEditBtn');
  closeBtn?.addEventListener('click', () => modal.classList.remove('active'));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });

  document.querySelectorAll('.btn-edit-product').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const form = document.getElementById('productEditForm');
      form.action = `/admin/products/${btn.dataset.id}/edit`;

      document.getElementById('editProdName').value = btn.dataset.name || '';
      document.getElementById('editProdPartNo').value = btn.dataset.partNumber || '';
      document.getElementById('editProdCategory').value = btn.dataset.categoryId || '';
      document.getElementById('editProdMachine').value = btn.dataset.machineId || '';
      document.getElementById('editProdRepeat').value = btn.dataset.repeatSizes || '';
      document.getElementById('editProdMaterial').value = btn.dataset.material || '';
      document.getElementById('editProdDesc').value = btn.dataset.description || '';
      document.getElementById('editProdSpecs').value = btn.dataset.specifications || '';
      
      const featuredCb = document.getElementById('editProdFeatured');
      if (featuredCb) featuredCb.checked = (btn.dataset.isFeatured === 'True' || btn.dataset.isFeatured === 'true');

      const activeCb = document.getElementById('editProdActive');
      if (activeCb) activeCb.checked = (btn.dataset.isActive === 'True' || btn.dataset.isActive === 'true');

      const previewImg = document.getElementById('editProdImagePreview');
      if (previewImg) previewImg.src = btn.dataset.imageUrl || '/static/images/hero_parts.jpg';

      modal.classList.add('active');
    });
  });
}
