# Security Policy

## Supported Versions

We actively support the following versions of AmaniQuery with security updates:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest | :x:                |

We recommend always using the latest version of AmaniQuery to ensure you have the most recent security patches.

## Reporting a Vulnerability

We take the security of AmaniQuery seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **Email**: Send an email to [INSERT SECURITY EMAIL] with the subject line "Security Vulnerability: [Brief Description]"
2. **GitHub Security Advisory**: Use GitHub's private vulnerability reporting feature (if enabled)
3. **Private Contact**: Contact the maintainers directly through GitHub (if you have access)

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Impact**: The potential impact of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Affected Versions**: Which versions of AmaniQuery are affected
- **Suggested Fix**: If you have a suggested fix, please include it (optional but appreciated)
- **Proof of Concept**: If possible, include a proof of concept (be careful not to exploit the vulnerability)

### What to Expect

1. **Acknowledgment**: You will receive an acknowledgment within 48 hours
2. **Initial Assessment**: We will provide an initial assessment within 7 days
3. **Updates**: We will keep you informed of our progress
4. **Resolution**: We will work to resolve the issue as quickly as possible
5. **Disclosure**: After the issue is resolved, we may publicly disclose the vulnerability (with your permission)

### Disclosure Policy

- We will work with you to coordinate public disclosure of the vulnerability
- We will credit you for discovering the vulnerability (if you wish)
- We will not disclose your identity without your explicit permission
- We aim to disclose vulnerabilities within 90 days of the initial report, or sooner if a patch is available

## Security Best Practices

When using AmaniQuery, please follow these security best practices:

### API Keys and Secrets

- **Never commit API keys or secrets to version control**
- Use environment variables or secure secret management systems
- Rotate API keys regularly
- Use separate API keys for development and production

### Environment Variables

- Store sensitive configuration in `.env` files (not committed to git)
- Use strong, unique passwords for database connections
- Keep your `.env` file secure and never share it

### Dependencies

- Keep all dependencies up to date
- Review Dependabot security alerts regularly
- Run `npm audit` and `pip check` regularly

### Database Security

- Use strong database passwords
- Restrict database access to necessary IPs only
- Enable SSL/TLS for database connections when possible
- Regularly backup your database

### API Security

- Use HTTPS in production
- Implement rate limiting
- Validate and sanitize all user inputs
- Use authentication and authorization where appropriate

### Docker Security

- Keep Docker images updated
- Scan images for vulnerabilities
- Use non-root users in containers when possible
- Limit container resources

## Known Security Considerations

### Data Sources

AmaniQuery crawls and processes data from various sources. Be aware that:

- Crawled data may contain sensitive information
- Always review and sanitize data before storing
- Respect `robots.txt` and rate limits
- Be mindful of copyright and data usage rights

### LLM Integration

When using LLM providers (OpenAI, Anthropic, Moonshot, etc.):

- API keys are sensitive and must be protected
- Review data sent to LLM providers (may be logged)
- Be aware of rate limits and costs
- Use appropriate model configurations for your use case

### SMS Gateway

When using the SMS gateway (Africa's Talking):

- Protect your API credentials
- Implement rate limiting for SMS endpoints
- Monitor SMS usage and costs
- Be mindful of SMS content and regulations

## Security Updates

Security updates will be released as:

- **Patch versions** (e.g., 1.0.0 → 1.0.1) for critical security fixes
- **Minor versions** (e.g., 1.0.0 → 1.1.0) for security improvements
- **Security advisories** published on GitHub

Subscribe to repository notifications to be alerted about security updates.

## Security Audit

We periodically conduct security audits of:

- Dependencies (via Dependabot and manual reviews)
- Code (via CodeQL and manual reviews)
- Infrastructure (Docker images, deployment configurations)
- API endpoints and authentication mechanisms

## Contact

For security-related questions or concerns, please contact:

- **Security Email**: [INSERT SECURITY EMAIL]
- **GitHub Issues**: Use the "Security" label for non-sensitive security questions
- **Maintainers**: Contact project maintainers directly

---

**Thank you for helping keep AmaniQuery secure!**

