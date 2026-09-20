// Debug script to check loading order and issues

// Check if jQuery is loaded immediately
console.log('Debug: jQuery loaded at script execution?', typeof jQuery !== 'undefined');

// Fallback if jQuery is not loaded
if (typeof jQuery === 'undefined') {
    console.error('CRITICAL: jQuery is not loaded! Check script loading order.');
    
    // Try to wait for jQuery
    let jqueryWaitCount = 0;
    const jqueryWaitInterval = setInterval(function() {
        jqueryWaitCount++;
        if (typeof jQuery !== 'undefined') {
            console.log('jQuery loaded after', jqueryWaitCount * 100, 'ms');
            clearInterval(jqueryWaitInterval);
            initializeAfterJQuery();
        } else if (jqueryWaitCount > 50) { // Wait max 5 seconds
            console.error('jQuery failed to load after 5 seconds');
            clearInterval(jqueryWaitInterval);
        }
    }, 100);
} else {
    console.log('Debug: jQuery is available immediately');
    
    // Check document ready
    jQuery(document).ready(function() {
        console.log('Debug: Document ready fired');
        console.log('Debug: Current page:', window.location.pathname);
        
        // Check for required elements
        if (jQuery('#sites-tbody').length) {
            console.log('Debug: Sites table found');
        }
        if (jQuery('#rules-container').length) {
            console.log('Debug: Rules container found');
        }
        
        // Check API endpoints
        console.log('Debug: Testing API endpoints...');
        testApiEndpoint('/api/sites', 'Sites API');
        testApiEndpoint('/api/rules', 'Rules API');
        testApiEndpoint('/api/scan/configs', 'Configs API');
    });
}

function initializeAfterJQuery() {
    console.log('Debug: Initializing after jQuery load');
    jQuery(document).ready(function() {
        console.log('Debug: Document ready after delayed jQuery load');
    });
}

function testApiEndpoint(endpoint, name) {
    jQuery.ajax({
        url: endpoint,
        method: 'GET',
        success: function(data) {
            console.log('✓ Debug:', name, 'working, returned', Array.isArray(data) ? data.length + ' items' : 'data');
        },
        error: function(xhr, status, error) {
            console.error('✗ Debug:', name, 'failed:', error);
        }
    });
}
