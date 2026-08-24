/* ==========================================================================
   DAV CLOUD SOLUTIONS - MAIN INTERACTIVE JAVASCRIPT ENGINE
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

        const navItems = navLinksWrapper.querySelectorAll('.nav-item, a');
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                navLinksWrapper.classList.remove('mobile-active');
                if (mobileMenuBtn) {
                    mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars-staggered"></i>';
                }
            });
        });

        document.addEventListener('click', function(e) {
            if (!navLinksWrapper.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                navLinksWrapper.classList.remove('mobile-active');
                mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars-staggered"></i>';
            }
        });
    }

    // ----------------------------------------------------------------------
    // 3. HARDWARE-OPTIMIZED NEURAL PARTICLE CANVAS (60 FPS)
    // ----------------------------------------------------------------------
    const canvas = document.getElementById('neural-particle-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        let mouse = { x: null, y: null, radius: 120 };
        let isScrolling = false;
        let scrollTimeout;

        // Pause canvas updates during fast scrolling to allocate GPU to the UI
        window.addEventListener('scroll', function() {
            isScrolling = true;
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                isScrolling = false;
            }, 120);
        }, { passive: true });

        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            initParticles();
        }

        window.addEventListener('resize', resizeCanvas, { passive: true });

        if (window.innerWidth > 768) {
            window.addEventListener('mousemove', e => {
                mouse.x = e.x;
                mouse.y = e.y;
            }, { passive: true });

            window.addEventListener('mouseleave', () => {
                mouse.x = null;
                mouse.y = null;
            }, { passive: true });
        }

        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 1.5 + 1;
                this.speedX = (Math.random() - 0.5) * 0.5;
                this.speedY = (Math.random() - 0.5) * 0.5;
            }
            update() {
                this.x += this.speedX;
                this.y += this.speedY;

                if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
                if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;

                if (mouse.x && mouse.y) {
                    const dx = mouse.x - this.x;
                    const dy = mouse.y - this.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < mouse.radius) {
                        const force = (mouse.radius - dist) / mouse.radius;
                        this.x -= (dx / dist) * force * 1.5;
                        this.y -= (dy / dist) * force * 1.5;
                    }
                }
            }
            draw() {
                const isLight = htmlElement.getAttribute('data-theme') === 'light';
                ctx.fillStyle = isLight ? 'rgba(99, 102, 241, 0.35)' : 'rgba(129, 140, 248, 0.45)';
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        function initParticles() {
            particles = [];
            const isMobile = window.innerWidth < 768;
            // Cap particle count strictly based on viewport size
            const maxParticles = isMobile ? 22 : 55;
            const particleCount = Math.min(Math.floor((canvas.width * canvas.height) / 25000), maxParticles);
            for (let i = 0; i < particleCount; i++) {
                particles.push(new Particle());
            }
        }

        function animateParticles() {
            if (!isScrolling) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                const isLight = htmlElement.getAttribute('data-theme') === 'light';
                const isMobile = window.innerWidth < 768;
                const maxDist = isMobile ? 80 : 105;

                // Render connection vectors
                for (let a = 0; a < particles.length; a++) {
                    for (let b = a + 1; b < particles.length; b++) {
                        const dx = particles[a].x - particles[b].x;
                        const dy = particles[a].y - particles[b].y;
                        const dist = Math.sqrt(dx * dx + dy * dy);

                        if (dist < maxDist) {
                            const opacity = (1 - dist / maxDist) * (isLight ? 0.12 : 0.18);
                            ctx.strokeStyle = `rgba(99, 102, 241, ${opacity})`;
                            ctx.lineWidth = 0.8;
                            ctx.beginPath();
                            ctx.moveTo(particles[a].x, particles[a].y);
                            ctx.lineTo(particles[b].x, particles[b].y);
                            ctx.stroke();
                        }
                    }
                }

                particles.forEach(p => {
                    p.update();
                    p.draw();
                });
            }

            requestAnimationFrame(animateParticles);
        }

        resizeCanvas();
        animateParticles();
    }

    // ----------------------------------------------------------------------
    // 4. TYPEWRITER DYNAMIC HEADLINE ENGINE
    // ----------------------------------------------------------------------
    class TxtType {
        constructor(el, toRotate, period) {
            this.toRotate = toRotate;
            this.el = el;
            this.loopNum = 0;
            this.period = parseInt(period, 10) || 2000;
            this.txt = '';
            this.tick();
            this.isDeleting = false;
        }
        tick() {
            const i = this.loopNum % this.toRotate.length;
            const fullTxt = this.toRotate[i];

            if (this.isDeleting) {
                this.txt = fullTxt.substring(0, this.txt.length - 1);
            } else {
                this.txt = fullTxt.substring(0, this.txt.length + 1);
            }

            this.el.innerHTML = '<span class="wrap">' + this.txt + '</span>';
            let delta = 150 - Math.random() * 80;

            if (this.isDeleting) delta /= 2;

            if (!this.isDeleting && this.txt === fullTxt) {
                delta = this.period;
                this.isDeleting = true;
            } else if (this.isDeleting && this.txt === '') {
                this.isDeleting = false;
                this.loopNum++;
                delta = 400;
            }

            setTimeout(() => this.tick(), delta);
        }
    }

    const typewriters = document.querySelectorAll('.typewrite');
    typewriters.forEach(el => {
        const toRotate = el.getAttribute('data-type');
        const period = el.getAttribute('data-period');
        if (toRotate) {
            new TxtType(el, JSON.parse(toRotate), period);
        }
    });

    // ----------------------------------------------------------------------
    // 5. ANIMATED NUMBER TICKER COUNTERS
    // ----------------------------------------------------------------------
    const counters = document.querySelectorAll('.stat-counter');
    let hasCounted = false;

    function runCounters() {
        counters.forEach(counter => {
            const target = parseFloat(counter.getAttribute('data-target'));
            const decimals = parseInt(counter.getAttribute('data-decimals') || '0', 10);
            const duration = 1600;
            const startTime = performance.now();

            function updateNumber(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const easeProgress = 1 - (1 - progress) * (1 - progress);
                const currentVal = easeProgress * target;

                counter.textContent = currentVal.toFixed(decimals);

                if (progress < 1) {
                    requestAnimationFrame(updateNumber);
                } else {
                    counter.textContent = target.toFixed(decimals);
                }
            }

            requestAnimationFrame(updateNumber);
        });
    }

    const statsSection = document.querySelector('.hero-stats, .metric-card');
    if (statsSection) {
        const counterObserver = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !hasCounted) {
                    hasCounted = true;
                    runCounters();
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });
        counterObserver.observe(statsSection);
    }

    // ----------------------------------------------------------------------
    // 6. SCROLL REVEAL (INTERSECTION OBSERVER)
    // ----------------------------------------------------------------------
    const revealObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-revealed');
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -20px 0px' });

    document.querySelectorAll('.glass-card, .section-header, .service-card, .pipeline-step, .team-card').forEach(el => {
        el.classList.add('reveal-on-scroll');
        revealObserver.observe(el);
    });

    // ----------------------------------------------------------------------
    // 7. DESKTOP-ONLY 3D TILT & MOUSE RADIAL SPOTLIGHT
    // ----------------------------------------------------------------------
    if (window.innerWidth > 1024) {
        const tiltElements = document.querySelectorAll('.tilt-card, .glass-card');
        tiltElements.forEach(card => {
            card.addEventListener('mousemove', function(e) {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                card.style.setProperty('--mouse-x', `${x}px`);
                card.style.setProperty('--mouse-y', `${y}px`);

                if (card.classList.contains('tilt-card')) {
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    const rotX = ((y - centerY) / centerY) * -4;
                    const rotY = ((x - centerX) / centerX) * 4;
                    card.style.transform = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg) translateY(-4px)`;
                }
            }, { passive: true });

            card.addEventListener('mouseleave', function() {
                if (card.classList.contains('tilt-card')) {
                    card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
                }
            });
        });

        // 8. Magnetic Buttons (Desktop Only)
        const magneticButtons = document.querySelectorAll('.magnetic-btn');
        magneticButtons.forEach(btn => {
            btn.addEventListener('mousemove', function(e) {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                btn.style.transform = `translate(${x * 0.18}px, ${y * 0.18}px)`;
            }, { passive: true });

            btn.addEventListener('mouseleave', function() {
                btn.style.transform = 'translate(0px, 0px)';
            });
        });
    }

    // ----------------------------------------------------------------------
    // 9. HARDWARE-ACCELERATED SCROLL PROGRESS & BACK-TO-TOP
    // ----------------------------------------------------------------------
    const progressBar = document.getElementById('scroll-progress-bar');
    const backToTopBtn = document.getElementById('back-to-top-btn');
    let ticking = false;

    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(() => {
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
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });

    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ----------------------------------------------------------------------
    // 10. DYNAMIC GLASS TOAST DISMISSAL
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
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }
        }, 4500);
    };

    const serverToasts = document.querySelectorAll('.flash-toast');
    serverToasts.forEach(toast => {
        setTimeout(() => {
            if (toast && toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }
        }, 4500);
    });

    // ----------------------------------------------------------------------
    // 11. GLOBAL MODAL TOGGLER UTILITY
    // ----------------------------------------------------------------------
    window.toggleModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const isVisible = modal.style.display === 'flex';
            modal.style.display = isVisible ? 'none' : 'flex';
        }
    };

    // ----------------------------------------------------------------------
    // 12. SMOOTH SCROLLING FOR HASH ANCHORS
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