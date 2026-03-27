// script.js

// Modal functionality
function createModal(title, content) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>${title}</h2>
            <div class="modal-body">${content}</div>
        </div>
    `;
    document.body.appendChild(modal);

    const closeBtn = modal.querySelector('.close');
    closeBtn.onclick = () => {
        modal.style.display = 'none';
        setTimeout(() => modal.remove(), 300);
    };

    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
            setTimeout(() => modal.remove(), 300);
        }
    };

    return modal;
}

// Add modal styles dynamically
const modalStyles = `
    .modal {
        display: block;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
        animation: fadeIn 0.3s ease-out;
    }
    .modal-content {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        margin: 10% auto;
        padding: 2rem;
        border-radius: 20px;
        width: 80%;
        max-width: 600px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        animation: slideDown 0.3s ease-out;
    }
    @keyframes slideDown {
        from { transform: translateY(-50px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .close {
        color: #aaa;
        float: right;
        font-size: 28px;
        font-weight: bold;
        cursor: pointer;
        transition: color 0.3s;
    }
    .close:hover { color: #667eea; }
    .modal-body { margin-top: 1rem; }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = modalStyles;
document.head.appendChild(styleSheet);

// Confirm delete with modal
document.addEventListener('DOMContentLoaded', function () {
    const deleteButtons = document.querySelectorAll('.delete-btn');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const schemeId = this.getAttribute('data-scheme-id');
            const modal = createModal('Confirm Deletion', `
                <p>Are you sure you want to delete this scheme? This action cannot be undone.</p>
                <div style="text-align: center; margin-top: 2rem;">
                    <button id="confirm-delete" class="btn" style="margin-right: 1rem;">Yes, Delete</button>
                    <button id="cancel-delete" class="btn" style="background: #e74c3c;">Cancel</button>
                </div>
            `);

            document.getElementById('confirm-delete').onclick = () => {
                fetch(`/delete_scheme/${schemeId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                })
                    .then(response => response.json())
                    .then(data => {
                        modal.style.display = 'none';
                        if (data.success) {
                            showToast('Scheme deleted successfully!', 'success');
                            setTimeout(() => location.reload(), 1500);
                        } else {
                            showToast('Error deleting scheme', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showToast('Error deleting scheme', 'error');
                    });
            };

            document.getElementById('cancel-delete').onclick = () => {
                modal.style.display = 'none';
                setTimeout(() => modal.remove(), 300);
            };
        });
    });

    // Add tooltips to scheme cards
    const schemeCards = document.querySelectorAll('.scheme-card');
    schemeCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = 'Click to view details';
            tooltip.style.cssText = `
                position: absolute;
                background: #333;
                color: white;
                padding: 0.5rem;
                border-radius: 5px;
                font-size: 0.8rem;
                z-index: 100;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s;
            `;
            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - 40 + 'px';
            tooltip.style.opacity = '1';

            this.addEventListener('mouseleave', () => {
                tooltip.style.opacity = '0';
                setTimeout(() => tooltip.remove(), 300);
            });
        });
    });

    // Animate elements on scroll
    const observerOptions = { threshold: 0.1 };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.feature, .scheme-card, .scheme-details').forEach(el => {
        el.style.animationPlayState = 'paused';
        observer.observe(el);
    });

    // Real-time form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function () {
                validateField(this);
            });
            input.addEventListener('input', function () {
                if (this.classList.contains('invalid')) {
                    validateField(this);
                }
            });
        });
    });
});

// Toast notifications
function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#56ab2f' : '#e74c3c'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 1001;
        animation: slideInRight 0.3s ease-out;
        font-weight: 500;
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

const toastStyles = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;

const toastStyleSheet = document.createElement('style');
toastStyleSheet.textContent = toastStyles;
document.head.appendChild(toastStyleSheet);

// Enhanced form validation
function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let message = '';

    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required';
    } else if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid email';
        }
    } else if (field.type === 'password' && value.length < 6) {
        isValid = false;
        message = 'Password must be at least 6 characters';
    }

    field.classList.toggle('invalid', !isValid);
    field.classList.toggle('valid', isValid && value);

    let errorElement = field.parentNode.querySelector('.field-error');
    if (!isValid && message) {
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            errorElement.style.cssText = `
                color: #e74c3c;
                font-size: 0.875rem;
                margin-top: 0.25rem;
                animation: shake 0.5s ease-in-out;
            `;
            field.parentNode.appendChild(errorElement);
        }
        errorElement.textContent = message;
    } else if (errorElement) {
        errorElement.remove();
    }
}

// Add CSS for validation states
const validationStyles = `
    .form-control.invalid {
        border-color: #e74c3c;
        box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1);
    }
    .form-control.valid {
        border-color: #27ae60;
        box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.1);
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
`;

const validationStyleSheet = document.createElement('style');
validationStyleSheet.textContent = validationStyles;
document.head.appendChild(validationStyleSheet);