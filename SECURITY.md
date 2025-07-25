# Security Guidelines for Ragify

This document outlines security best practices for deploying and using the Ragify RAG framework.

## 🔒 API Keys and Credentials

### OpenAI API Keys
- **Never commit API keys to version control**
- Store in environment variables or secure configuration management
- Use `.env` files for local development (already in `.gitignore`)
- Rotate keys regularly

### Google Cloud Service Accounts
- **Never commit service account JSON files to version control**
- Use Google Cloud IAM best practices
- Limit service account permissions to minimum required
- Store credentials securely using Google Secret Manager in production

## 🛡️ Production Security

### Environment Configuration
```bash
# Production environment variables
FLASK_DEBUG=False
FLASK_ENV=production
```

### Rate Limiting
- Default: 60 requests per minute per IP
- Burst limit: 10 requests
- Configure in `config.yaml`:
```yaml
server:
  rate_limit:
    enabled: true
    requests_per_minute: 60
    burst_limit: 10
```

### Input Validation
- Maximum message length: 10,000 characters
- JSON payload validation
- Content-Type enforcement

### HTTPS Configuration
- Always use HTTPS in production
- Configure SSL/TLS certificates
- Use reverse proxy (nginx/Apache) for SSL termination

## 🔍 Monitoring and Logging

### Security Logging
- All API requests are logged
- Failed authentication attempts logged
- Rate limit violations logged
- Error details sanitized in responses

### Recommended Monitoring
- Monitor for unusual request patterns
- Track API usage and quotas
- Set up alerts for error rates
- Monitor vector database access

## 🚀 Deployment Security

### Docker Security
```dockerfile
# Use non-root user
USER 1000:1000

# Limit container capabilities
--cap-drop=ALL
--cap-add=NET_BIND_SERVICE
```

### Network Security
- Use private networks for internal communication
- Restrict database access to application only
- Configure firewall rules appropriately

### Data Security
- Encrypt data at rest (Qdrant supports encryption)
- Use secure communication channels
- Implement backup encryption
- Consider data retention policies

## 🔧 Configuration Security

### Secure Defaults
- Debug mode disabled by default
- Rate limiting enabled
- Input validation enforced
- Error messages sanitized

### Environment-Specific Configs
```yaml
# Development
server:
  debug: true
  
# Production  
server:
  debug: false
  rate_limit:
    enabled: true
```

## 📋 Security Checklist

### Before Deployment
- [ ] Remove all hardcoded credentials
- [ ] Enable HTTPS
- [ ] Configure rate limiting
- [ ] Set up monitoring
- [ ] Review firewall rules
- [ ] Test input validation
- [ ] Verify error handling
- [ ] Check log configuration

### Regular Maintenance
- [ ] Update dependencies regularly
- [ ] Monitor security advisories
- [ ] Review access logs
- [ ] Rotate API keys
- [ ] Update SSL certificates
- [ ] Backup security configurations

## 🚨 Incident Response

### If Credentials Are Compromised
1. Immediately revoke/rotate affected credentials
2. Review access logs for unauthorized usage
3. Update all affected systems
4. Monitor for suspicious activity

### Reporting Security Issues
- Create a private issue in the repository
- Include detailed description and reproduction steps
- Do not disclose vulnerabilities publicly until fixed

## 📚 Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [OpenAI API Security Guidelines](https://platform.openai.com/docs/guides/safety-best-practices)