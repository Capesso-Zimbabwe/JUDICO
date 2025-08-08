/**
 * Modal Select Fix - Ensures select elements in modals work properly
 * Modified to avoid conflicts with prevent-autofill.js
 */
document.addEventListener('DOMContentLoaded', function() {
    // Function to fix select elements in modals
    function fixModalSelects() {
        // Get all modals on the page
        const modals = document.querySelectorAll('[data-modal-backdrop]');
        
        modals.forEach(modal => {
            // Check if this modal has already been processed
            if (modal.getAttribute('data-select-fixed') === 'true') return;
            
            // Mark as processed
            modal.setAttribute('data-select-fixed', 'true');
            
            // Find all select elements in this modal
            const selects = modal.querySelectorAll('select');
            
            selects.forEach(select => {
                // Remove any disabled attribute that might have been added
                select.removeAttribute('disabled');
                
                // Set data-disabled attribute to false to work with prevent-autofill.js
                select.setAttribute('data-disabled', 'false');
                
                // Add event listeners to ensure the select stays enabled
                select.addEventListener('click', function(e) {
                    // Prevent any browser extension from interfering
                    e.stopPropagation();
                    
                    this.removeAttribute('disabled');
                    this.setAttribute('data-disabled', 'false');
                    
                    // Log the interaction for debugging
                    console.log(`Modal select ${this.id} clicked, disabled=${this.disabled}`);
                });
                
                select.addEventListener('focus', function() {
                    this.removeAttribute('disabled');
                    this.setAttribute('data-disabled', 'false');
                    
                    // Log the interaction for debugging
                    console.log(`Modal select ${this.id} focused, disabled=${this.disabled}`);
                });
            });
        });
    }
    
    // Fix selects when page loads
    fixModalSelects();
    
    // Watch for modal open events
    document.addEventListener('click', function(e) {
        // Check if the clicked element opens a modal
        const modalTrigger = e.target.closest('[data-modal-target], [data-modal-toggle]');
        if (modalTrigger) {
            const modalId = modalTrigger.getAttribute('data-modal-target') || 
                          modalTrigger.getAttribute('data-modal-toggle');
            
            if (modalId) {
                // Wait for modal to open
                setTimeout(function() {
                    fixModalSelects();
                    
                    // Extra check for the specific modal
                    const modal = document.getElementById(modalId);
                    if (modal) {
                        const selects = modal.querySelectorAll('select');
                        selects.forEach(select => {
                            select.disabled = false;
                        });
                    }
                }, 300);
            }
        }
    });
    
    // Watch for HTMX content swaps
    document.body.addEventListener('htmx:afterSwap', function() {
        setTimeout(fixModalSelects, 50);
    });
});