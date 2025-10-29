"""
Tests for GitHub integration module.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from privileges.github.github import GitHubIntegration, get_pr_service_requests


class TestGitHubIntegration:
    """Test cases for GitHub integration functionality."""

    def test_init(self):
        """Test GitHubIntegration initialization."""
        github_integration = GitHubIntegration()
        assert github_integration.repo_root == Path.cwd()
        assert github_integration.service_request_parser is not None

    def test_init_with_repo_root(self):
        """Test GitHubIntegration initialization with custom repo root."""
        repo_root = "/tmp/test"
        github_integration = GitHubIntegration(repo_root)
        assert github_integration.repo_root == Path(repo_root)

    def test_filter_service_request_files(self):
        """Test filtering service request files."""
        github_integration = GitHubIntegration()
        
        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            service_requests_dir = temp_path / "service_requests" / "priviliges"
            service_requests_dir.mkdir(parents=True)
            
            test_yml = service_requests_dir / "test.yml"
            test_yml.write_text("test: content")
            
            other_file = temp_path / "other.txt"
            other_file.write_text("other content")
            
            # Test with current working directory set to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                github_integration.repo_root = Path(temp_dir)
                
                file_paths = [
                    "service_requests/priviliges/test.yml",
                    "other.txt",
                    "service_requests/abac/policy.yaml",  # This won't exist
                    "not_service_request.yml"
                ]
                
                filtered = github_integration.filter_service_request_files(file_paths)
                
                # Only the existing service request file should be included
                assert len(filtered) == 1
                assert "service_requests/priviliges/test.yml" in filtered
                
            finally:
                os.chdir(original_cwd)

    @patch('subprocess.run')
    def test_get_changed_files_success(self, mock_run):
        """Test successful retrieval of changed files."""
        mock_run.return_value = Mock(
            stdout="service_requests/priviliges/test.yml\nother.txt\n",
            stderr="",
            returncode=0
        )
        
        github_integration = GitHubIntegration()
        changed_files = github_integration.get_changed_files("main")
        
        assert len(changed_files) == 2
        assert "service_requests/priviliges/test.yml" in changed_files
        assert "other.txt" in changed_files
        
        mock_run.assert_called_once_with(
            ["git", "diff", "--name-only", "main...HEAD"],
            cwd=github_integration.repo_root,
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_get_changed_files_error(self, mock_run):
        """Test error handling when git command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git", "diff"], stderr="fatal: not a git repository"
        )
        
        github_integration = GitHubIntegration()
        
        with pytest.raises(subprocess.CalledProcessError):
            github_integration.get_changed_files("main")

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_BASE_REF": "develop"})
    @patch('subprocess.run')
    def test_get_changed_files_from_env_github_actions(self, mock_run):
        """Test getting changed files in GitHub Actions environment."""
        mock_run.return_value = Mock(
            stdout="service_requests/priviliges/test.yml\n",
            stderr="",
            returncode=0
        )
        
        github_integration = GitHubIntegration()
        changed_files = github_integration.get_changed_files_from_env()
        
        assert len(changed_files) == 1
        assert "service_requests/priviliges/test.yml" in changed_files
        
        # Should use the base ref from environment
        mock_run.assert_called_once_with(
            ["git", "diff", "--name-only", "develop...HEAD"],
            cwd=github_integration.repo_root,
            capture_output=True,
            text=True,
            check=True
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_get_changed_files_from_env_not_github_actions(self):
        """Test getting changed files when not in GitHub Actions."""
        github_integration = GitHubIntegration()
        changed_files = github_integration.get_changed_files_from_env()
        
        assert changed_files == []

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "pull_request"})
    def test_is_in_pull_request_github_actions(self):
        """Test PR detection in GitHub Actions."""
        github_integration = GitHubIntegration()
        assert github_integration.is_in_pull_request() is True

    @patch.dict(os.environ, {}, clear=True)
    @patch('subprocess.run')
    def test_is_in_pull_request_git_branch(self, mock_run):
        """Test PR detection based on git branch."""
        mock_run.return_value = Mock(
            stdout="feature-branch\n",
            stderr="",
            returncode=0
        )
        
        github_integration = GitHubIntegration()
        assert github_integration.is_in_pull_request() is True

    @patch.dict(os.environ, {}, clear=True)
    @patch('subprocess.run')
    def test_is_not_in_pull_request_main_branch(self, mock_run):
        """Test PR detection when on main branch."""
        mock_run.return_value = Mock(
            stdout="main\n",
            stderr="",
            returncode=0
        )
        
        github_integration = GitHubIntegration()
        assert github_integration.is_in_pull_request() is False

    def test_get_pr_service_requests_convenience_function(self):
        """Test the convenience function for getting PR service requests."""
        with patch.object(GitHubIntegration, 'get_pr_service_requests') as mock_method:
            mock_method.return_value = []
            
            result = get_pr_service_requests("/tmp/repo", "develop")
            
            mock_method.assert_called_once_with("develop")
            assert result == []