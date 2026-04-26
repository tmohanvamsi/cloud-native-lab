# LFCS — Linux Foundation Certified System Administrator

## Start VM
```bash
make vagrant-up
make vagrant-ssh
```

## Lab 1 — Users and Groups
```bash
sudo useradd -m -s /bin/bash alice
sudo passwd alice
sudo groupadd developers
sudo usermod -aG developers alice
id alice                            # verify groups
groups alice
```

## Lab 2 — File Permissions
```bash
ls -la /etc/passwd                  # see owner, group, permissions
chmod 750 /home/alice               # rwxr-x---
chown alice:developers /home/alice
# Octal: 4=read 2=write 1=exec
# 750 = rwx(owner) r-x(group) ---(others)
```

## Lab 3 — systemd Services
```bash
systemctl list-units --type=service --state=running
systemctl status ssh
sudo systemctl stop ssh
sudo systemctl start ssh
sudo systemctl enable ssh           # persist across reboots
journalctl -u ssh -n 50            # last 50 log lines
```

## Lab 4 — Processes and Jobs
```bash
ps aux | grep nginx
top -b -n1 | head -20
kill -9 <PID>
nice -n 10 sleep 100 &             # low priority background job
jobs                               # list background jobs
fg %1                              # bring job 1 to foreground
```

## Lab 5 — Networking
```bash
ip addr show
ip route show
ss -tlnp                           # listening TCP ports
ping -c4 8.8.8.8
dig google.com
curl -I http://example.com
```

## Lab 6 — Disk and LVM
```bash
lsblk                              # list block devices
df -h                              # disk usage
du -sh /var/log/*
# LVM basics (needs extra disk)
sudo pvcreate /dev/sdb
sudo vgcreate myvg /dev/sdb
sudo lvcreate -L 1G -n mylv myvg
sudo mkfs.ext4 /dev/myvg/mylv
sudo mount /dev/myvg/mylv /mnt
```

## Lab 7 — Cron Jobs
```bash
crontab -e
# Format: min hour day month weekday command
# 0 2 * * * /usr/bin/find /tmp -mtime +7 -delete   (2am daily cleanup)
crontab -l
systemctl status cron
```

## Lab 8 — Firewall
```bash
sudo ufw status
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw enable
sudo ufw deny 8080
sudo ufw status numbered
```

## Lab 9 — Package Management
```bash
apt-get update
apt-get install -y nginx
apt-get remove nginx
dpkg -l | grep nginx
apt-cache search python3
```

## Lab 10 — Archive and Transfer
```bash
tar -czf backup.tar.gz /etc/nginx
tar -tzf backup.tar.gz             # list contents
tar -xzf backup.tar.gz -C /tmp
scp backup.tar.gz ubuntu@192.168.56.11:/tmp/
rsync -avz /var/log/ ubuntu@192.168.56.11:/backup/logs/
```

## Exam Tips
- `man <command>` is allowed in the exam — use it
- Practice `systemctl`, `journalctl`, `ss`, `ip`, `lsblk` until automatic
- Know chmod octal notation cold: 755, 644, 600, 750
- Know the difference between `useradd` and `adduser`
