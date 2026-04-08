# Surface Hub Deployment Script (PowerShell)

Write-Host "🚀 Starting Surface Hub Deployment..." -ForegroundColor Cyan

# 1. Firebase Deployment
Write-Host "📦 Deploying to Firebase Hosting & Database..." -ForegroundColor Yellow
firebase deploy --only hosting,database,firestore

# 2. GitHub Deployment
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow
git add .
git commit -m "Final production push: Full bot functionality + Website reward bridge"
git push origin main

Write-Host "✅ Deployment Complete! Website is live." -ForegroundColor Green
Write-Host "⚠️  Note: For Hugging Face, ensure you have set the secrets in your Space." -ForegroundColor Gray
