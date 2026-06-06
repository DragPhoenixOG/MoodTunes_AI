// MoodTunes AI – Security Filter
// Never capture passwords, tokens, banking info, or OTPs

const BLOCKED_DOMAINS = [
  /bankof/, /chase\.com/, /wellsfargo/, /citibank/, /hsbc/,
  /paypal\.com/, /stripe\.com/, /braintree/, /square\.com/,
  /accounts\.google\.com/, /login\.microsoftonline\.com/,
  /signin\.aws\.amazon\.com/, /auth0\.com/, /okta\.com/,
  /twilio\.com/, /authy\.com/,
];

const BLOCKED_TITLE_PATTERNS = [
  /sign in/i, /log in/i, /verify/i, /two.factor/i,
  /otp/i, /authentication/i, /payment/i, /checkout/i,
  /billing/i, /banking/i,
];

const SENSITIVE_INPUT_TYPES = new Set([
  'password', 'tel', 'credit-card', 'cc-number',
  'cc-csc', 'cc-exp',
]);

export const SecurityFilter = {
  isSensitivePage(hostname, title = '') {
    if (BLOCKED_DOMAINS.some(re => re.test(hostname))) return true;
    if (BLOCKED_TITLE_PATTERNS.some(re => re.test(title))) return true;
    return false;
  },

  sanitize(text) {
    if (!text) return '';
    // Remove anything that looks like a password field value
    let out = text;
    // Remove OTP-like tokens (4-8 consecutive digits)
    out = out.replace(/\b\d{4,8}\b/g, '[redacted]');
    // Remove credit card patterns
    out = out.replace(/\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g, '[card-redacted]');
    // Remove JWT tokens
    out = out.replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, '[token-redacted]');
    // Remove session cookies / bearer tokens
    out = out.replace(/Bearer\s+[A-Za-z0-9_.-]+/gi, '[bearer-redacted]');
    // Trim excessively repeated whitespace
    out = out.replace(/\s{3,}/g, ' ').trim();
    return out;
  },

  isInputSafe(inputElement) {
    const type = (inputElement.type || '').toLowerCase();
    const autoComplete = (inputElement.autocomplete || '').toLowerCase();
    if (SENSITIVE_INPUT_TYPES.has(type)) return false;
    if (SENSITIVE_INPUT_TYPES.has(autoComplete)) return false;
    return true;
  },
};
