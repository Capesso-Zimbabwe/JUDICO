// Finance Dashboard JavaScript
// This file contains additional JavaScript functionality for the finance dashboard

// Initialize any additional dashboard features
document.addEventListener('DOMContentLoaded', function() {
    // Add any custom finance dashboard functionality here
    console.log('Finance Dashboard loaded successfully');
    
    // Example: Add hover effects to cards
    const cards = document.querySelectorAll('.bg-white.rounded-lg.shadow');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow-lg');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow-lg');
        });
    });
    
    // Example: Add click handlers for quick actions
    const quickActionButtons = document.querySelectorAll('[data-quick-action]');
    quickActionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.getAttribute('data-quick-action');
            console.log('Quick action triggered:', action);
            // Add specific action handling here
        });
    });
});

// Utility functions for finance dashboard
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(date));
}

// Export functions for use in other scripts
window.FinanceDashboard = {
    formatCurrency,
    formatDate
};