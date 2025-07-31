# JSON Field Selector - EC2 Deployment Guide

This guide will help you deploy the JSON Field Selector application to your EC2 server.

## Prerequisites

- An EC2 instance running Ubuntu 20.04+ or Amazon Linux 2
- SSH access to your EC2 instance
- Security group allowing inbound traffic on port 80 (HTTP)

## Deployment Options

### Option 1: Direct File Transfer + Docker Build (Recommended)

#### Step 1: Prepare EC2 Server
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install docker.io curl -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes to take effect
exit
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### Step 2: Transfer Application Files
```bash
# From your local machine, transfer the application
scp -i your-key.pem -r /path/to/json-selector ubuntu@your-ec2-ip:~/

# Or use rsync for better transfer
rsync -avz -e "ssh -i your-key.pem" /path/to/json-selector/ ubuntu@your-ec2-ip:~/json-selector/
```

#### Step 3: Deploy Application
```bash
# On your EC2 server
cd json-selector

# Build and start the application
docker-compose -f docker-compose.prod.yml up -d

# Check if it's running
docker ps
```

#### Step 4: Verify Deployment
```bash
# Test locally on the server
curl http://localhost

# Your application should now be available at:
# http://your-ec2-public-ip
```

### Option 2: Using Docker Hub

#### Step 1: Push to Docker Hub (from local machine)
```bash
# Login to Docker Hub
docker login

# Edit deploy.sh and replace 'your-dockerhub-username' with your actual username
# Then run:
./deploy.sh
```

#### Step 2: Deploy on EC2
```bash
# SSH into EC2 and run:
docker run -d -p 80:5000 --name json-selector --restart unless-stopped your-dockerhub-username/json-selector:latest
```

### Option 3: Using Git Repository

#### Step 1: Push to Git Repository
```bash
# From your local machine
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/json-selector.git
git push -u origin main
```

#### Step 2: Clone and Deploy on EC2
```bash
# On your EC2 server
git clone https://github.com/yourusername/json-selector.git
cd json-selector
docker-compose -f docker-compose.prod.yml up -d
```

## Application Features

- **Stateless Design**: No data persists on the server
- **Auto-cleanup**: Uploaded files are automatically removed after processing
- **File System Access API**: Modern browsers can save directly to user's local folders
- **Fallback Download**: Older browsers use traditional download method
- **Large File Support**: Handles up to 1GB of JSON files
- **Hierarchical UI**: Tree view for nested JSON structures

## Security Considerations

1. **HTTPS**: Consider setting up SSL/TLS with Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. **Firewall**: Configure UFW if needed:
   ```bash
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

3. **Updates**: Keep your system and Docker updated:
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Monitoring and Maintenance

### Check Application Status
```bash
docker ps
docker logs json-selector_json-selector_1
```

### Update Application
```bash
# Pull latest changes (if using Git)
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backup (if needed)
Since the application is stateless, no regular backups are needed. The application code is your backup.

## Troubleshooting

### Application won't start
```bash
# Check logs
docker logs json-selector_json-selector_1

# Check if port 80 is available
sudo netstat -tlnp | grep :80
```

### Can't access from browser
1. Check EC2 security group allows port 80
2. Verify application is running: `docker ps`
3. Test locally: `curl http://localhost`

### Out of disk space
```bash
# Clean up Docker
docker system prune -a

# Check disk usage
df -h
```

## Performance Notes

- The application automatically cleans up uploaded files after processing
- Memory usage scales with JSON file size (up to 1GB supported)
- For high-traffic scenarios, consider using a reverse proxy like Nginx
- Multiple instances can be run behind a load balancer if needed

## Support

If you encounter issues, check:
1. Docker logs: `docker logs container-name`
2. System resources: `htop` or `free -h`
3. Network connectivity: `curl http://localhost`
