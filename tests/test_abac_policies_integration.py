"""
Integration tests for ABAC Policies Interface

These tests verify the integration between different components
and test realistic usage scenarios.
"""

from unittest.mock import Mock, patch

import pytest

from priviliges.abac.abac import (
    ABACPoliciesInterface,
    abac_policies,
    create_abac_policy,
    delete_abac_policy,
    get_abac_policy,
    update_abac_policy,
)


class TestABACPoliciesIntegration:
    """Integration tests for ABAC policies functionality."""

    def test_complete_policy_lifecycle(self):
        """Test complete policy lifecycle: create, read, update, delete."""
        with patch("abac.abac.abac.WorkspaceClient") as mock_ws:
            # Setup mock workspace client
            mock_client = Mock()
            mock_ws.return_value = mock_client

            # Mock policy responses
            created_policy = Mock()
            created_policy.name = "test_policy"
            created_policy.id = "policy-123"
            created_policy.to_principals = ["user@example.com"]

            updated_policy = Mock()
            updated_policy.name = "test_policy"
            updated_policy.id = "policy-123"
            updated_policy.to_principals = ["user@example.com", "admin@example.com"]

            mock_client.policies.create_policy.return_value = created_policy
            mock_client.policies.get_policy.return_value = created_policy
            mock_client.policies.update_policy.return_value = updated_policy
            mock_client.policies.delete_policy.return_value = Mock()

            # Create a new interface instance
            interface = ABACPoliciesInterface(mock_client)

            # 1. Create policy
            policy = interface.create_policy(
                name="test_policy",
                securable_type="table",
                securable_fullname="catalog.schema.table",
                policy_type="POLICY_TYPE_COLUMN_MASK",
                principals=["user@example.com"],
                column_mask_function="mask_func",
                column_mask_on_column="sensitive_col",
            )

            assert policy.name == "test_policy"
            mock_client.policies.create_policy.assert_called_once()

            # 2. Get policy
            retrieved_policy = interface.get_policy(
                securable_type="table", securable_fullname="catalog.schema.table", policy_name="test_policy"
            )

            assert retrieved_policy.name == "test_policy"
            mock_client.policies.get_policy.assert_called_once()

            # 3. Update policy
            updated = interface.update_policy(
                securable_type="table",
                securable_fullname="catalog.schema.table",
                policy_name="test_policy",
                principals=["user@example.com", "admin@example.com"],
            )

            assert len(updated.to_principals) == 2
            mock_client.policies.update_policy.assert_called_once()

            # 4. Delete policy
            interface.delete_policy(
                securable_type="table", securable_fullname="catalog.schema.table", policy_name="test_policy"
            )

            mock_client.policies.delete_policy.assert_called_once()

    @patch("abac.abac.abac.abac_policies")
    def test_convenience_functions_integration(self, mock_global_interface):
        """Test that convenience functions properly use the global interface."""
        # Mock the global interface responses
        created_policy = Mock()
        created_policy.name = "convenience_policy"

        mock_global_interface.create_policy.return_value = created_policy
        mock_global_interface.get_policy.return_value = created_policy
        mock_global_interface.update_policy.return_value = created_policy
        mock_global_interface.delete_policy.return_value = Mock()

        # Test create
        policy = create_abac_policy(
            name="convenience_policy",
            securable_type="table",
            securable_fullname="catalog.schema.table",
            policy_type="POLICY_TYPE_ROW_FILTER",
            principals=["user@example.com"],
            row_filter_function="filter_func",
        )

        assert policy.name == "convenience_policy"
        mock_global_interface.create_policy.assert_called_once()

        # Test get
        retrieved = get_abac_policy(
            securable_type="table", securable_fullname="catalog.schema.table", policy_name="convenience_policy"
        )

        assert retrieved.name == "convenience_policy"
        mock_global_interface.get_policy.assert_called_once()

        # Test update
        updated = update_abac_policy(
            securable_type="table",
            securable_fullname="catalog.schema.table",
            policy_name="convenience_policy",
            comment="Updated comment",
        )

        assert updated.name == "convenience_policy"
        mock_global_interface.update_policy.assert_called_once()

        # Test delete
        delete_abac_policy(
            securable_type="table", securable_fullname="catalog.schema.table", policy_name="convenience_policy"
        )

        mock_global_interface.delete_policy.assert_called_once()

    def test_policy_validation_scenarios(self):
        """Test various policy validation scenarios."""
        with patch("abac.abac.abac.WorkspaceClient") as mock_ws:
            mock_client = Mock()
            mock_ws.return_value = mock_client
            interface = ABACPoliciesInterface(mock_client)

            # Test column mask policy validation
            with pytest.raises(ValueError, match="Column mask policies require"):
                interface.create_policy(
                    name="invalid_mask",
                    securable_type="table",
                    securable_fullname="catalog.schema.table",
                    policy_type="POLICY_TYPE_COLUMN_MASK",
                    principals=["user@example.com"],
                    # Missing column_mask_function
                )

            # Test row filter policy validation
            with pytest.raises(ValueError, match="Row filter policies require"):
                interface.create_policy(
                    name="invalid_filter",
                    securable_type="table",
                    securable_fullname="catalog.schema.table",
                    policy_type="POLICY_TYPE_ROW_FILTER",
                    principals=["user@example.com"],
                    # Missing row_filter_function
                )

            # Test invalid policy type
            with pytest.raises(ValueError, match="Invalid policy_type"):
                interface.create_policy(
                    name="invalid_type",
                    securable_type="table",
                    securable_fullname="catalog.schema.table",
                    policy_type="INVALID_TYPE",
                    principals=["user@example.com"],
                )

    def test_complex_policy_configurations(self):
        """Test creating policies with complex configurations."""
        with patch("abac.abac.abac.WorkspaceClient") as mock_ws:
            mock_client = Mock()
            mock_ws.return_value = mock_client
            mock_client.policies.create_policy.return_value = Mock()

            interface = ABACPoliciesInterface(mock_client)

            # Test column mask policy with all options
            interface.create_policy(
                name="complex_mask",
                securable_type="table",
                securable_fullname="catalog.schema.table",
                policy_type="POLICY_TYPE_COLUMN_MASK",
                principals=["group:analysts", "user@example.com"],
                column_mask_function="advanced_mask",
                column_mask_on_column="sensitive_data",
                column_mask_using_args=[
                    {"alias": "mask_type", "constant": "partial"},
                    {"alias": "visible_chars", "constant": "4"},
                ],
                when_condition="user_role != 'admin'",
                match_columns=[{"alias": "dept", "condition": "department = 'finance'"}],
                except_principals=["group:executives"],
                comment="Complex masking policy for sensitive financial data",
            )

            mock_client.policies.create_policy.assert_called_once()
            call_args = mock_client.policies.create_policy.call_args[0][0]

            # Verify complex configuration
            assert call_args.name == "complex_mask"
            assert len(call_args.to_principals) == 2
            assert call_args.when_condition == "user_role != 'admin'"
            assert call_args.except_principals == ["group:executives"]
            assert call_args.comment == "Complex masking policy for sensitive financial data"
            assert call_args.column_mask is not None
            assert len(call_args.column_mask.using) == 2
            assert call_args.match_columns is not None
            assert len(call_args.match_columns) == 1

    def test_global_interface_initialization(self):
        """Test that the global interface is properly initialized."""
        # The global abac_policies should be an instance of ABACPoliciesInterface
        assert isinstance(abac_policies, ABACPoliciesInterface)
        assert hasattr(abac_policies, "client")
        assert hasattr(abac_policies, "create_policy")
        assert hasattr(abac_policies, "update_policy")
        assert hasattr(abac_policies, "delete_policy")
        assert hasattr(abac_policies, "get_policy")
        assert hasattr(abac_policies, "list_policies")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
