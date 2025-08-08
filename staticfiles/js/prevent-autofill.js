/**
 * This script prevents browser extensions from interfering with select elements
 * by adding protection against external manipulation of the disabled property
 * Completely rewritten to avoid property redefinition conflicts
 */
document.addEventListener('DOMContentLoaded', function() {
    // Function to protect select elements from external manipulation
    function protectSelectElements() {
        const selects = document.querySelectorAll('select');
        
        selects.forEach(select => {
            // Skip if the element already has a data-protected attribute
            if (select.hasAttribute('data-protected')) return;
            
            // Store the initial state
            select.setAttribute('data-disabled', select.disabled ? 'true' : 'false');
            
            // Remove any disabled attribute
            select.removeAttribute('disabled');
            
            // Add event listeners to prevent disabling
            select.addEventListener('click', function(e) {
                // Ensure the element is not disabled
                if (this.hasAttribute('disabled')) {
                    this.removeAttribute('disabled');
                    console.log('Prevented select element from being disabled on click');
                }
                e.stopPropagation();
            }, true);
            
            select.addEventListener('focus', function(e) {
                // Ensure the element is not disabled
                if (this.hasAttribute('disabled')) {
                    this.removeAttribute('disabled');
                    console.log('Prevented select element from being disabled on focus');
                }
                e.stopPropagation();
            }, true);
            
            // Create a MutationObserver to watch for disabled attribute changes
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.attributeName === 'disabled') {
                        // Check if the call is coming from our own code
                        const stack = new Error().stack || '';
                        const isInternalCall = stack.includes('htmx:beforeRequest') || 
                                              stack.includes('htmx:afterRequest') ||
                                              stack.includes('disableFormElements') ||
                                              stack.includes('enableFormElements');
                        
                        if (!isInternalCall) {
                            // Remove the disabled attribute if it was added externally
                            select.removeAttribute('disabled');
                            console.warn('Blocked attempt to disable select element by external code');
                        }
                    }
                });
            });
            
            // Start observing the select element
            observer.observe(select, { attributes: true });
            
            // Mark as protected
            select.setAttribute('data-protected', 'true');
        });
    }

    // Apply protection when page loads
    protectSelectElements();

    // Re-apply protection after HTMX content swaps
    document.body.addEventListener('htmx:afterSwap', function() {
        setTimeout(protectSelectElements, 10);
    });
});