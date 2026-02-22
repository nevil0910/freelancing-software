// Dashboard interactions
document.addEventListener('DOMContentLoaded', function() {
    // Navigation active state and section switching
    const navItems = document.querySelectorAll('.nav-item');
    const contentSections = document.querySelectorAll('.content-section');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const sectionId = this.getAttribute('data-section');
            
            // Remove active class from all nav items
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Hide all sections
            contentSections.forEach(section => section.classList.remove('active'));
            
            // Show target section
            const targetSection = document.getElementById(sectionId + '-section');
            if (targetSection) {
                targetSection.classList.add('active');
            }
        });
    });

    // Action cards click handlers for navigation
    const actionCards = document.querySelectorAll('.action-card[data-section]');
    
    actionCards.forEach(card => {
        card.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section');
            
            // Find the corresponding nav item and trigger click
            const targetNavItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
            if (targetNavItem) {
                targetNavItem.click();
            }
            
            // Add pulse animation
            this.style.animation = 'pulse 0.3s ease-in-out';
            setTimeout(() => {
                this.style.animation = '';
            }, 300);
        });
    });

    // Empty state buttons
    const emptyStateButtons = document.querySelectorAll('.empty-state .btn[data-section]');
    
    emptyStateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section');
            
            // Find the corresponding nav item and trigger click
            const targetNavItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
            if (targetNavItem) {
                targetNavItem.click();
            }
        });
    });

    // Chat button click handler
    const chatButton = document.querySelector('.chat-button');
    if (chatButton) {
        chatButton.addEventListener('click', function() {
            // Navigate to messages section
            const messagesNavItem = document.querySelector('.nav-item[data-section="messages"]');
            if (messagesNavItem) {
                messagesNavItem.click();
            }
            
            // Add pulse animation
            this.style.animation = 'pulse 0.3s ease-in-out';
            setTimeout(() => {
                this.style.animation = '';
            }, 300);
        });
    }

    // Form submission (placeholder for backend integration)
    const jobForm = document.querySelector('.job-form');
    if (jobForm) {
        jobForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Placeholder - backend will handle this
            alert('Form submission will be handled by backend. All form data is ready!');
            
            // Optionally, you can collect form data here
            const formData = {
                title: document.getElementById('job-title')?.value,
                category: document.getElementById('job-category')?.value,
                description: document.getElementById('job-description')?.value,
                budget: document.getElementById('job-budget')?.value,
                deadline: document.getElementById('job-deadline')?.value,
                skills: document.getElementById('job-skills')?.value
            };
            
            console.log('Form data:', formData);
        });
    }
});

// Add pulse animation for action cards
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(0.95); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style);
