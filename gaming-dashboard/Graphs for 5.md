# Graphs for 5.1: AI-driven anomaly detection / AI triggered risk alerts

Requirement 5.1 states: "Integrate AI models to flag unusual operator activity such as abnormal spikes or drops in stakes, payouts, operating outside licensed game categories, turnover dropping below regulatory viability thresholds".

The graphs should be designed to clearly visualize the activity against a predicted/normal baseline, making the anomaly the focus.

1. Time-Series Graph for Stakes and Payouts
    Type: Dual-axis Time-Series Line Chart (e.g., daily or weekly aggregates).

    Data Series:

    Actual Stakes/Payouts (Primary Line, e.g., Blue).

    AI-Predicted Normal Range (Shaded area or secondary line, e.g., Light Grey/Yellow).

    Anomaly Flagging: Use distinct markers (e.g., Red Dots) on the line whenever the actual data falls outside the AI-predicted normal range (spike or drop). Tooltips should show the precise alert details.

2. Categorical Activity Violation Graph
    Type: Stacked Column Chart or Pie Chart/Donut Chart with Time Series Drill-Down.

    Purpose: To flag operators operating outside licensed game categories.

    Visualization:

    The primary view could be a high-level table/bar chart listing operators.

    The graph would appear upon clicking an operator. It would show their reported Activity by Game Category over a period.

    A prominent Red Bar/Slice would be used for any activity in an unlicensed category, triggering an immediate visual alert.

3. Regulatory Viability Threshold Monitoring Chart
Type: Time-Series Line Chart (similar to a control chart).

Data Series:

Operator Turnover (Line chart, e.g., Blue).

Regulatory Viability Threshold (Fixed horizontal red line).

Anomaly Flagging: The line is highlighted in red/flashing when the Turnover line drops below the threshold line, indicating the AI-triggered risk.
