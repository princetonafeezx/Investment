"""Text tables and charts for projection results."""

# Enable postponed evaluation of annotations for modern type hinting
from __future__ import annotations

# Import sys to check terminal encoding for drawing the ASCII chart
import sys
# Import Mapping for type-hinting read-only dictionary structures
from collections.abc import Mapping
# Import Decimal for high-precision currency calculations
from decimal import Decimal

# Import the projection logic to generate data for comparisons
from investment_engine import project_scenario
# Import TypedDict schemas for structured investment data
from schemas import InvestmentScenario, ProjectionResult
# Import formatting utilities for currency and percentage strings
from storage import format_money, format_percent


def format_single_projection(result: ProjectionResult) -> str:
    """Create an aligned text table for one scenario."""
    # Initialize a list to collect lines of text for the final output
    lines = []
    # Extract the scenario configuration from the projection result
    scenario = result["scenario"]
    # Add the scenario name as the primary header
    lines.append(f"Scenario: {scenario['name']}")
    # Add a sub-header showing the main inputs: principal, rate, term, and compounding type
    lines.append(
        f"Principal {format_money(scenario['initial_principal'])} | "
        f"Rate {format_percent(scenario['annual_rate'])}% | "
        f"Years {scenario['years']} | "
        f"Compounding {scenario['compounding']}"
    )
    # If the engine produced a warning (e.g., high interest rate), add it to the output
    if result["warning"]:
        lines.append(result["warning"])
    # Add a horizontal separator line
    lines.append("-" * 108)
    # Define and add the table column headers with specific text alignments
    lines.append(
        f"{'Year':<6}"
        f"{'Start':>14}"
        f"{'Contrib':>14}"
        f"{'Interest':>14}"
        f"{'End':>16}"
        f"{'Real End':>16}"
        f"{'Note':>10}"
    )
    # Add another separator under the header
    lines.append("-" * 108)

    # Iterate through each year of data in the projection result
    for row in result["rows"]:
        # Mark every 5th year as a "milestone" for easier visual scanning
        milestone_note = "milestone" if row["year"] % 5 == 0 else ""
        # Format the numeric data into a row string with aligned columns
        lines.append(
            f"{row['year']:<6}"
            f"{format_money(row['starting_balance']):>14}"
            f"{format_money(row['contributions']):>14}"
            f"{format_money(row['interest_earned']):>14}"
            f"{format_money(row['ending_balance']):>16}"
            f"{format_money(row['real_balance']):>16}"
            f"{milestone_note:>10}"
        )

    # Add a closing separator for the main table body
    lines.append("-" * 108)
    # Add summary lines for total money put in vs. total interest gained
    lines.append(
        f"Total contributed: {format_money(result['total_contributed'])} | "
        f"Total earned: {format_money(result['total_earned'])}"
    )
    # Show the nominal ending balance alongside the inflation-adjusted "real" balance
    lines.append(
        f"Ending balance: {format_money(result['ending_balance'])} | "
        f"Inflation-adjusted ending balance: {format_money(result['real_ending_balance'])}"
    )
    # Show the estimated difference in value caused by inflation over the term
    lines.append(f"Purchasing power loss estimate: {format_money(result['purchasing_power_loss'])}")
    # Join all collected lines into a single string separated by newlines
    return "\n".join(lines)


def compare_scenarios(scenarios: Mapping[str, InvestmentScenario]) -> str:
    """Compare up to four scenarios side by side."""
    # Return a message if no scenarios are provided for comparison
    if not scenarios:
        return "No scenarios are saved yet."
    # Enforce a limit of 4 scenarios to ensure the table fits within typical terminal widths
    if len(scenarios) > 4:
        return "Please compare four scenarios or fewer."

    # Dictionary to store the results of each projection and a counter for the longest term
    results: dict[str, ProjectionResult] = {}
    max_years = 0
    # Run the projection engine for every provided scenario
    for name, scenario in scenarios.items():
        results[name] = project_scenario(scenario)
        # Track the maximum number of years among all scenarios to determine table height
        max_years = max(max_years, int(scenario["years"]))

    # Get the list of scenario names for header creation
    names = list(results)
    lines = []
    # Build the table header with the Year column and truncated scenario names
    header = f"{'Year':<6}"
    for name in names:
        header += f"{name[:16]:>18}"
    lines.append(header)
    # Add a separator line matching the total width of the header
    lines.append("-" * len(header))

    # Loop through each year up to the longest scenario duration
    for year_number in range(1, max_years + 1):
        line = f"{year_number:<6}"
        # For each scenario, check if it has data for the current year
        for name in names:
            rows = results[name]["rows"]
            # If the year is within the scenario's term, add the ending balance
            if year_number <= len(rows):
                line += f"{format_money(rows[year_number - 1]['ending_balance']):>18}"
            # Otherwise, add a dash to indicate the scenario has ended
            else:
                line += f"{'-':>18}"
        lines.append(line)

    # Add a bottom separator line
    lines.append("-" * len(header))
    # Prepare summary rows for total contributions and total earnings
    contributed_line = f"{'Contrib':<6}"
    earned_line = f"{'Earned':<6}"
    # Iterate through scenario results to build the summary rows
    for name in names:
        contributed_line += f"{format_money(results[name]['total_contributed']):>18}"
        earned_line += f"{format_money(results[name]['total_earned']):>18}"
    lines.append(contributed_line)
    lines.append(earned_line)
    # Return the comparison table as a single newline-joined string
    return "\n".join(lines)


def build_growth_chart(result: ProjectionResult, width: int = 80) -> str:
    """Draw a text-based bar chart using principal and interest portions."""
    # Extract the yearly data rows
    rows = result["rows"]
    # If there's no data (0 years), return a failure message
    if not rows:
        return "No chart data available."

    # Calculate the horizontal space available for the bars, reserving room for labels
    bar_width = max(20, width - 26)
    # Determine the highest balance to scale the chart bars accordingly
    max_balance = max(row["ending_balance"] for row in rows) or Decimal(1)
    # Detect the current output encoding to determine which characters to use for the bars
    encoding = sys.stdout.encoding or "utf-8"
    try:
        # Check if the terminal can display the preferred block characters
        "█".encode(encoding)
        principal_char = "█" # Solid block for money contributed
        interest_char = "░"  # Light shade for interest earned
    except (UnicodeEncodeError, LookupError, TypeError):
        # Fall back to standard ASCII characters if Unicode blocks aren't supported
        principal_char = "#"
        interest_char = "."

    # Create a legend to explain what the bar segments represent
    legend = f"Legend: {principal_char} principal/contributions, {interest_char} growth"
    # Start the chart output with a title and the legend
    lines = ["Growth chart", legend]
    # Add a decorative line under the title
    lines.append("-" * min(width, 80))
    # Convert width to Decimal for precise ratio calculations
    bar_dec = Decimal(bar_width)

    # Loop through the year rows to generate the bars
    for row in rows:
        # Calculate how many character slots to fill for principal and interest segments
        principal_width = int((row["principal_portion"] / max_balance) * bar_dec)
        interest_width = int((row["interest_portion"] / max_balance) * bar_dec)
        # Ensure that even small balances show at least one character
        if principal_width + interest_width == 0:
            principal_width = 1
        # Construct the bar string by repeating the characters
        bar = (principal_char * principal_width) + (interest_char * interest_width)
        # Format the dollar amount for the end of the line
        end_bal = format_money(row["ending_balance"])
        # Add the year label, the bar (left-aligned), and the total balance
        lines.append(f"Year {row['year']:>2} {bar:<{bar_width}} {end_bal}")

    # Return the final chart as a multiline string
    return "\n".join(lines)