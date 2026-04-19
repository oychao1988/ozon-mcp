"""OZON page element selectors for browser automation."""


class LoginPage:
    """Login page selectors for OZON seller backend."""

    # Phone login page - email input (shown after clicking email login button)
    EMAIL_INPUT_TEXTBOX = 'input[autocomplete="email"]'
    EMAIL_INPUT_FALLBACK = 'input[type="email"]'

    # Email login button (on phone login page)
    EMAIL_LOGIN_BUTTON = 'button:has-text("使用邮箱登录")'

    # Login button (sends verification code)
    LOGIN_BUTTON = 'button:has-text("登录")'

    # OTP page - code input (generic text input without name)
    CODE_INPUT = 'input[type="text"]'

    # Submit/login button on OTP page
    SUBMIT_BUTTON = 'button:has-text("登录")'

    # Get new code button
    NEW_CODE_BUTTON = 'button:has-text("获取新验证码")'

    # Return home button
    RETURN_HOME_BUTTON = 'button:has-text("返回主页")'

    # Error messages
    ERROR_MESSAGE_INCORRECT_CODE = 'text="代码不正确"'
    ERROR_MESSAGE = '.error-message, .alert-error, [data-testid*="error"]'

    # CAPTCHA page detection
    CAPTCHA_PAGE_TITLES = ['доступ ограничен', 'access denied', 'antibot', 'challenge']
    LOGIN_SUCCESS_PATTERNS = ['seller.ozon', 'otp', 'ozonid']


class OTPPage:
    """OTP verification page selectors."""

    # Code input field
    CODE_INPUT = 'input[name="code"]'

    # Resend code button
    RESEND_BUTTON = 'button:has-text("获取新验证码")'

    # Timer display
    TIMER = '.timer, [class*="timer"]'

    # Error message
    ERROR_MESSAGE = 'text="代码不正确，请再试一次"'


class MarketingActionsPage:
    """Marketing actions page selectors for OZON seller promotions."""

    # Page container
    PAGE_CONTAINER = '.page-content, .main-content, .layout-content'

    # Product row - table structure in marketing actions page
    PRODUCT_ROW = 'table tbody tr, .products-table tr, [class*="products"] tr'

    # Product name element - first column or specific element
    PRODUCT_NAME = 'td:first-child .name, td:first-child a, .product-name, [class*="product"] [class*="name"]'

    # SKU element - second column
    SKU = 'td:nth-child(2), .sku, [class*="sku"], td:nth-child(3)'

    # Your price element - price column
    YOUR_PRICE = 'td:nth-child(5), .price, [class*="price"]:not([class*="min"]), td .price-current'

    # Min price element - minimum price column
    MIN_PRICE = 'td:nth-child(6), .min-price, [class*="min-price"], td .price-min'

    # Discount price before
    DISCOUNT_PRICE = 'td:nth-child(4), .discount-price, [class*="discount"], td .price-old'

    # Promotion type indicator
    PROMOTION_TYPE = '[class*="promotion"], [class*="action"], .badge'

    # Status indicator (有利/不利/中等)
    STATUS = 'td:last-child, [class*="status"], .state-badge'

    # Pagination container
    PAGINATION = '.pagination, [class*="pagination"], .pager'

    # Next page button
    NEXT_PAGE_BUTTON = '.next, button[class*="next"], a[rel="next"], .pagination__next'

    # Page number indicator
    PAGE_NUMBER = '.current-page, [class*="current"], input[type="number"]'

    # Loading spinner/indicator
    LOADING_INDICATOR = '.loading, [class*="loading"], .spinner, [class*="skeleton"]'

    # Empty state/no data message
    EMPTY_STATE = '.empty, [class*="empty"], .no-data, .placeholder-empty'


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
