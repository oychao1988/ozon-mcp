"""OZON page element selectors for browser automation."""


class LoginPage:
    """Login page selectors for OZON seller backend."""

    # Email input field - multiple selectors for robustness
    EMAIL_INPUT = 'input[name="email"], input[type="email"], input[placeholder*="email"], input[placeholder*="Email"], input[placeholder*="почта"], input[id*="email"]'

    # Send verification code button
    SEND_CODE_BUTTON = 'button[type="submit"], button:has-text("Получить код"), button:has-text("Send code"), button:has-text("获取验证码"), button[data-testid*="send"], .send-code-button'

    # Verification code input field
    CODE_INPUT = 'input[name="code"], input[type="text"][placeholder*="код"], input[placeholder*="code"], input[placeholder*="Code"], input[placeholder*="验证码"], input[id*="code"]'

    # Submit/login button
    SUBMIT_BUTTON = 'button[type="submit"], button:has-text("Войти"), button:has-text("Sign in"), button:has-text("Login"), button:has-text("登录"), button[data-testid*="login"], .login-button'

    # Error messages container
    ERROR_MESSAGE = '.error-message, .alert-error, .notification-error, [data-testid*="error"], .error-text, .form-error'


class MarketingActionsPage:
    """Marketing actions page selectors for OZON seller promotions."""

    # Page container
    PAGE_CONTAINER = '.marketing-actions-page, .promotions-container, [data-testid*="marketing"], .main-content, .page-content'

    # Product row/list item
    PRODUCT_ROW = '.product-row, .product-item, [data-testid*="product"], tr[data-product], .goods-item, .promotion-item'

    # Product name element
    PRODUCT_NAME = '.product-name, .product-title, [data-testid*="product-name"], .goods-name, .item-name, .product-info h3, .product-info a'

    # SKU element
    SKU = '.sku, [data-testid*="sku"], .product-sku, .goods-sku, .item-sku, td:nth-child(2), .sku-text'

    # Your price element
    YOUR_PRICE = '.your-price, [data-testid*="your-price"], .current-price, .seller-price, .price-current, .product-price'

    # Min price element
    MIN_PRICE = '.min-price, [data-testid*="min-price"], .minimal-price, .minimun-price, .price-min, .price-minimum'

    # Promotion type indicator
    PROMOTION_TYPE = '.promotion-type, [data-testid*="promotion"], .action-type, .promo-type, .campaign-type, .promotion-badge'

    # Status indicator
    STATUS = '.status, [data-testid*="status"], .product-status, .item-status, .state-badge, .status-label'

    # Pagination container
    PAGINATION = '.pagination, [data-testid*="pagination"], .page-navigation, .pager, .pagination-container'

    # Next page button
    NEXT_PAGE_BUTTON = '.pagination-next, [data-testid*="next-page"], button:has-text("Next"), button:has-text("Далее"), .next-page-btn, a[rel="next"]'

    # Page number indicator
    PAGE_NUMBER = '.page-number, [data-testid*="page-number"], .current-page, .page-active, input[type="number"][class*="page"]'

    # Loading spinner/indicator
    LOADING_INDICATOR = '.loading, [data-testid*="loading"], .spinner, .progress-indicator, .skeleton-loader, .loading-overlay'

    # Empty state/no data message
    EMPTY_STATE = '.empty-state, [data-testid*="empty"], .no-data, .no-results, .empty-list, .placeholder-empty'


class Common:
    """Common page elements shared across OZON pages."""

    # Modal dialog container
    MODAL = '.modal, [data-testid*="modal"], .dialog, .popup, .overlay, [role="dialog"], .modal-window'

    # Modal close button
    MODAL_CLOSE = '.modal-close, [data-testid*="close-modal"], .dialog-close, .popup-close, button:has-text("Close"), button:has-text("×"), .close-button'

    # Cookie banner/consent popup
    COOKIE_BANNER = '.cookie-banner, [data-testid*="cookie"], .cookies-consent, .gdpr-banner, .cookie-notice, .consent-popup'

    # Cookie accept button
    COOKIE_ACCEPT = '.cookie-accept, [data-testid*="accept-cookie"], button:has-text("Accept"), button:has-text("Принять"), button:has-text("同意"), .cookies-ok, .accept-all-cookies'
