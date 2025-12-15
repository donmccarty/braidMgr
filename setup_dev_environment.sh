#!/bin/bash
# =============================================================================
# Development Environment Setup - BRAID Manager
# =============================================================================
#
# This script sets up project-isolated credentials:
# - Git credentials (local config, SSH authentication)
# - Python virtual environment
#
# Run: chmod +x setup_dev_environment.sh
# Run: ./setup_dev_environment.sh
#
# =============================================================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PROJECT_NAME="BRAID Manager"
PROJECT_DESC="Desktop application for managing BRAID logs (Budget, Risks, Action Items, Issues, Decisions)"

echo "================================================"
echo "$PROJECT_NAME"
echo "Development Environment Setup"
echo "================================================"
echo ""
echo "$PROJECT_DESC"
echo ""

# =============================================================================
# 1. Git Credentials Setup
# =============================================================================
echo "1. Git Credentials Setup"
echo "------------------------"

if git config --local user.name >/dev/null 2>&1; then
    echo "✓ Git already configured for this project"
    echo "  User: $(git config --local user.name)"
    echo "  Email: $(git config --local user.email)"
else
    echo "Setting up project-specific git credentials..."
    read -p "GitHub username for this project: " GIT_USER
    read -p "GitHub email for this project: " GIT_EMAIL

    git config --local user.name "$GIT_USER"
    git config --local user.email "$GIT_EMAIL"

    echo "✓ Git user configured locally (this repo only)"
fi

# SSH Key Setup
echo ""
read -p "Configure SSH authentication for git? (y/n): " SETUP_SSH

if [[ "$SETUP_SSH" == "y" ]]; then
    echo ""
    SSH_KEY_PATH="$HOME/.ssh/id_ed25519_braidmgr"
    SSH_KEY_EMAIL="don.mccarty@gmail.com"

    if [[ -f "$SSH_KEY_PATH" ]]; then
        echo "✓ SSH key already exists at $SSH_KEY_PATH"
    else
        echo "Generating SSH key..."
        echo "Command: ssh-keygen -t ed25519 -C \"$SSH_KEY_EMAIL\" -f \"$SSH_KEY_PATH\" -N \"\""
        ssh-keygen -t ed25519 -C "$SSH_KEY_EMAIL" -f "$SSH_KEY_PATH" -N ""
        echo "✓ SSH key generated"
    fi

    echo ""
    echo "Next steps for SSH setup:"
    echo "1. Copy your public key:"
    echo "   cat ${SSH_KEY_PATH}.pub"
    echo ""
    echo "2. Add to GitHub:"
    echo "   https://github.com/settings/keys"
    echo ""
    echo "3. After adding to GitHub, press Enter to continue..."
    read

    # Add key to SSH agent
    echo "Adding key to SSH agent..."
    eval "$(ssh-agent -s)" >/dev/null 2>&1 || true
    ssh-add "$SSH_KEY_PATH" 2>/dev/null || true

    # Update SSH config for braidmgr-specific host
    SSH_CONFIG="$HOME/.ssh/config"
    if ! grep -q "Host github-braidmgr" "$SSH_CONFIG" 2>/dev/null; then
        echo "" >> "$SSH_CONFIG"
        echo "# BRAID Manager GitHub SSH Configuration" >> "$SSH_CONFIG"
        echo "Host github-braidmgr" >> "$SSH_CONFIG"
        echo "    HostName github.com" >> "$SSH_CONFIG"
        echo "    User git" >> "$SSH_CONFIG"
        echo "    IdentityFile $SSH_KEY_PATH" >> "$SSH_CONFIG"
        echo "    AddKeysToAgent yes" >> "$SSH_CONFIG"
        echo "✓ Updated ~/.ssh/config with github-braidmgr host"
    fi

    # Test connection
    echo ""
    echo "Testing GitHub connection..."
    if ssh -T git@github-braidmgr 2>&1 | grep -q "successfully authenticated"; then
        echo "✓ GitHub SSH connection successful"
    else
        echo "⚠ GitHub connection test inconclusive - verify manually with:"
        echo "  ssh -T git@github-braidmgr"
    fi

    # Update git remote to SSH with custom host
    CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
    GITHUB_ORG="donmccarty"
    REPO_NAME="braidMgr"

    echo ""
    echo "Updating remote to use SSH with project-specific key..."
    echo "GitHub user: $GITHUB_ORG"
    echo "Repository: $REPO_NAME"
    read -p "Is this correct? (y/n): " CONFIRM_REMOTE

    if [[ "$CONFIRM_REMOTE" == "y" ]]; then
        # Use the custom host alias so it picks up the right SSH key
        git remote set-url origin "git@github-braidmgr:${GITHUB_ORG}/${REPO_NAME}.git"
        echo "✓ Remote updated to SSH (git@github-braidmgr:${GITHUB_ORG}/${REPO_NAME}.git)"
    fi
fi

# =============================================================================
# 2. Python Virtual Environment
# =============================================================================
echo ""
echo "2. Python Virtual Environment"
echo "-----------------------------"

if [[ -d ".venv" ]]; then
    echo "✓ Virtual environment exists"
else
    read -p "Create Python virtual environment? (y/n): " CREATE_VENV
    if [[ "$CREATE_VENV" == "y" ]]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
        echo "✓ Virtual environment created"
    fi
fi

if [[ -d ".venv" ]]; then
    echo ""
    echo "To activate: source .venv/bin/activate"

    # Install dependencies if requirements.txt exists
    if [[ -f "requirements.txt" ]]; then
        read -p "Install dependencies from requirements.txt? (y/n): " INSTALL_DEPS
        if [[ "$INSTALL_DEPS" == "y" ]]; then
            source .venv/bin/activate
            pip install -r requirements.txt
            echo "✓ Dependencies installed"
        fi
    fi
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "==========================================="
echo "Setup Complete!"
echo "==========================================="
echo ""
echo "Next steps:"
echo "1. Activate environment: source .venv/bin/activate"
echo "2. Install dependencies (if not done): pip install -r requirements.txt"
echo "3. Run the app: python -m src.ui_qt.app"
echo "4. Test git push: git push"
echo ""
echo "Current git configuration:"
git config --local --list | grep -E "^user\.|^remote\.|^core\.ssh" || true
echo ""
