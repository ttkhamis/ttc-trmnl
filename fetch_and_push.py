import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

LIVE_ALERTS_URL = 'https://alerts.ttc.ca/api/alerts/live-alerts'
TARGET_LINES = {'1', '2', '5'}
TORONTO_TZ = ZoneInfo('America/Toronto')

EXCLUDED_EFFECTS = {
    'reduced speed zone',
    'subway closure - early access',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}

SEVERITY_MAP = {
    'Critical': 'Critical',
    'Major':    'Major',
    'Minor':    'Minor',
    'Info':     'Info',
}

COMMUTE_WINDOWS = [
    (6, 8),   # 6:00–8:00 AM
    (15, 17), # 3:00–5:00 PM
]


def in_commute_window() -> bool:
    now = datetime.now(TORONTO_TZ)
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    for start_h, end_h in COMMUTE_WINDOWS:
        if start_h <= now.hour < end_h:
            return True
    return False


def iso_to_local(iso_str: str | None) -> str | None:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        local = dt.astimezone(TORONTO_TZ)
        return local.strftime('%b %-d, %Y %-I:%M %p')
    except Exception:
        return iso_str


def fetch_alerts() -> tuple[list, str | None]:
    try:
        r = requests.get(LIVE_ALERTS_URL, headers=HEADERS, timeout=12)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        return [], f'Could not reach TTC alerts API: {e}'
    except ValueError:
        return [], 'TTC API returned unexpected data format'

    alerts = []
    for item in data.get('routes', []):
        route = str(item.get('route', '')).strip()
        if route not in TARGET_LINES:
            continue
        if item.get('routeType', '').lower() != 'subway':
            continue
        if item.get('effectDesc', '').strip().lower() in EXCLUDED_EFFECTS:
            continue

        active = item.get('activePeriod', {})
        start = iso_to_local(active.get('start'))
        end   = iso_to_local(active.get('end'))
        time_range = f'{start} – {end}' if start and end else start or end

        alerts.append({
            'line':       int(route),
            'title':      item.get('title', '').strip(),
            'effect':     item.get('effectDesc', '').strip(),
            'severity':   SEVERITY_MAP.get(item.get('severity', ''), 'Info'),
            'cause':      item.get('causeDescription', '').strip(),
            'direction':  item.get('direction', '').strip(),
            'time_range': time_range,
        })

    alerts.sort(key=lambda a: (a['line'], a['severity']))
    return alerts, None


def build_payload(alerts: list, fetch_time: str, run_number: str = 'local') -> dict:
    def line_vars(line_num: int) -> dict:
        line_alerts = [a for a in alerts if a['line'] == line_num]
        return {
            f'line{line_num}_ok':     len(line_alerts) == 0,
            f'line{line_num}_count':  len(line_alerts),
            f'line{line_num}_alerts': [
                {
                    'severity':  a['severity'],
                    'title':     a['title'],
                    'effect':    a['effect'],
                    'cause':     a['cause'],
                    'direction': a['direction'],
                    'time_range': a['time_range'],
                }
                for a in line_alerts
            ],
        }

    merge_vars = {'updated_at': fetch_time, 'run_number': run_number}
    for n in (1, 2, 5):
        merge_vars.update(line_vars(n))

    return {'merge_variables': merge_vars}


def push_to_trmnl(payload: dict, webhook_url: str, api_key: str) -> None:
    import json
    print(f'Sending payload: {json.dumps(payload, indent=2)}')
    headers = {'Authorization': f'Bearer {api_key}'}
    resp = requests.post(webhook_url, json=payload, headers=headers, timeout=15)
    print(f'TRMNL response: HTTP {resp.status_code}')
    print(f'TRMNL response body: {resp.text}')
    if resp.status_code >= 500:
        print(f'Warning: TRMNL server error {resp.status_code} — will retry next run.')
        return
    resp.raise_for_status()


def main() -> None:
    # Uncomment when done testing:
    # if not in_commute_window():
    #     print('Outside commute window — skipping.')
    #     sys.exit(0)

    webhook_url = os.environ.get('TRMNL_WEBHOOK_URL')
    if not webhook_url:
        print('Error: TRMNL_WEBHOOK_URL environment variable not set.', file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get('TRMNL_API_KEY')
    if not api_key:
        print('Error: TRMNL_API_KEY environment variable not set.', file=sys.stderr)
        sys.exit(1)

    alerts, error = fetch_alerts()
    if error:
        print(f'Warning: {error}', file=sys.stderr)

    fetch_time = datetime.now(TORONTO_TZ).strftime('%a %-I:%M %p')
    run_number = os.environ.get('GITHUB_RUN_NUMBER', 'local')
    payload = build_payload(alerts, fetch_time, run_number)

    push_to_trmnl(payload, webhook_url, api_key)


if __name__ == '__main__':
    main()
