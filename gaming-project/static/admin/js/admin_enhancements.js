/**
 * Modern Admin Enhancements for Gaming Analytics
 * Adds interactive features and improved UX to Django Admin
 */

(function($) {
    'use strict';

    $(document).ready(function() {
        
        // Add loading states to buttons
        $('input[type="submit"], .button').on('click', function(e) {
            const $btn = $(this);
            if (!$btn.hasClass('cancel-link')) {
                const originalText = $btn.val() || $btn.text();
                $btn.prop('disabled', true);
                if ($btn.is('input')) {
                    $btn.val('Processing...');
                } else {
                    $btn.html('<i class="fas fa-spinner fa-spin"></i> Processing...');
                }
                
                // Re-enable after 5 seconds as fallback
                setTimeout(function() {
                    $btn.prop('disabled', false);
                    if ($btn.is('input')) {
                        $btn.val(originalText);
                    } else {
                        $btn.text(originalText);
                    }
                }, 5000);
            }
        });

        // Enhance tables with hover effects
        $('.results table tbody tr').hover(
            function() {
                $(this).addClass('highlight');
            },
            function() {
                $(this).removeClass('highlight');
            }
        );

        // Add smooth animations
        $('.module').each(function() {
            $(this).css({
                'opacity': '0',
                'transform': 'translateY(20px)'
            }).animate({
                'opacity': '1'
            }, 300).css('transform', 'translateY(0px)');
        });

        // Enhance filter sidebar
        $('#changelist-filter h3').each(function() {
            const $this = $(this);
            $this.css('cursor', 'pointer').on('click', function() {
                $this.next('ul').slideToggle(200);
            });
        });

        // Add search enhancement
        if ($('#searchbar').length) {
            $('#searchbar').attr('placeholder', 'Search records...');
        }

        // Add tooltips to action buttons
        $('.action-select').attr('title', 'Select this item for batch actions');
        $('.action-checkbox-column input').attr('title', 'Select all visible items');

        // Enhance messages with auto-hide
        $('.messagelist li').each(function() {
            const $message = $(this);
            setTimeout(function() {
                $message.fadeOut(500, function() {
                    $message.remove();
                });
            }, 5000);
        });

        // Add confirmation for dangerous actions
        $('a[href*="delete"], input[value*="delete"], .deletelink').on('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
                return false;
            }
        });

        // Enhance form fields
        $('input[type="text"], input[type="email"], input[type="password"], textarea, select').each(function() {
            const $field = $(this);
            const $label = $('label[for="' + $field.attr('id') + '"]');
            
            if ($label.length && !$field.attr('placeholder')) {
                $field.attr('placeholder', $label.text().replace('*', '').trim());
            }
        });

        // Add keyboard shortcuts
        $(document).on('keydown', function(e) {
            // Ctrl+S or Cmd+S for save
            if ((e.ctrlKey || e.metaKey) && e.which === 83) {
                e.preventDefault();
                $('.default[type="submit"]').click();
            }
            
            // Escape to cancel
            if (e.which === 27) {
                $('.cancel, .cancel-link').first().click();
            }
        });

        // Add dark mode toggle (if user prefers)
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            $('body').addClass('dark-mode');
        }

        // Responsive table enhancement
        $('.results table').wrap('<div class="table-responsive"></div>');

        // Add loading indicator for AJAX requests
        $(document).ajaxStart(function() {
            $('body').addClass('loading');
        }).ajaxStop(function() {
            $('body').removeClass('loading');
        });

    });

    // Custom admin utilities
    window.GamingAnalyticsAdmin = {
        showNotification: function(message, type = 'info') {
            const notification = $('<div class="notification notification-' + type + '">' + message + '</div>');
            $('body').append(notification);
            notification.fadeIn(300);
            
            setTimeout(function() {
                notification.fadeOut(300, function() {
                    notification.remove();
                });
            }, 3000);
        },
        
        confirmAction: function(message, callback) {
            if (confirm(message)) {
                callback();
            }
        }
    };

})(django.jQuery);

// Add CSS for enhancements
const style = document.createElement('style');
style.textContent = `
    .highlight {
        background-color: rgba(139, 0, 0, 0.05) !important;
    }
    
    .loading {
        cursor: wait !important;
    }
    
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 16px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 9999;
        display: none;
    }
    
    .notification-info {
        background-color: #3B82F6;
    }
    
    .notification-success {
        background-color: #10B981;
    }
    
    .notification-warning {
        background-color: #F59E0B;
    }
    
    .notification-error {
        background-color: #EF4444;
    }
    
    .table-responsive {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    @media (max-width: 768px) {
        .table-responsive table {
            min-width: 600px;
        }
    }
`;
document.head.appendChild(style);