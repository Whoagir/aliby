# Deployment Guide - Alias/Taboo Game

## Quick Deploy (Ubuntu Server with Cloud-Init)

### 1. Prepare Your Repository

```bash
# On your local machine
cd c:\Users\user\Desktop\aliby
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/aliby.git
git push -u origin main
```

### 2. Create Server with Cloud-Init

1. Rent server (Ubuntu 24.04, 1GB RAM minimum)
2. Upload `cloud-init.yaml` during server creation
3. Wait 3-5 minutes for setup to complete

### 3. Connect and Deploy

```bash
# SSH into server (replace YOUR_IP)
ssh root@YOUR_IP
# or
ssh aliby@YOUR_IP

# Clone repository
cd /opt/aliby
git clone https://github.com/YOUR_USERNAME/aliby.git .

# Start application
docker compose up -d

# Check status
docker compose ps
docker compose logs -f
```

### 4. Access Your Game

Open in browser:
```
http://YOUR_IP:8888
```

---

## Manual Setup (if cloud-init didn't work)

### Install Docker

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Logout and login again
exit
```

### Setup Swap (Important for 1GB RAM!)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Setup Firewall

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 8888/tcp # Game
sudo ufw enable
```

### Deploy Application

```bash
# Clone repository
mkdir -p /opt/aliby
cd /opt/aliby
git clone https://github.com/YOUR_USERNAME/aliby.git .

# Start application
docker compose up -d

# Check logs
docker compose logs -f
```

---

## Useful Commands

### Application Management

```bash
# View status
docker compose ps

# View logs
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend

# Restart services
docker compose restart
docker compose restart backend

# Stop application
docker compose down

# Start application
docker compose up -d

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d
```

### Updates

```bash
# Pull latest code
cd /opt/aliby
git pull

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d
```

### Monitoring

```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check memory
free -h

# Check swap
swapon --show
```

### Troubleshooting

```bash
# If backend fails to start
docker compose logs backend

# If out of memory
free -h
swapon --show

# If port already in use
sudo netstat -tulpn | grep 8888
sudo lsof -i :8888

# Clean up Docker
docker system prune -a

# Restart everything
docker compose down
docker system prune -f
docker compose up -d
```

---

## Environment Variables (Optional)

If you need custom configuration, edit `docker-compose.yml`:

```yaml
backend:
  environment:
    - DATABASE_URL=postgresql://aliby:NEW_PASSWORD@postgres:5432/aliby_db
    - SECRET_KEY=your-random-secret-key-here
```

---

## SSL/HTTPS Setup (Optional, for production)

### Using Let's Encrypt (Free SSL)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is set up automatically
sudo certbot renew --dry-run
```

### Update Nginx config

Edit `nginx/nginx.conf` to support SSL on port 443.

---

## Performance Tips for 1GB RAM

1. **Swap is critical** - make sure 2GB swap is enabled
2. **Monitor memory**: `watch free -h`
3. **Limit PostgreSQL**: Edit `docker-compose.yml`:
   ```yaml
   postgres:
     command: postgres -c shared_buffers=128MB -c max_connections=50
   ```
4. **Restart weekly** to clear memory leaks:
   ```bash
   # Add to crontab
   0 4 * * 0 cd /opt/aliby && docker compose restart
   ```

---

## Backup Strategy

```bash
# Backup database
docker compose exec postgres pg_dump -U aliby aliby_db > backup.sql

# Restore database
docker compose exec -T postgres psql -U aliby aliby_db < backup.sql
```

---

## Support

If something doesn't work:
1. Check logs: `docker compose logs -f`
2. Check resources: `free -h` and `df -h`
3. Restart: `docker compose restart`
4. Clean rebuild: `docker compose down && docker compose up -d --build`
