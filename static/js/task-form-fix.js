/**
 * Task Form Fix - Ensures select elements work properly in the task form
 */
document.addEventListener('DOMContentLoaded', function() {
    // Function to initialize select elements in the task form
    function initializeTaskFormSelects() {
        // Target the specific select elements in the task form
        const clientSelect = document.getElementById('id_client');
        const assignedToSelect = document.getElementById('id_assigned_to');
        const statusSelect = document.getElementById('id_status');
        const prioritySelect = document.getElementById('id_priority');
        
        const selects = [clientSelect, assignedToSelect, statusSelect, prioritySelect];
        
        // Process each select element if it exists
        selects.forEach(select => {
            if (!select) return;
            
            // Ensure the element is not disabled
            select.disabled = false;
            
            // Add a click handler to ensure the dropdown opens
            select.addEventListener('click', function(e) {
                // Prevent any browser extension from interfering
                e.stopPropagation();
                
                // Force the select to be enabled
                this.disabled = false;
                
                // Log the interaction for debugging
                console.log(`${this.id} clicked, disabled=${this.disabled}`);
            });
            
            // Add a focus handler
            select.addEventListener('focus', function() {
                // Force the select to be enabled
                this.disabled = false;
                
                // Log the interaction for debugging
                console.log(`${this.id} focused, disabled=${this.disabled}`);
            });
        });
        
        console.log('Task form select elements initialized');
    }
    
    // Initialize when the page loads
    initializeTaskFormSelects();
    
    // Re-initialize after HTMX content swaps (when the modal is loaded)
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        // Check if the swapped content contains the task form
        if (evt.detail.target.id === 'new-modal-container' || 
            evt.detail.target.querySelector('#newTaskForm')) {
            console.log('Task form loaded via HTMX, initializing select elements');
            setTimeout(initializeTaskFormSelects, 50);
        }
    });
    
    // Handle modal open events
    document.addEventListener('click', function(e) {
        // Check if the clicked element is a button that opens the task modal
        if (e.target.closest('[data-modal-target="new-modal"]') || 
            e.target.closest('[data-modal-toggle="new-modal"]')) {
            console.log('Task modal opening, will initialize select elements');
            setTimeout(initializeTaskFormSelects, 300); // Wait for modal to open
        }
    });
});