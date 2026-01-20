#!/usr/bin/env python3
"""
Fund Comparison CLI

Demonstrates how to compare investment funds using the FundAnalyzer.
"""

from fund_analyzer import FundAnalyzer
import json


def display_fund_comparison(analyzer, cnpj_list):
    """Display fund comparison"""
    comparison = analyzer.compare_funds(cnpj_list)

    if "error" in comparison:
        print(f"Error: {comparison['error']}")
        return

    print("\n" + "=" * 80)
    print("FUND COMPARISON REPORT")
    print("=" * 80)
    print(f"Comparison Date: {comparison['comparison_date']}")
    print(f"Number of funds: {len(comparison['funds'])}")
    print("=" * 80)

    funds = comparison['funds']

    # Display each category
    for category, fields in comparison['fields'].items():
        print(f"\n{category}:")
        print("-" * 80)

        for field in fields:
            print(f"\n  {field.upper().replace('_', ' ')}:")
            for i, fund in enumerate(funds, 1):
                value = fund.get(field, 'N/A')
                if value is None:
                    value = 'N/A'
                print(f"    Fund {i}: {value}")


def search_and_compare(analyzer):
    """Interactive fund search and comparison"""

    # Search for funds with specific criteria
    print("\n" + "=" * 80)
    print("SEARCHING FOR FUNDS WITH SPECIFIC CRITERIA")
    print("=" * 80)

    # Example 1: Find funds by ANBIMA classification
    print("\nExample 1: Renda Fixa funds")
    results = analyzer.database.search_funds({
        'status': 'EM FUNCIONAMENTO NORMAL',
        'anbima_class': 'Renda Fixa'
    })
    print(f"Found {len(results)} Renda Fixa funds")

    if len(results) >= 2:
        print("\nComparing first 2 Renda Fixa funds...")
        cnpj_list = [results[0]['cnpj'], results[1]['cnpj']]
        display_fund_comparison(analyzer, cnpj_list)

    # Example 2: Find funds by manager
    print("\n\n" + "=" * 80)
    print("Example 2: Finding funds by manager")
    print("=" * 80)

    # Get top manager
    stats = analyzer.get_statistics()
    if stats['top_managers']:
        top_manager = stats['top_managers'][0]
        manager_name = top_manager['manager']
        print(f"\nSearching for funds managed by: {manager_name}")

        results = analyzer.database.search_funds({
            'status': 'EM FUNCIONAMENTO NORMAL',
            'manager': manager_name
        })
        print(f"Found {len(results)} funds")

        if len(results) >= 2:
            print(f"\nComparing 2 funds from {manager_name}...")
            cnpj_list = [results[0]['cnpj'], results[1]['cnpj']]
            display_fund_comparison(analyzer, cnpj_list)

    # Example 3: Export comparison to CSV
    print("\n\n" + "=" * 80)
    print("Example 3: Exporting comparison to CSV")
    print("=" * 80)

    results = analyzer.database.search_funds({
        'status': 'EM FUNCIONAMENTO NORMAL'
    })

    if len(results) >= 3:
        cnpj_list = [results[0]['cnpj'], results[1]['cnpj'], results[2]['cnpj']]
        output_file = "fund_comparison.csv"

        print(f"\nExporting comparison of 3 funds to {output_file}...")
        analyzer.export_comparison_csv(cnpj_list, output_file)

        # Display which funds were compared
        print("\nFunds compared:")
        for i, cnpj in enumerate(cnpj_list, 1):
            fund = analyzer.database.search_funds({'cnpj': cnpj})[0]
            print(f"  {i}. {fund['name']} ({cnpj})")


def show_fund_changes(analyzer):
    """Show recent fund changes"""
    print("\n" + "=" * 80)
    print("RECENT FUND CHANGES")
    print("=" * 80)

    changes = analyzer.database.get_fund_changes(limit=20)

    if not changes:
        print("No changes tracked yet.")
        print("Changes will appear after the database is updated with new data.")
        return

    print(f"\nFound {len(changes)} recent changes:\n")

    for change in changes:
        print(f"CNPJ: {change['cnpj']}")
        print(f"  Change Type: {change['change_type']}")
        print(f"  Field: {change['field_name']}")
        print(f"  Old Value: {change['old_value']}")
        print(f"  New Value: {change['new_value']}")
        print(f"  Changed At: {change['changed_at']}")
        print()


def main():
    """Main demonstration"""
    print("=" * 80)
    print("FUND COMPARISON SYSTEM - DEMONSTRATION")
    print("=" * 80)

    # Check if database exists
    import os
    if not os.path.exists('./funds.db'):
        print("\nDatabase not found. Running initial data load...")
        print("This may take a few minutes...\n")
        analyzer = FundAnalyzer()
        analyzer.load_fund_data()
    else:
        print("\nUsing existing database...")
        analyzer = FundAnalyzer()

    # Show statistics
    print("\n" + "=" * 80)
    print("FUND DATABASE STATISTICS")
    print("=" * 80)
    stats = analyzer.get_statistics()

    print(f"Total funds: {stats['total_funds']}")
    print(f"Active funds: {stats['active_funds']}")

    print(f"\nBy status:")
    for status, count in list(stats['by_status'].items())[:3]:
        print(f"  {status}: {count}")

    if stats['by_type']:
        print(f"\nActive funds by type:")
        for fund_type, count in list(stats['by_type'].items())[:5]:
            print(f"  {fund_type}: {count}")

    if stats['top_managers']:
        print(f"\nTop 5 managers by fund count:")
        for manager in stats['top_managers'][:5]:
            print(f"  {manager['manager']}: {manager['fund_count']} funds")

    # Demonstrate comparisons
    search_and_compare(analyzer)

    # Show changes
    show_fund_changes(analyzer)

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nYou can now use the FundAnalyzer class to:")
    print("  - Search for funds with custom filters")
    print("  - Compare funds side-by-side")
    print("  - Track changes over time")
    print("  - Export comparisons to CSV")
    print("\nSee fund_analyzer.py for the full API documentation.")


if __name__ == "__main__":
    main()
