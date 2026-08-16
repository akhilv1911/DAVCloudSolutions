/* ==========================================================================
   DAV CLOUD SOLUTIONS - MAIN INTERACTIVE JAVASCRIPT
   Tech Stack: HTML5, CSS3, JavaScript (ES6+), Python Flask, MongoDB
   Founder: V Akhil
   File: static/js/main.js
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // ----------------------------------------------------------------------
    // 1. THEME TOGGLER (Dark Mode Default / Light Mode Memory)
    // ----------------------------------------------------------------------
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-icon');
    const htmlElement = document.documentElement;

    // Load saved theme preference or default to 'dark'
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const currentTheme = htmlElement.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    function applyTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);
        if (themeIcon) {
            if (theme === 'light') {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
    }

    // ----------------------------------------------------------------------
    // 2. MOBILE NAVIGATION DRAWER TOGGLE
    // ----------------------------------------------------------------------
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navLinksWrapper = document.getElementById('nav-links');

    if (mobileMenuBtn && navLinksWrapper) {
        mobileMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = navLinksWrapper.classList.contains('mobile-active');
            if (isOpen) {
                navLinksWrapper.classList.remove('mobile-active');
                mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
            } else {
                navLinksWrapper.classList.add('mobile-active');
                mobileMenuBtn.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            }
        });

        // Close mobile drawer when clicking a navigation item
        const navItems = navLinksWrapper.querySelectorAll('.nav-item, a');
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                navLinksWrapper.classList.remove('mobile-active');
                if (mobileMenuBtn) {
                    mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
                }
            });
        });

        // Close when clicking outside of the navbar
        document.addEventListener('click', function(e) {
            if (!navLinksWrapper.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                navLinksWrapper.classList.remove('mobile-active');
                mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
            }
        });
    }

    // ----------------------------------------------------------------------
    // 3. WEB3FORMS AJAX SUBMISSION & FEEDBACK
    // ----------------------------------------------------------------------
    const web3formsContact = document.getElementById('web3forms-contact');

    if (web3formsContact) {
        web3formsContact.addEventListener('submit', function(e) {
            e.preventDefault();

            const submitBtn = web3formsContact.querySelector('button[type="submit"]');
            const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';

            // Update button state during transmission
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Transmitting Request...';
            }

            const formData = new FormData(web3formsContact);

            fetch('https://api.web3forms.com/submit', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Inquiry submitted successfully! Founder V Akhil will review your scope shortly.', 'success');
                    web3formsContact.reset();
                } else {
                    showToast(data.message || 'Transmission failed. Please check your access key and try again.', 'danger');
                }
            })
            .catch(error => {
                console.error('Web3Forms Error:', error);
                showToast('Network error occurred while submitting contact form.', 'danger');
            })
            .finally(() => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnHtml;
                }
            });
        });
    }

    // ----------------------------------------------------------------------
    // 4. DYNAMIC FLASH TOAST CREATOR & AUTO DISMISSAL
    // ----------------------------------------------------------------------
    function showToast(message, category = 'info') {
        let flashContainer = document.getElementById('flash-container');

        if (!flashContainer) {
            flashContainer = document.createElement('div');
            flashContainer.id = 'flash-container';
            flashContainer.className = 'flash-messages-container';
            document.body.appendChild(flashContainer);
        }

        const toast = document.createElement('div');
        toast.className = `flash-toast flash-${category}`;
        toast.setAttribute('role', 'alert');

        const iconClass = category === 'success' ? 'fa-circle-check' :
                          category === 'danger'  ? 'fa-circle-xmark' :
                          category === 'warning' ? 'fa-triangle-exclamation' : 'fa-circle-info';

        toast.innerHTML = `
            <div class="flash-content">
                <i class="fa-solid ${iconClass}"></i>
                <span>${message}</span>
            </div>
            <button type="button" class="flash-close-btn" onclick="this.closest('.flash-toast').remove();">&times;</button>
        `;

        flashContainer.appendChild(toast);

        // Auto-dismiss toast with fade animation after 5 seconds
        setTimeout(() => {
            if (toast && toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    // Auto-dismiss initial server-rendered flash messages
    const serverToasts = document.querySelectorAll('.flash-toast');
    serverToasts.forEach(toast => {
        setTimeout(() => {
            if (toast && toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }
        }, 6000);
    });

    // ----------------------------------------------------------------------
    // 5. SMOOTH SCROLLING FOR HASH ANCHORS
    // ----------------------------------------------------------------------
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

});