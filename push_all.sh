#!/bin/bash

USERNAME="swordenkisk"

create_gitignore() {
    cat > .gitignore << 'EOF'
venv/
.env
*.db
otc.py
credentials.json
__pycache__/
logs/
data/
*.pyc
*.log
secrets/
config/
EOF
    git add .gitignore 2>/dev/null || true
}

# TOP LEVEL DIRECTORIES ONLY - NO SUBDIRECTORIES
find . -maxdepth 1 -mindepth 1 -type d ! -name '.' ! -name '..' ! -path '*/.git*' | while IFS= read -r dir; do
    repo=$(basename "$dir")
    
    # Skip script itself and Git internals
    [[ "$repo" =~ ^(push_all|.*.sh)$ ]] && continue
    [[ "$repo" =~ ^(hooks|info|refs|objects|logs)$ ]] && continue
    
    echo "========================================"
    echo "Processing: $repo ($dir)"
    
    cd "$dir" 2>/dev/null || { echo "❌ Cannot enter $dir"; continue; }

    # Skip empty directories
    if [[ -z "$(ls -A)" && ! -d .git ]]; then
        echo "⏭️  $repo – Empty, skipping"
        cd ..
        continue
    fi

    # 1. Git repo setup
    if [[ ! -d .git ]]; then
        git init
        git config init.defaultBranch main >/dev/null 2>&1
        create_gitignore
        git add .
        if git diff --staged --quiet; then
            echo "⏭️  $repo – No files to commit"
        else
            git commit -m "Initial: $repo"
        fi
    else
        create_gitignore
        git add .
        if ! git diff --staged --quiet 2>/dev/null; then
            git commit -m "Update: $repo $(date +%Y-%m-%d)"
        fi
    fi

    # 2. Main branch
    git branch -M main 2>/dev/null || true

    # 3. Remote setup
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/$USERNAME/$repo.git"

    # 4. FORCE PUSH EVERYTHING
    if git push -u origin main --force 2>/dev/null; then
        echo "✅ $repo – FORCE PUSHED SUCCESS"
    else
        echo "⚠️  $repo – Manual intervention needed"
        echo "   https://github.com/$USERNAME/$repo"
    fi

    cd ..
done

echo "🎉 ALL TOP-LEVEL REPOS PROCESSED!"
