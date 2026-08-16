/* ==========================================================================
   DAV CLOUD SOLUTIONS - DASHBOARD INTERACTIVE JAVASCRIPT
   Tech Stack: HTML5, CSS3, JavaScript (ES6+), Python Flask, MongoDB
   File: static/js/dashboard.js
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {

    // ----------------------------------------------------------------------
    // 1. REUSABLE MODAL MANAGEMENT SYSTEM
    // ----------------------------------------------------------------------
    window.toggleModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const isVisible = modal.style.display === 'flex';
            modal.style.display = isVisible ? 'none' : 'flex';

            // Prevent background scrolling when modal is active
            document.body.style.overflow = isVisible ? 'auto' : 'hidden';
        }
    };

    // Close modals when clicking outside the modal content card
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal-overlay')) {
            event.target.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    // Close modals on 'Escape' key press
    window.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(modal => {
                modal.style.display = 'none';
            });
            document.body.style.overflow = 'auto';
        }
    });

    // ----------------------------------------------------------------------
    // 2. SUPPORT & QUERY MODAL PRE-FILLER
    // ----------------------------------------------------------------------
    window.openSupportModal = function(projectTitle) {
        const studentSubject = document.getElementById('ticket-subject');
        const bizSubject = document.getElementById('biz-ticket-subject');

        if (studentSubject) {
            studentSubject.value = `Query regarding: ${projectTitle}`;
            studentSubject.focus();
        } else if (bizSubject) {
            bizSubject.value = `Feedback regarding: ${projectTitle}`;
            bizSubject.focus();
        }
    };

    // ----------------------------------------------------------------------
    // 3. STUDENT & BUSINESS SUPPORT TICKET FORM INTERCEPTORS
    // ----------------------------------------------------------------------
    const studentTicketForm = document.getElementById('support-ticket-form');
    const bizTicketForm = document.getElementById('business-support-form');

    if (studentTicketForm) {
        studentTicketForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const submitBtn = studentTicketForm.querySelector('button[type="submit"]');
            
            if (submitBtn) submitBtn.disabled = true;

            setTimeout(() => {
                alert('Support ticket submitted successfully! Founder Akhil V and team will respond to your registered email.');
                studentTicketForm.reset();
                if (submitBtn) submitBtn.disabled = false;
            }, 600);
        });
    }

    if (bizTicketForm) {
        bizTicketForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const submitBtn = bizTicketForm.querySelector('button[type="submit"]');

            if (submitBtn) submitBtn.disabled = true;

            setTimeout(() => {
                alert('Priority ticket transmitted to Founder Akhil V and core engineering team.');
                bizTicketForm.reset();
                if (submitBtn) submitBtn.disabled = false;
            }, 600);
        });
    }

    // ----------------------------------------------------------------------
    // 4. DYNAMIC MILESTONE PROGRESS TRACKER UPDATER
    // ----------------------------------------------------------------------
    window.updateMilestones = function(containerElement, currentStatus) {
        if (!containerElement) return;

        const steps = containerElement.querySelectorAll('.tracker-step');
        const statusMap = {
            'pending': 1,
            'building': 2,
            'in progress': 2,
            'testing': 3,
            'ready': 4,
            'completed': 4
        };

        const activeStep = statusMap[currentStatus.toLowerCase()] || 1;

        steps.forEach((step, index) => {
            if (index < activeStep) {
                step.classList.add('completed');
                const dot = step.querySelector('.step-dot');
                if (dot) dot.innerHTML = '<i class="fa-solid fa-check"></i>';
            } else {
                step.classList.remove('completed');
            }
        });
    };

});