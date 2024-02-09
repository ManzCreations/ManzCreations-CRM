#!/bin/bash

# Replace the following variables with your information
GITHUB_USERNAME="ManzCreations"
REPOSITORY_NAME="ManzCreations-CRM"
COMMIT_MESSAGE="Initial commit"
REMOTE_URL="https://github.com/$GITHUB_USERNAME/$REPOSITORY_NAME.git"

# Initialize a new Git repository
git init

# Add all files in the project directory to the staging area
git add .

# Commit the files
git commit -m "$COMMIT_MESSAGE"

# Add the remote GitHub repository
git remote add origin $REMOTE_URL

# Rename the local branch to 'main'
git branch -m master main

# Push the commit to the GitHub repository on the 'main' branch
git push -u origin main

echo "Repository setup completed."