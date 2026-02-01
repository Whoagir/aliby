#!/bin/bash

# Setup Docker without sudo
sudo usermod -aG docker $USER

# Add aliases for convenience
cat >> ~/.bashrc << 'EOF'

# Docker aliases for Aliby project
alias dc='sudo docker compose'
alias dcu='sudo docker compose up -d'
alias dcd='sudo docker compose down'
alias dcl='sudo docker compose logs -f'
alias dcp='sudo docker compose ps'
alias dcr='sudo docker compose restart'

# Aliby project shortcut
alias aliby='cd ~/projects/aliby'
EOF

echo "Aliases added! Use: dc, dcu, dcd, dcl, dcp, dcr, aliby"
echo "Run: source ~/.bashrc"
