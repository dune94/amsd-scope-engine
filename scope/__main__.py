"""python3 -m scope <KEY ...> --plan | --run | --drivers-only
python3 -m scope <KEY> --build-pack <DIR>          read the ticket and write a story pack (no agents are run)
python3 -m scope <KEY> --run --story-pack <FILE>    run from a story pack instead of fetching from Jira
Run it under the memory cap:  $SCOPE_BOUNDED --want 1536 -- python3 -u -m scope <KEY> --run
--plan prints every command a run would execute and runs nothing. Stories run one at a time."""
import sys


def usage(msg):
    raise SystemExit(f'{msg}\n\n{__doc__}')


def parse(argv):
    def value(flag):
        if flag not in argv: return None
        i = argv.index(flag)
        if i + 1 >= len(argv) or argv[i + 1].startswith('--'): usage(f'{flag} needs a value')
        return argv[i + 1]
    build_pack, story_pack = value('--build-pack'), value('--story-pack')
    skip = {argv.index(f) + 1 for f in ('--build-pack', '--story-pack') if f in argv}
    keys = [a for i, a in enumerate(argv) if not a.startswith('--') and i not in skip]
    mode = '--run' if '--run' in argv else '--drivers-only' if '--drivers-only' in argv else '--plan'
    if build_pack and (len(keys) != 1 or '--run' in argv or story_pack): usage('--build-pack takes exactly one key and cannot be combined with --run or --story-pack')
    if story_pack and (mode != '--run' or len(keys) != 1): usage('--story-pack needs --run and exactly one key')
    return dict(keys=keys, mode=mode, build_pack=build_pack, story_pack=story_pack)


def main(argv):
    from . import flow, pack
    a = parse(argv)
    if a['build_pack']:
        print('pack:', pack.build_pack(a['keys'][0], a['build_pack']), flush=True)
        return
    for k in a['keys']:
        print(f"\n######## {k} {a['mode']}", flush=True)
        try:
            if a['mode'] == '--plan': flow.plan(k)
            else: flow.go(k, drivers_only=a['mode'] == '--drivers-only', pack_path=a['story_pack'])
        except SystemExit as e: print(f'{k} stopped: {e}', flush=True)
        except Exception as e: print(f'{k} FAILED: {type(e).__name__}: {e}', flush=True)


if __name__ == '__main__':
    main(sys.argv[1:])
