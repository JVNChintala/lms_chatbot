# Production Deployment Checklist

## Pre-Deployment

### 1. Environment Configuration
- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate strong `SECRET_KEY` (min 32 characters)
- [ ] Verify `OPENAI_API_KEY` is production key
- [ ] Verify `CANVAS_TOKEN` has appropriate permissions
- [ ] Set `CANVAS_URL` to production Canvas instance
- [ ] Remove any test/demo credentials

### 2. Security Review
- [ ] Review all API endpoints for authentication
- [ ] Verify role-based access control is enforced
- [ ] Check for SQL injection vulnerabilities
- [ ] Validate all user inputs
- [ ] Review error messages (no sensitive data exposed)
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set secure cookie flags
- [ ] Implement rate limiting
- [ ] Add request size limits

### 3. Code Quality
- [ ] Run verification script: `python verify_system.py`
- [ ] Remove all debug print statements
- [ ] Remove unused imports
- [ ] Check for hardcoded credentials
- [ ] Review logging configuration
- [ ] Ensure proper error handling
- [ ] Code review completed
- [ ] All tests passing

### 4. Database
- [ ] Backup existing databases
- [ ] Consider PostgreSQL migration (from SQLite)
- [ ] Set up database backups
- [ ] Configure connection pooling
- [ ] Add database indexes for performance
- [ ] Test database failover

### 5. Performance
- [ ] Load test with expected traffic
- [ ] Configure worker processes (4+ for production)
- [ ] Set up Redis for caching (optional)
- [ ] Enable gzip compression
- [ ] Optimize database queries
- [ ] Configure request timeouts
- [ ] Set up CDN for static files

### 6. Monitoring
- [ ] Set up application monitoring (e.g., Sentry)
- [ ] Configure log aggregation (e.g., ELK stack)
- [ ] Set up uptime monitoring
- [ ] Configure alerts for errors
- [ ] Monitor API usage and costs
- [ ] Track response times
- [ ] Monitor database performance

### 7. Infrastructure
- [ ] Set up reverse proxy (nginx/Apache)
- [ ] Configure firewall rules
- [ ] Set up load balancer (if needed)
- [ ] Configure auto-scaling (if needed)
- [ ] Set up backup server
- [ ] Configure DNS
- [ ] Set up SSL certificates

## Deployment Steps

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip -y

# Install nginx
sudo apt install nginx -y

# Install supervisor (for process management)
sudo apt install supervisor -y
```

### 2. Application Deployment
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/lms_chatbot.git
cd lms_chatbot

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Test application
python verify_system.py
```

### 3. Nginx Configuration
```nginx
# /etc/nginx/sites-available/lms-chatbot
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 100M;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/lms-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Supervisor Configuration
```ini
# /etc/supervisor/conf.d/lms-chatbot.conf
[program:lms-chatbot]
directory=/path/to/lms_chatbot
command=/path/to/venv/bin/uvicorn lms_chatot.main:app --host 127.0.0.1 --port 8001 --workers 4
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/lms-chatbot.err.log
stdout_logfile=/var/log/lms-chatbot.out.log
```

```bash
# Start application
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start lms-chatbot
```

### 5. SSL Setup (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Post-Deployment

### 1. Verification
- [ ] Access application via domain
- [ ] Test login functionality
- [ ] Test chat functionality
- [ ] Test analytics display
- [ ] Test file upload
- [ ] Test all user roles (student, teacher, admin)
- [ ] Verify SSL certificate
- [ ] Check logs for errors

### 2. Monitoring Setup
- [ ] Configure monitoring dashboards
- [ ] Set up alert notifications
- [ ] Test alert system
- [ ] Document monitoring procedures

### 3. Backup Configuration
```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/backups/lms-chatbot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp /path/to/lms_chatbot/lms_chatot/conversations.db $BACKUP_DIR/conversations_$DATE.db
cp /path/to/lms_chatbot/lms_chatot/usage_tracker.db $BACKUP_DIR/usage_tracker_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
```

```bash
# Add to crontab
0 2 * * * /path/to/backup_script.sh
```

### 4. Documentation
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document rollback procedure
- [ ] Create user guide
- [ ] Document API endpoints

## Rollback Procedure

### Quick Rollback
```bash
# Stop application
sudo supervisorctl stop lms-chatbot

# Restore previous version
cd /path/to/lms_chatbot
git checkout previous-stable-tag

# Restart application
sudo supervisorctl start lms-chatbot
```

### Database Rollback
```bash
# Stop application
sudo supervisorctl stop lms-chatbot

# Restore database
cp /backups/lms-chatbot/conversations_YYYYMMDD.db /path/to/lms_chatbot/lms_chatot/conversations.db
cp /backups/lms-chatbot/usage_tracker_YYYYMMDD.db /path/to/lms_chatbot/lms_chatot/usage_tracker.db

# Restart application
sudo supervisorctl start lms-chatbot
```

## Maintenance

### Daily
- [ ] Check application logs
- [ ] Monitor error rates
- [ ] Check disk space
- [ ] Verify backups completed

### Weekly
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Review user feedback
- [ ] Analyze usage patterns

### Monthly
- [ ] Update dependencies
- [ ] Review and optimize database
- [ ] Test backup restoration
- [ ] Security audit
- [ ] Performance optimization

## Troubleshooting

### Application Won't Start
```bash
# Check logs
sudo tail -f /var/log/lms-chatbot.err.log

# Check supervisor status
sudo supervisorctl status lms-chatbot

# Restart application
sudo supervisorctl restart lms-chatbot
```

### High Memory Usage
```bash
# Check memory
free -h

# Check process memory
ps aux | grep uvicorn

# Restart application
sudo supervisorctl restart lms-chatbot
```

### Database Locked
```bash
# Check for locks
lsof /path/to/conversations.db

# Kill blocking process if needed
kill -9 <PID>

# Restart application
sudo supervisorctl restart lms-chatbot
```

### SSL Certificate Issues
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Restart nginx
sudo systemctl restart nginx
```

## Performance Tuning

### Uvicorn Workers
```bash
# Adjust based on CPU cores
# Formula: (2 x CPU cores) + 1
uvicorn lms_chatot.main:app --workers 9  # For 4 cores
```

### Database Optimization
```sql
-- Add indexes
CREATE INDEX idx_conversations_user ON conversations(canvas_user_id);
CREATE INDEX idx_messages_conv ON messages(conversation_id);
CREATE INDEX idx_usage_user ON usage_logs(user_id);
```

### Nginx Caching
```nginx
# Add to nginx config
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g;

location /static/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 1d;
}
```

## Security Hardening

### Firewall Rules
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Rate Limiting
```python
# Add to main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/inference")
@limiter.limit("10/minute")
async def inference(req: InferenceRequest):
    # ... existing code
```

### Security Headers
```nginx
# Add to nginx config
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

## Support Contacts

- **Technical Lead**: [email]
- **DevOps**: [email]
- **Canvas Admin**: [email]
- **On-Call**: [phone]

## Emergency Procedures

### Critical Issue
1. Assess impact
2. Notify stakeholders
3. Enable maintenance mode
4. Investigate and fix
5. Test thoroughly
6. Deploy fix
7. Monitor closely
8. Post-mortem

### Data Breach
1. Isolate affected systems
2. Notify security team
3. Preserve evidence
4. Assess scope
5. Notify affected users
6. Implement fixes
7. Document incident

---

**Last Updated**: [Date]
**Version**: 2.0.0
**Status**: Production Ready ✅
