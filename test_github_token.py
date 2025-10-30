#!/usr/bin/env python3
"""
Test script to check GitHub token detection in different environments.
"""
import os
from privileges.github.github import GitHubIntegration

def test_token_detection():
    """Test GitHub token detection."""
    print("=== GitHub Token Detection Test ===")
    
    # Test current environment
    github_token = os.getenv("GITHUB_TOKEN")
    github_actions = os.getenv("GITHUB_ACTIONS")
    
    print(f"GITHUB_ACTIONS env var: {github_actions}")
    print(f"GITHUB_TOKEN available: {'Yes' if github_token else 'No'}")
    
    if github_token:
        print(f"Token starts with: {github_token[:10]}...")
    
    # Initialize GitHub integration
    github_integration = GitHubIntegration()
    
    print(f"GitHub client initialized: {'Yes' if github_integration.github_client else 'No'}")
    print(f"Repository owner: {github_integration.repo_owner}")
    print(f"Repository name: {github_integration.repo_name}")
    print(f"PR number: {github_integration.pr_number}")
    
    # Test API access
    if github_integration.github_client:
        try:
            repo = github_integration.get_repository()
            if repo:
                print(f"Successfully connected to repo: {repo.full_name}")
                print(f"Repo description: {repo.description}")
            else:
                print("Could not get repository (might be normal in local development)")
        except Exception as e:
            print(f"Error accessing repository: {e}")
    else:
        print("No GitHub client available - will use git fallback")

if __name__ == "__main__":
    test_token_detection()