#!/bin/bash
# Surface Hub Deployment Script

echo "🚀 Starting Surface Hub Deployment..."

# 1. Firebase Deployment
echo "📦 Deploying to Firebase Hosting & Database..."
firebase deploy --only hosting,database,firestore

# 2. GitHub Deployment
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Final production push: Full bot functionality + Website reward bridge"
git push origin main

echo "✅ Deployment Complete! Website is live."
echo "⚠️  Note: For Hugging Face, ensure you have set the secrets in your Space."
