"""python3 -m scope <KEY ...> --plan | --run | --drivers-only
Run it under the memory cap:  $SCOPE_BOUNDED --want 1536 -- python3 -u -m scope <KEY> --run
--plan prints every command a run would execute and runs nothing. Stories run one at a time."""
import sys
from . import flow

keys = [a for a in sys.argv[1:] if not a.startswith('--')]
mode = '--run' if '--run' in sys.argv else '--drivers-only' if '--drivers-only' in sys.argv else '--plan'
for k in keys:
    print(f'\n######## {k} {mode}', flush=True)
    try: flow.plan(k) if mode == '--plan' else flow.go(k, drivers_only=mode == '--drivers-only')
    except SystemExit as e: print(f'{k} stopped: {e}', flush=True)
    except Exception as e: print(f'{k} FAILED: {type(e).__name__}: {e}', flush=True)
