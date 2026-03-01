# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Studymate, please report it responsibly:

**Please DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, email: **fgmelofilho@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You should receive a response within 48 hours. We'll work with you to understand and address the issue.

## Supported Versions

Currently, we support the latest version only. Security updates will be released as patches.

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Considerations

### Local AI Model (Recommended)

When using Ollama (local inference), Studymate provides enhanced security:

✅ **All data stays on your device** - No external API calls  
✅ **No data collection** - We don't track or log user data  
✅ **Offline operation** - Works without internet after setup  
✅ **Full data ownership** - You control all your study materials  

### Cloud AI Model (Optional)

When using OpenAI or other cloud providers:

⚠️ **API Keys**: Store in `.env` file, never commit to git  
⚠️ **Data transmission**: Your queries and documents are sent to the provider's servers  
⚠️ **Third-party policies**: Subject to the provider's privacy policy and terms  

### Best Practices

1. **Never commit secrets**
   - Keep `.env` in `.gitignore`
   - Use `.env.example` for documentation
   - Rotate API keys if accidentally exposed

2. **Secure your SECRET_KEY**
   - Generate a strong random key for production
   - Never use the default development key in production
   - Rotate periodically

3. **Database security**
   - SQLite database is stored locally in `instance/` directory
   - Ensure proper file permissions on production systems
   - Backup database regularly

4. **PDF uploads**
   - Files stored locally in `instance/uploads/`
   - Validate file types before processing
   - Consider file size limits (default: 50MB)

5. **Dependencies**
   - Keep dependencies updated: `pip install --upgrade -r requirements.txt`
   - Review security advisories for Python packages
   - Use virtual environments to isolate dependencies

## Known Limitations

- **Local storage only**: No built-in encryption for stored PDFs or database
- **Single-user design**: Not designed for multi-tenant environments
- **No authentication hardening**: Basic Flask-Login implementation
- **PDF processing**: Relies on PyPDF2 which may have vulnerabilities in complex PDFs

## Secure Configuration

### Production Deployment (if you choose to self-host)

```bash
# Generate a strong SECRET_KEY
python -c 'import secrets; print(secrets.token_hex(32))'

# Set in .env
SECRET_KEY=your-generated-key-here

# Ensure proper permissions
chmod 600 .env
chmod 700 instance/
```

### Recommended Reading

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [Python Security Guide](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## Disclosure Policy

We follow responsible disclosure:

1. Report received and acknowledged (48 hours)
2. Issue confirmed and assessed (1 week)
3. Patch developed and tested (timeline varies)
4. Security advisory published (after patch released)
5. Credit given to reporter (if desired)

## Security Updates

Security patches will be announced via:
- GitHub Security Advisories
- Release notes
- README updates

## Questions?

For security-related questions that are not vulnerabilities, open a GitHub Discussion or email the maintainer.

---

**Remember**: When using local AI (Ollama), your data never leaves your computer, providing the highest level of privacy and security for your study materials.
