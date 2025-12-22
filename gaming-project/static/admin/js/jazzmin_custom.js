/**
 * Custom Jazzmin JavaScript for Gaming Analytics
 * Adds enhanced functionality and gaming-themed features
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Add gaming theme enhancements
    function initGamingTheme() {
        // Add gaming icons to specific sections
        const gamingIcons = {
            'Dashboard': 'fas fa-gamepad',
            'Users': 'fas fa-user-friends',
            'Analytics': 'fas fa-chart-line',
            'Reports': 'fas fa-file-chart',
            'Settings': 'fas fa-cogs'
        };
        
        // Apply icons to menu items
        document.querySelectorAll('.nav-sidebar .nav-link').forEach(link => {
            const text = link.querySelector('.nav-link-text')?.textContent?.trim();
            if (text && gamingIcons[text]) {
                const icon = link.querySelector('.nav-icon');
                if (icon) {
                    icon.className = `nav-icon ${gamingIcons[text]}`;
                }
            }
        });
        
        // Add current time display
        const navbar = document.querySelector('.main-header.navbar');
        if (navbar) {
            const timeElement = document.createElement('div');
            timeElement.id = 'current-time';
            timeElement.className = 'navbar-text ml-auto';
            timeElement.style.cssText = 'color: #5a5c69; font-size: 0.875rem; font-weight: 500;';
            navbar.appendChild(timeElement);
            
            function updateTime() {
                const now = new Date();
                const timeString = now.toLocaleString('en-US', {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true
                });
                timeElement.textContent = timeString;
            }
            
            updateTime();
            setInterval(updateTime, 60000);
        }
    }
    
    // Enhanced form interactions
    function initFormEnhancements() {
        // Add loading states to submit buttons
        document.querySelectorAll('input[type="submit"], button[type="submit"]').forEach(button => {
            button.addEventListener('click', function() {
                if (!this.classList.contains('btn-secondary')) {
                    this.disabled = true;
                    const originalText = this.textContent;
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                    
                    // Re-enable after 5 seconds as fallback
                    setTimeout(() => {
                        this.disabled = false;
                        this.textContent = originalText;
                    }, 5000);
                }
            });
        });
        
        // Enhanced field focus effects
        document.querySelectorAll('.form-control').forEach(field => {
            field.addEventListener('focus', function() {
                this.closest('.form-group')?.classList.add('focused');
            });
            
            field.addEventListener('blur', function() {
                this.closest('.form-group')?.classList.remove('focused');
            });
        });
    }
    
    // Add confirmation for destructive actions
    function initSafetyConfirmations() {
        document.querySelectorAll('a[href*="delete"], .deletelink, input[value*="Delete"]').forEach(element => {
            element.addEventListener('click', function(e) {
                const confirmMsg = 'Are you sure you want to delete this item? This action cannot be undone.';
                if (!confirm(confirmMsg)) {
                    e.preventDefault();
                    return false;
                }
            });
        });
        
        // Bulk actions confirmation
        const actionSelect = document.querySelector('select[name="action"]');
        if (actionSelect) {
            actionSelect.addEventListener('change', function() {
                if (this.value.includes('delete')) {
                    const form = this.closest('form');
                    if (form) {
                        form.addEventListener('submit', function(e) {
                            const checkedBoxes = form.querySelectorAll('input[name="_selected_action"]:checked');
                            if (checkedBoxes.length > 0) {
                                const confirmMsg = `Are you sure you want to delete ${checkedBoxes.length} item(s)? This action cannot be undone.`;
                                if (!confirm(confirmMsg)) {
                                    e.preventDefault();
                                    return false;
                                }
                            }
                        });
                    }
                }
            });
        }
    }
    
    // Add keyboard shortcuts
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + S for save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                const saveButton = document.querySelector('input[type="submit"][value*="Save"], button[type="submit"]');
                if (saveButton) {
                    saveButton.click();
                }
            }
            
            // Escape to go back or cancel
            if (e.key === 'Escape') {
                const cancelLink = document.querySelector('.btn-secondary, .cancel, a[href*="changelist"]');
                if (cancelLink) {
                    window.location.href = cancelLink.href;
                }
            }
            
            // Ctrl/Cmd + Enter for save and continue
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                const saveAndContinueButton = document.querySelector('input[value*="Save and continue"]');
                if (saveAndContinueButton) {
                    saveAndContinueButton.click();
                }
            }
        });
    }
    
    // Enhanced table interactions
    function initTableEnhancements() {
        // Highlight table rows on hover
        document.querySelectorAll('.table tbody tr').forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = 'rgba(139, 0, 0, 0.05)';
                this.style.transform = 'scale(1.01)';
                this.style.transition = 'all 0.2s ease';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
                this.style.transform = '';
            });
        });
        
        // Make entire row clickable for change links
        document.querySelectorAll('.table tbody tr').forEach(row => {
            const changeLink = row.querySelector('a[href*="/change/"]');
            if (changeLink) {
                row.style.cursor = 'pointer';
                row.addEventListener('click', function(e) {
                    // Don't trigger if clicking on a checkbox or other interactive element
                    if (!e.target.matches('input, a, button')) {
                        window.location.href = changeLink.href;
                    }
                });
            }
        });
    }
    
    // Add notification system
    function initNotifications() {
        // Create notification container
        const notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
        `;
        document.body.appendChild(notificationContainer);
        
        // Global notification function
        window.showNotification = function(message, type = 'info', duration = 4000) {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show`;
            notification.style.cssText = `
                margin-bottom: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            `;
            
            notification.innerHTML = `
                ${message}
                <button type="button" class="close" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            `;
            
            notificationContainer.appendChild(notification);
            
            // Auto-dismiss
            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, duration);
            
            // Manual dismiss
            notification.querySelector('.close').addEventListener('click', function() {
                notification.style.opacity = '0';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            });
        };
        
        // Show success notification on form save
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('_changelist_filters') || window.location.href.includes('?saved=1')) {
            showNotification('Changes saved successfully!', 'success');
        }
    }
    
    // Add progressive enhancement
    function initProgressiveEnhancements() {
        // Lazy load images if any
        const images = document.querySelectorAll('img[data-src]');
        if (images.length && 'IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });
            
            images.forEach(img => imageObserver.observe(img));
        }
        
        // Add smooth scrolling
        document.documentElement.style.scrollBehavior = 'smooth';
        
        // Add focus management for accessibility
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'sr-only sr-only-focusable';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            z-index: 10000;
            text-decoration: none;
        `;
        skipLink.addEventListener('focus', function() {
            this.style.top = '6px';
        });
        skipLink.addEventListener('blur', function() {
            this.style.top = '-40px';
        });
        document.body.insertBefore(skipLink, document.body.firstChild);
    }
    
    // Initialize all enhancements
    initGamingTheme();
    initFormEnhancements();
    initSafetyConfirmations();
    initKeyboardShortcuts();
    initTableEnhancements();
    initNotifications();
    initProgressiveEnhancements();
    
    // Show welcome message for new sessions
    if (sessionStorage.getItem('adminWelcomeShown') !== 'true') {
        setTimeout(() => {
            showNotification('🎮 Welcome to Gaming Analytics Admin! Use Ctrl+S to save, Esc to cancel.', 'info', 6000);
            sessionStorage.setItem('adminWelcomeShown', 'true');
        }, 1000);
    }
});

// Add some CSS for enhanced interactions
const style = document.createElement('style');
style.textContent = `
    .form-group.focused {
        transform: translateY(-1px);
        transition: transform 0.2s ease;
    }
    
    .sr-only:not(.sr-only-focusable) {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        border: 0 !important;
    }
    
    .table tbody tr {
        transition: all 0.2s ease;
    }
    
    @media (prefers-reduced-motion: reduce) {
        * {
            transition: none !important;
            animation: none !important;
        }
    }
`;
document.head.appendChild(style);