// Form debugging script

document.addEventListener('DOMContentLoaded', function() {
    console.log('Form debugging script loaded');
    
    // Function to log select element interactions
    function monitorSelectElements() {
        const selects = document.querySelectorAll('select');
        console.log(`Found ${selects.length} select elements on the page`);
        
        selects.forEach((select, index) => {
            console.log(`Select #${index}: id=${select.id}, name=${select.name}, disabled=${select.disabled}`);
            
            // Monitor disabled property changes
            const originalPropertyDescriptor = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'disabled');
            Object.defineProperty(select, 'disabled', {
                get: function() {
                    return originalPropertyDescriptor.get.call(this);
                },
                set: function(value) {
                    console.log(`Select #${index} (${select.id}) disabled property changing to: ${value}`);
                    console.log('Stack trace:', new Error().stack);
                    return originalPropertyDescriptor.set.call(this, value);
                }
            });
            
            // Monitor click events
            select.addEventListener('click', function(e) {
                console.log(`Select #${index} (${select.id}) clicked, disabled=${select.disabled}`);
                if (select.disabled) {
                    console.log('This select element is disabled, preventing interaction');
                }
            });
            
            // Monitor focus events
            select.addEventListener('focus', function(e) {
                console.log(`Select #${index} (${select.id}) focused, disabled=${select.disabled}`);
            });
        });
    }
    
    // Run the monitor function when the page loads and after HTMX content swaps
    monitorSelectElements();
    
    document.body.addEventListener('htmx:afterSwap', function() {
        console.log('HTMX content swapped, re-monitoring select elements');
        setTimeout(monitorSelectElements, 100); // Small delay to ensure DOM is updated
    });
    
    // Monitor for any browser extensions that might be interfering
    const originalAddEventListener = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
        if (type === 'change' && this.tagName === 'SELECT') {
            console.log(`External code adding change listener to select #${this.id}`);
            console.log('Stack trace:', new Error().stack);
        }
        return originalAddEventListener.call(this, type, listener, options);
    };
});