from __future__ import annotations

import json

from avori_discovery import refresh_tracked_watchlist, run_discovery


def main():
    discovery_result = run_discovery()
    tracking_result = refresh_tracked_watchlist()

    print(
        json.dumps(
            {
                "results_path": str(discovery_result["results_path"]),
                "brief_path": str(discovery_result["brief_path"]),
                "tracked_entries": tracking_result["tracked_entries"],
                "refreshed_entries": tracking_result["refreshed_entries"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
