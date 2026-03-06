#!/bin/bash
# 立即推送到 GitHub
# Run this to push to GitHub now!

set -e

echo "========================================================================"
echo "📤 Pushing to GitHub: weisenchen/chanlunInvester"
echo "========================================================================"
echo ""

cd "$(dirname "$0")"

# Show current status
echo "Current branch: $(git branch --show-current)"
echo "Remote: $(git remote get-url origin)"
echo ""

# Show last commit
echo "Latest commit:"
git log -1 --oneline
echo ""

# Push
echo "Pushing to GitHub..."
echo ""
echo "⚠️  If prompted for password, use your GitHub Personal Access Token"
echo "   Get token from: https://github.com/settings/tokens"
echo ""

git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ SUCCESS! Code pushed to GitHub!"
    echo "========================================================================"
    echo ""
    echo "📊 Repository: https://github.com/weisenchen/chanlunInvester"
    echo "📝 Check your commits at:"
    echo "   https://github.com/weisenchen/chanlunInvester/commits/main"
    echo ""
    echo "🎉 System Status: v1.1 Production Ready (91%)"
    echo ""
else
    echo ""
    echo "========================================================================"
    echo "❌ Push failed!"
    echo "========================================================================"
    echo ""
    echo "Please try:"
    echo "  1. Set GH_TOKEN environment variable:"
    echo "     export GH_TOKEN=your_github_token"
    echo ""
    echo "  2. Or use git with token:"
    echo "     git push https://YOUR_TOKEN@github.com/weisenchen/chanlunInvester.git main"
    echo ""
    echo "  3. Or configure SSH key and use:"
    echo "     git remote set-url origin git@github.com:weisenchen/chanlunInvester.git"
    echo "     git push origin main"
    echo ""
    exit 1
fi
