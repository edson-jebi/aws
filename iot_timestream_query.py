#!/usr/bin/env python3
"""
AWS IoT Rules → Timestream Query Tool

Lists IoT topic rules, identifies Timestream actions,
and queries the discovered Timestream database/table.
"""

import sys
import argparse
from datetime import datetime

import boto3
import botocore.exceptions
from tabulate import tabulate
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query AWS Timestream tables discovered from IoT Rule actions"
    )
    parser.add_argument(
        "--profile", required=True, help="AWS SSO profile name"
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--query",
        default=None,
        help='Custom Timestream SQL query (overrides auto-generated). '
             'Example: SELECT * FROM "mydb"."mytable" WHERE time > ago(1h)',
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate a time-series plot of the data (requires matplotlib and pandas)"
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# IoT Rule helpers
# ---------------------------------------------------------------------------

def list_all_rules(iot_client):
    """Fetch all IoT topic rules, handling pagination."""
    all_rules = []
    params = {"maxResults": 100}
    while True:
        response = iot_client.list_topic_rules(**params)
        all_rules.extend(response.get("rules", []))
        next_token = response.get("nextToken")
        if not next_token:
            break
        params["nextToken"] = next_token
    return all_rules


def display_rules(rules):
    """Print rules in a numbered table."""
    table_data = []
    for i, rule in enumerate(rules, start=1):
        status = "Disabled" if rule.get("ruleDisabled", False) else "Enabled"
        table_data.append([
            i,
            rule["ruleName"],
            rule.get("topicPattern", "N/A"),
            status,
        ])
    print("\n" + tabulate(
        table_data,
        headers=["#", "Rule Name", "Topic Pattern", "Status"],
        tablefmt="grid",
    ))


def select_rule(rules):
    """Prompt user to pick a rule by number."""
    while True:
        try:
            choice = int(input(f"\nSelect a rule (1-{len(rules)}): "))
            if 1 <= choice <= len(rules):
                return rules[choice - 1]
            print(f"Please enter a number between 1 and {len(rules)}")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)


# ---------------------------------------------------------------------------
# Timestream action extraction
# ---------------------------------------------------------------------------

def find_timestream_actions(rule_detail):
    """Extract all Timestream actions from a rule (including errorAction)."""
    timestream_actions = []
    actions = rule_detail.get("rule", {}).get("actions", [])

    for action in actions:
        ts = action.get("timestream")
        if ts:
            timestream_actions.append({
                "databaseName": ts["databaseName"],
                "tableName": ts["tableName"],
                "dimensions": ts.get("dimensions", []),
                "timestamp": ts.get("timestamp"),
            })

    # Also check the error action
    error_action = rule_detail.get("rule", {}).get("errorAction", {})
    if error_action:
        ts = error_action.get("timestream")
        if ts:
            timestream_actions.append({
                "databaseName": ts["databaseName"],
                "tableName": ts["tableName"],
                "dimensions": ts.get("dimensions", []),
                "timestamp": ts.get("timestamp"),
                "isErrorAction": True,
            })

    return timestream_actions


def display_timestream_info(ts_action):
    """Print the Timestream target details."""
    print("\n--- Timestream Target ---")
    print(f"  Database: {ts_action['databaseName']}")
    print(f"  Table:    {ts_action['tableName']}")
    if ts_action.get("dimensions"):
        print("  Dimensions:")
        for dim in ts_action["dimensions"]:
            print(f"    - {dim['name']}: {dim['value']}")
    if ts_action.get("timestamp"):
        ts = ts_action["timestamp"]
        print(f"  Timestamp: value={ts.get('value', 'N/A')}, unit={ts.get('unit', 'N/A')}")
    print()


def select_timestream_action(ts_actions):
    """If multiple Timestream actions, let user pick one."""
    if len(ts_actions) == 1:
        return ts_actions[0]

    print(f"\nFound {len(ts_actions)} Timestream actions:")
    for i, ts in enumerate(ts_actions, 1):
        label = " (error action)" if ts.get("isErrorAction") else ""
        print(f"  {i}. {ts['databaseName']}.{ts['tableName']}{label}")

    while True:
        try:
            choice = int(input(f"Select (1-{len(ts_actions)}): "))
            if 1 <= choice <= len(ts_actions):
                return ts_actions[choice - 1]
            print(f"Please enter a number between 1 and {len(ts_actions)}")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)


# ---------------------------------------------------------------------------
# Timestream query
# ---------------------------------------------------------------------------

def build_query(database_name, table_name, custom_query=None):
    """Build the Timestream SQL query string."""
    if custom_query:
        return custom_query
    return f'SELECT * FROM "{database_name}"."{table_name}" ORDER BY time DESC LIMIT 20'


def execute_timestream_query(session, region, query_string):
    """Execute a Timestream query and return (column_info, rows)."""
    ts_client = session.client("timestream-query", region_name=region)

    all_rows = []
    column_info = []
    params = {"QueryString": query_string}

    while True:
        response = ts_client.query(**params)
        column_info = response.get("ColumnInfo", column_info)
        all_rows.extend(response.get("Rows", []))
        next_token = response.get("NextToken")
        if not next_token:
            break
        params["NextToken"] = next_token

    return column_info, all_rows


def parse_timestream_response(column_info, rows):
    """Convert Timestream response into headers and row lists for tabulate."""
    headers = [col["Name"] for col in column_info]

    parsed_rows = []
    for row in rows:
        parsed_row = []
        for datum in row["Data"]:
            if datum.get("NullValue", False):
                parsed_row.append("NULL")
            elif "ScalarValue" in datum:
                parsed_row.append(datum["ScalarValue"])
            elif "TimeSeriesValue" in datum:
                points = datum["TimeSeriesValue"]
                formatted = ", ".join(
                    f"{p['Time']}={p['Value'].get('ScalarValue', '?')}"
                    for p in points[:3]
                )
                if len(points) > 3:
                    formatted += f" ... (+{len(points) - 3} more)"
                parsed_row.append(formatted)
            elif "ArrayValue" in datum:
                parsed_row.append(str(datum["ArrayValue"]))
            else:
                parsed_row.append("N/A")
        parsed_rows.append(parsed_row)

    return headers, parsed_rows


def display_results(headers, rows):
    """Print query results as a formatted table."""
    if not rows:
        print("Query returned no results.")
        return
    print(f"--- Query Results ({len(rows)} rows) ---\n")
    print(tabulate(rows, headers=headers, tablefmt="grid", maxcolwidths=40))


def plot_timestream_data(headers, rows):
    """Generate a time-series plot from Timestream data."""
    if not rows:
        print("No data to plot.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=headers)

    # Find time column (usually named 'time', 'timestamp', or similar)
    time_col = None
    for col in headers:
        if col.lower() in ['time', 'timestamp', 'datetime', 'date']:
            time_col = col
            break

    if not time_col:
        print("Warning: Could not find a time column. Using row index instead.")
        df['index'] = range(len(df))
        time_col = 'index'
    else:
        # Try to convert to datetime
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except Exception as e:
            print(f"Warning: Could not parse time column as datetime: {e}")
            df['index'] = range(len(df))
            time_col = 'index'

    # Find numeric columns to plot
    numeric_cols = []
    for col in headers:
        if col != time_col:
            try:
                # Attempt to convert to numeric
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Check if column has any non-null numeric values
                if df[col].notna().any():
                    numeric_cols.append(col)
            except:
                continue

    if not numeric_cols:
        print("No numeric columns found to plot.")
        return

    # Create the plot
    fig, axes = plt.subplots(len(numeric_cols), 1, figsize=(12, 4 * len(numeric_cols)), squeeze=False)
    fig.suptitle('Timestream Data Visualization', fontsize=16, fontweight='bold')

    for idx, col in enumerate(numeric_cols):
        ax = axes[idx, 0]

        # Plot the data
        ax.plot(df[time_col], df[col], marker='o', linestyle='-', linewidth=2, markersize=4)
        ax.set_xlabel(time_col, fontsize=12)
        ax.set_ylabel(col, fontsize=12)
        ax.set_title(f'{col} over time', fontsize=14)
        ax.grid(True, alpha=0.3)

        # Format x-axis for datetime
        if time_col != 'index':
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()

    # Save the plot
    output_file = 'timestream_plot.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n--- Plot saved to: {output_file} ---")

    # Show the plot
    plt.show()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # --- Create AWS session ---
    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        iot_client = session.client("iot")
    except botocore.exceptions.ProfileNotFound:
        print(f"Error: AWS profile '{args.profile}' not found.")
        print("Run 'aws configure sso' to set up an SSO profile.")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating AWS session: {e}")
        print(f"Hint: Run 'aws sso login --profile {args.profile}' to refresh your SSO token.")
        sys.exit(1)

    # --- List IoT rules ---
    try:
        print("Fetching IoT topic rules...")
        rules = list_all_rules(iot_client)
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDeniedException":
            print("Access denied. Ensure your role has 'iot:ListTopicRules' permission.")
        else:
            print(f"AWS error listing rules: {e}")
        sys.exit(1)

    if not rules:
        print("No IoT topic rules found in this region.")
        sys.exit(0)

    # --- Select a rule ---
    display_rules(rules)
    selected = select_rule(rules)

    # --- Get rule details ---
    try:
        print(f"\nFetching details for rule '{selected['ruleName']}'...")
        rule_detail = iot_client.get_topic_rule(ruleName=selected["ruleName"])
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDeniedException":
            print("Access denied. Ensure your role has 'iot:GetTopicRule' permission.")
        else:
            print(f"AWS error fetching rule: {e}")
        sys.exit(1)

    # --- Find Timestream actions ---
    ts_actions = find_timestream_actions(rule_detail)
    if not ts_actions:
        actions = rule_detail.get("rule", {}).get("actions", [])
        action_types = set()
        for action in actions:
            action_types.update(action.keys())
        print(f"\nNo Timestream actions found in rule '{selected['ruleName']}'.")
        if action_types:
            print(f"Found action types: {', '.join(sorted(action_types))}")
        sys.exit(0)

    # --- Select Timestream action ---
    ts_action = select_timestream_action(ts_actions)
    display_timestream_info(ts_action)

    # --- Query Timestream ---
    query_string = build_query(
        ts_action["databaseName"], ts_action["tableName"], args.query
    )
    print(f"Executing query:\n  {query_string}\n")

    try:
        column_info, rows = execute_timestream_query(session, args.region, query_string)
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDeniedException":
            print("Access denied. Ensure your role has 'timestream:Select' permission.")
        elif error_code == "ValidationException":
            print(f"Query validation error: {e.response['Error']['Message']}")
            print(f"Query was: {query_string}")
        else:
            print(f"AWS error querying Timestream: {e}")
        sys.exit(1)

    # --- Display results ---
    headers, parsed_rows = parse_timestream_response(column_info, rows)
    display_results(headers, parsed_rows)

    # --- Generate plot if requested ---
    if args.plot:
        print("\nGenerating plot...")
        plot_timestream_data(headers, parsed_rows)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
