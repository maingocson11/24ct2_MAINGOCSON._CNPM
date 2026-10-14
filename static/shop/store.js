document.addEventListener('click', async (event) => {
    const thumbnail = event.target.closest('[data-image]');
    if (thumbnail) thumbnail.closest('.gallery').querySelector('.gallery-main').src = thumbnail.dataset.image;
    const quickButton = event.target.closest('.quickview-button');
    const dialog = document.querySelector('#quickview');
    if (quickButton) {
        const content = quickButton.closest('.product-card').querySelector('template').content.cloneNode(true);
        document.querySelector('#quickview-content').replaceChildren(content);
        dialog.showModal();
    }
    if (event.target.closest('.dialog-close') || event.target === dialog) dialog.close();
    const couponButton = event.target.closest('.copy-coupon');
    if (couponButton) {
        try {
            await navigator.clipboard.writeText(couponButton.dataset.code);
            couponButton.textContent = 'Đã sao chép ✓';
        } catch {
            document.querySelector('#coupon-feedback').textContent = 'Mã của bạn: ' + couponButton.dataset.code + ' — nhập mã trong giỏ hàng.';
        }
    }
    const stepButton = event.target.closest('[data-step]');
    if (stepButton) {
        const input = stepButton.closest('.quantity-picker').querySelector('input');
        input.value = Math.max(1, Math.min(Number(input.max), (Number(input.value) || 1) + Number(stepButton.dataset.step)));
    }
    const guideButton = event.target.closest('.size-guide-link');
    if (guideButton) {
        const guide = guideButton.closest('form').querySelector('.size-guide');
        guide.hidden = !guide.hidden;
    }
    const slideButton = event.target.closest('[data-slide]');
    if (slideButton) {
        document.querySelectorAll('.campaign-slide').forEach((slide, index) => slide.classList.toggle('active', index === Number(slideButton.dataset.slide)));
        document.querySelectorAll('[data-slide]').forEach((button) => button.setAttribute('aria-pressed', String(button === slideButton)));
    }
    if (event.target.closest('.back-top')) window.scrollTo({top: 0, behavior: 'smooth'});
});
document.addEventListener('submit', (event) => {
    if (event.target.matches('.confirm-cancel') && !window.confirm('Bạn chắc chắn muốn hủy đơn hàng này?')) event.preventDefault();
});
document.addEventListener('change', (event) => {
    if (event.target.matches('.purchase-form input[name=variant]')) {
        const form = event.target.closest('form');
        const quantity = form.querySelector('input[name=quantity]');
        quantity.max = Math.min(99, Number(event.target.dataset.stock));
        quantity.value = Math.min(Number(quantity.value), Number(quantity.max));
    }
});
