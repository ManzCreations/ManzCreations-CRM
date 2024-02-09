#!/bin/bash

# Replace the following variables with your information
GITHUB_USERNAME="ManzCreations"
REPOSITORY_NAME="ManzCreations-CRM"
COMMIT_MESSAGE="Initial commit"
REMOTE_URL="https://github.com/$GITHUB_USERNAME/$REPOSITORY_NAME.git"

# Initialize a new Git repository (if one doesn't already exist)
git init

# Add all files in the project directory to the staging area
git add .

# Commit the files
git commit -m "$COMMIT_MESSAGE"

# Check if the remote origin already exists
if git remote get-url origin; then
  echo "Remote origin already exists."
else
  # Add the remote GitHub repository
  git remote add origin $REMOTE_URL
fi

# Rename the local branch to 'main' if it's not already named 'main'
if [ "$(git symbolic-ref --short HEAD)" != "main" ]; then
  git branch -m master main
fi

# Pull changes from the remote 'main' branch, if any, to integrate them
# Use this with caution; it might be better to manually merge or rebase based on your project's state
git pull origin main --allow-unrelated-histories

# Push the commit to the GitHub repository on the 'main' branch
git push -u origin main

echo "Repository setup completed."