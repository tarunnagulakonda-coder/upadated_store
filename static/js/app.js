// Global state for items in cart
let cartItemsState = {}; // { product_id: quantity }
const MIN_ORDER_AMOUNT = 100;
let currentCartTotal = 0;

// Navbar search handler
function handleSearch() {
    const q = document.getElementById('searchInput')?.value?.trim();
    if (q) window.location.href = '/search?q=' + encodeURIComponent(q);
}

document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();

    // If we're on the cart page, load it
    if (document.getElementById('cartItemsList')) {
        loadCartPage();
    }

    // Pre-fetch cart items so interactive grids know what's active
    syncCartState();
});

function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.innerText = message;
    toast.classList.remove('hidden');
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.classList.add('hidden'), 300);
    }, 2500);
}

// -------------------------------------------------------------------
// CORE CART OPERATIONS
// -------------------------------------------------------------------
async function updateCartBadge() {
    try {
        const response = await fetch('/api/cart/count');
        const data = await response.json();
        const badge = document.getElementById('cartCount');
        if (badge) badge.innerText = data.count || 0;
    } catch (e) { }
}

async function syncCartState() {
    try {
        const response = await fetch('/api/cart');
        const data = await response.json();
        cartItemsState = {}; // clear

        if (data.items) {
            data.items.forEach(item => {
                cartItemsState[item.cart_item_id + '_pid_' + item.product_id] = item.quantity;
                cartItemsState[item.name] = item.quantity; // mapping by name to simplify UI sync 
                // A better approach is returning product_ids directly in the API for sync.
            });
        }
    } catch (e) { }
}

// Inline + Add Button Click 
async function addToCartInline(btn, productId) {
    btn.innerText = "Adding...";
    try {
        const response = await fetch('/api/cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: 1 })
        });
        const data = await response.json();
        if (data.success) {
            // Update UI
            btn.classList.add('hidden');
            const qtyControl = btn.nextElementSibling;
            qtyControl.classList.remove('hidden');
            qtyControl.querySelector('.qty-display').innerText = 1;

            showToast("Added to cart ✓");
            updateCartBadge();
        } else {
            if (data.redirect) { window.location.href = data.redirect; return; }
            alert(data.message || "Failed to add.");
            btn.innerText = "+ Add";
        }
    } catch (e) {
        btn.innerText = "+ Add";
    }
}

// Detail Page Add Button Click 
async function addToCartDetail(btn, productId) {
    addToCartInline(btn, productId);
}


// Inline Quantity +/-
async function updateInlineQty(btn, productId, action) {
    const qtyDisplay = btn.parentElement.querySelector('.qty-display');
    let currentQty = parseInt(qtyDisplay.innerText);

    // First figure out the cart_item_id. Since we didn't fetch it, we will just call a generic endpoint or we rely on cart logic.
    // Instead of completely refactoring API right now, I'll cheat a bit. 
    // The previous `/api/cart/<item_id>` uses cart_item_id.
    // If I don't have cart_item_id on the product grid, I can just do a POST to /api/cart for 'inc' 
    // and wait, there isn't a simple 'dec' by product_id in the API we wrote earlier.

    // Let's optimize: since we are on the grid, just POST quantity: 1 for 'inc' using the add_to_cart logic!
    if (action === 'inc') {
        const response = await fetch('/api/cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: 1 })
        });
        if (response.ok) {
            qtyDisplay.innerText = currentQty + 1;
            updateCartBadge();
        }
    } else {
        // For 'dec', fetch the cart, find the item, and then PUT/DELETE.
        // It's a bit heavier on the client, but keeps API intact.
        const res = await fetch('/api/cart');
        const data = await res.json();

        let cartItem = null;
        if (data.items) {
            cartItem = data.items.find(i => i.name === btn.closest('.product-card')?.querySelector('.prod-name')?.innerText
                || i.name === document.querySelector('.product-info-block h2')?.innerText);
        }

        if (cartItem) {
            await fetch(`/api/cart/${cartItem.cart_item_id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'dec' })
            });

            if (currentQty > 1) {
                qtyDisplay.innerText = currentQty - 1;
            } else {
                // Was 1, now 0 -> switch back to add btn
                btn.parentElement.classList.add('hidden');
                btn.parentElement.previousElementSibling.classList.remove('hidden');
                btn.parentElement.previousElementSibling.innerHTML = '<span class="btn-text">+ Add</span>';
            }
            updateCartBadge();
        }
    }
}


// -------------------------------------------------------------------
// CART PAGE LOGIC
// -------------------------------------------------------------------
async function loadCartPage() {
    const list = document.getElementById('cartItemsList');
    const summary = document.getElementById('cartSummary');
    const emptyMsg = document.getElementById('emptyCartMessage');

    try {
        const res = await fetch('/api/cart');
        const data = await res.json();

        if (!data.items || data.items.length === 0) {
            list.innerHTML = '';
            summary.classList.add('hidden');
            emptyMsg.classList.remove('hidden');
            return;
        }

        let html = '';
        let total = 0;

        data.items.forEach(item => {
            total += (item.price * item.quantity);
            html += `
            <div class="cart-item-card">
                <div class="cart-item-details">
                    <h4>${item.name}</h4>
                    <p>₹${item.price}</p>
                    <p class="price">₹${item.price * item.quantity}</p>
                </div>
                <div class="cart-item-actions">
                    <div class="qty-control">
                        <button class="qty-btn" onclick="updateCartItemPage(${item.cart_item_id}, 'dec')">−</button>
                        <span class="qty-display">${item.quantity}</span>
                        <button class="qty-btn" onclick="updateCartItemPage(${item.cart_item_id}, 'inc')">+</button>
                    </div>
                </div>
            </div>`;
        });

        list.innerHTML = html;
        currentCartTotal = total;
        document.getElementById('cartTotalDisplay').innerText = '₹' + total;
        document.getElementById('cartTotalFinal').innerText = '₹' + total;

        const minNotice = document.getElementById('minOrderNotice');
        const checkoutBtn = document.getElementById('proceedToCheckoutBtn');
        const progressFill = document.getElementById('minOrderProgressFill');
        const minOrderRemaining = document.getElementById('minOrderRemaining');
        const minOrderTitle = document.getElementById('minOrderTitle');
        const minOrderText = document.getElementById('minOrderText');
        const minOrderIcon = document.getElementById('minOrderIcon');

        if (minNotice) {
            minNotice.classList.remove('hidden');
            const percent = Math.min(100, Math.round((total / MIN_ORDER_AMOUNT) * 100));
            if (progressFill) progressFill.style.width = percent + '%';

            if (total < MIN_ORDER_AMOUNT) {
                const diff = MIN_ORDER_AMOUNT - total;
                if (minOrderRemaining) minOrderRemaining.innerText = diff;
                if (minOrderTitle) minOrderTitle.innerText = `Minimum order is ₹${MIN_ORDER_AMOUNT}`;
                if (minOrderText) minOrderText.innerHTML = `Add <strong>₹${diff}</strong> more to continue to checkout`;
                if (minOrderIcon) minOrderIcon.innerText = '⚠️';
                minNotice.classList.remove('success');
                minNotice.classList.add('warning');

                if (checkoutBtn) {
                    checkoutBtn.classList.add('btn-disabled');
                    checkoutBtn.classList.remove('pulse');
                    checkoutBtn.innerText = `Add ₹${diff} more to Checkout`;
                }
            } else {
                if (minOrderTitle) minOrderTitle.innerText = `Minimum order reached!`;
                if (minOrderText) minOrderText.innerHTML = `You can now proceed to checkout`;
                if (minOrderIcon) minOrderIcon.innerText = '✅';
                minNotice.classList.remove('warning');
                minNotice.classList.add('success');

                if (checkoutBtn) {
                    checkoutBtn.classList.remove('btn-disabled');
                    checkoutBtn.classList.add('pulse');
                    checkoutBtn.innerText = `Proceed to Checkout`;
                }
            }
        }

        summary.classList.remove('hidden');
        emptyMsg.classList.add('hidden');

    } catch (e) { }
}

function proceedToCheckout() {
    if (currentCartTotal < MIN_ORDER_AMOUNT) {
        const diff = MIN_ORDER_AMOUNT - currentCartTotal;
        showToast(`Minimum order is ₹${MIN_ORDER_AMOUNT}. Add ₹${diff} more to continue.`);
        return;
    }
    window.location.href = '/checkout';
}

async function updateCartItemPage(cartItemId, action) {
    try {
        await fetch(`/api/cart/${cartItemId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        loadCartPage();
        updateCartBadge();
    } catch (e) { }
}

// -------------------------------------------------------------------
// CHECKOUT LOGIC
// -------------------------------------------------------------------
async function placeOrder() {
    const btn = document.getElementById('orderBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Processing...";
    }

    try {
        const response = await fetch('/api/orders', { method: 'POST' });
        const data = await response.json();

        if (data.success && data.whatsapp_url) {
            showToast("Order placed!");
            setTimeout(() => {
                window.location.href = data.whatsapp_url;
            }, 1000);
        } else {
            showToast(data.message || "Error placing order");
            alert(data.message || "Error placing order");
            if (btn) {
                btn.disabled = false;
                btn.innerText = "Place Order";
            }
        }
    } catch (e) {
        alert("An error occurred");
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Place Order";
        }
    }
}
