/**
 * GDPR cookie consent banner.
 *
 * Strictly-necessary cookies (session, CSRF, remember-me) are set regardless
 * and disclosed in /privacy. This banner records an opt-in choice for any
 * non-essential cookies before they may be set. Use
 * `window.cwacConsent.allowsOptional()` to gate optional features.
 */
(function () {
    var CONSENT_COOKIE = 'cwac_cookie_consent';
    var CONSENT_DAYS = 365;

    function getConsent() {
        var match = document.cookie.match(new RegExp('(?:^|; )' + CONSENT_COOKIE + '=([^;]*)'));
        return match ? decodeURIComponent(match[1]) : null;
    }

    function setConsent(value) {
        var maxAge = CONSENT_DAYS * 24 * 60 * 60;
        document.cookie = CONSENT_COOKIE + '=' + encodeURIComponent(value) +
            '; max-age=' + maxAge + '; path=/; SameSite=Lax' +
            (location.protocol === 'https:' ? '; Secure' : '');
    }

    window.cwacConsent = {
        get: getConsent,
        allowsOptional: function () { return getConsent() === 'accepted'; },
        reset: function () {
            document.cookie = CONSENT_COOKIE + '=; max-age=0; path=/';
            location.reload();
        }
    };

    function hideBanner() {
        var banner = document.getElementById('cookie-consent-banner');
        if (banner) { banner.remove(); }
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (getConsent()) { return; }

        var banner = document.getElementById('cookie-consent-banner');
        if (!banner) { return; }
        banner.hidden = false;

        banner.querySelector('[data-consent="accepted"]').addEventListener('click', function () {
            setConsent('accepted');
            hideBanner();
        });
        banner.querySelector('[data-consent="essential"]').addEventListener('click', function () {
            setConsent('essential');
            hideBanner();
        });
    });
})();
