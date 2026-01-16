#!/usr/bin/env python3
"""Extract metrics from analysis results JSON for GitHub Actions output."""

import json
import sys

if __name__ == "__main__":
    try:
        with open('analysis-results.json', 'r') as f:
            data = json.load(f)
        
        metrics = data['metrics']
        
        # Output for GitHub Actions
        print(f"feedback_count={metrics['feedback_processed']}")
        print(f"patterns_count={metrics['patterns_found']}")
        print(f"proposals_count={metrics['proposals_generated']}")
        print(f"high_priority={metrics['high_priority_count']}")
        
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"Error extracting metrics: {e}", file=sys.stderr)
        sys.exit(1)
