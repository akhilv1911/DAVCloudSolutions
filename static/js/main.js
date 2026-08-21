/* ==========================================================================
   DAV CLOUD SOLUTIONS - MAIN INTERACTIVE JAVASCRIPT
   Tech Stack: HTML5, CSS3, JavaScript (ES6+), Python Flask, MongoDB
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
                mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars-staggered"></i>';
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
                    mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars-staggered"></i>';
                }
            });
        });

        // Close when clicking outside of the navbar
        document.addEventListener('click', function(e) {
            if (!navLinksWrapper.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                navLinksWrapper.classList.remove('mobile-active');
                mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars-staggered"></i>';
            }
        });
    }

    // ----------------------------------------------------------------------
    // 3. GLOBAL 3D PERSPECTIVE TILT PHYSICS
    // ----------------------------------------------------------------------
    const tiltElements = document.querySelectorAll('.tilt-card');
    tiltElements.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            const rotX = (y / (rect.height / 2)) * -6;
            const rotY = (x / (rect.width / 2)) * 6;
            card.style.transform = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg) translateY(-6px) scale(1.01)`;
        });

        card.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0) scale(1)';
        });
    });

    // ----------------------------------------------------------------------
    // 4. SCROLL PROGRESS & FLOATING BACK-TO-TOP HANDLER
    // ----------------------------------------------------------------------
    const progressBar = document.getElementById('scroll-progress-bar');
    const backToTopBtn = document.getElementById('back-to-top-btn');

    window.addEventListener('scroll', function() {
        const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (totalHeight > 0 && progressBar) {
            const progress = (window.pageYOffset / totalHeight) * 100;
            progressBar.style.width = `${progress}%`;
        }

        if (backToTopBtn) {
            if (window.scrollY > 350) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        }
    });

    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ----------------------------------------------------------------------
    // 5. GLOBAL CONTACT & INQUIRY FORM DUAL-DISPATCH
    // ----------------------------------------------------------------------
    const contactForm = document.getElementById('main-contact-form') || document.getElementById('web3forms-contact');

    if (contactForm) {
        contactForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Dispatching Inquiry...';
            }

            const formData = new FormData(contactForm);
            const formJSON = Object.fromEntries(formData.entries());

            try {
                // 1. Dispatch to Web3Forms API (Instant Email Delivery)
                const web3Response = await fetch('https://api.web3forms.com/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(formJSON)
                });
                const web3Data = await web3Response.json();

                // 2. Dispatch to Local Flask Endpoint (MongoDB Persistence)
                await fetch('/api/submit-inquiry', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formJSON)
                }).catch(() => {});

                if (web3Data.success) {
                    showToast('Inquiry received! Our engineering team will reach out shortly with technical scope notes.', 'success');
                    contactForm.reset();
                    const orderModal = document.getElementById('project-order-modal');
                    if (orderModal) orderModal.style.display = 'none';
                } else {
                    showToast(web3Data.message || 'Error transmitting inquiry. Please try again.', 'danger');
                }
            } catch (err) {
                showToast('Network error occurred. Please verify your connection.', 'danger');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnHtml;
                }
            }
        });
    }

    // ----------------------------------------------------------------------
    // 6. DYNAMIC FLASH TOAST CREATOR & AUTO DISMISSAL
    // ----------------------------------------------------------------------
    window.showToast = function(message, category = 'info') {
        let flashContainer = document.getElementById('flash-container');

        if (!flashContainer) {
            flashContainer = document.createElement('div');
            flashContainer.id = 'flash-container';
            flashContainer.className = 'flash-messages-container';
            document.body.appendChild(flashContainer);
        }

        const toast = document.createElement('div');
        toast.className = `flash-toast flash-${category} glass-card`;
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

        setTimeout(() => {
            if (toast && toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                toast.style.transition = 'all 0.4s ease';
                setTimeout(() => toast.remove(), 400);
            }
        }, 5000);
    };

    // Auto-dismiss initial server-rendered flash messages
    const serverToasts = document.querySelectorAll('.flash-toast');
    serverToasts.forEach(toast => {
        setTimeout(() => {
            if (toast && toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                toast.style.transition = 'all 0.4s ease';
                setTimeout(() => toast.remove(), 400);
            }
        }, 5000);
    });

    // ----------------------------------------------------------------------
    // 7. GLOBAL MODAL TOGGLER UTILITY
    // ----------------------------------------------------------------------
    window.toggleModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const isVisible = modal.style.display === 'flex';
            modal.style.display = isVisible ? 'none' : 'flex';
        }
    };

    // ----------------------------------------------------------------------
    // 8. SMOOTH SCROLLING FOR HASH ANCHORS
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