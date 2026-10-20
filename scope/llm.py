# Builds and runs one agent call. CLI, flags, model, tools, caps and timeouts all come from config / agents/<name>.yml.
import json, re, shlex, subprocess, tempfile, time
import jsonschema
from . import config

S = config.load('scope')


def bounded(want_mb, cmd):
    return [str(config.path(S['paths']['bounded'])), '--want', str(want_mb), '--'] + list(cmd)


def build(agent, si_file=None, images=()):
    """Full argv for one agent call, already wrapped in the memory cap and timeout."""
    L = S['llm']
    cmd = list(L['command']) + [L['model_flag'], agent.model]
    tools, allowed, turns = list(agent.tools), list(agent.allowed_tools), agent.max_turns
    if images and agent.images:
        tools.append(L['image_tool']); allowed.append(L['image_tool'])
        turns = (turns or 0) + len(images) + L['image_turns_extra']
    cmd += [L['tools_flag'], ','.join(tools) if tools else '']
    if allowed: cmd += [L['allowed_tools_flag']] + allowed
    if turns: cmd += [L['max_turns_flag'], str(turns)]
    if agent.si_mode != 'inline': cmd += [L['system_prompt_flags'][agent.si_mode], str(si_file)]
    return bounded(agent.memory_mb, ['timeout', str(agent.timeout_s)] + cmd)


def image_block(images):
    return ('\n\nIMAGES ATTACHED TO THE TICKET (open each with the Read tool):\n' + '\n'.join(f'- {p}' for p in images)) if images else ''


def parse(stdout, result_field='result'):
    """--output-format json wraps the reply; pull the largest parseable JSON object out of it."""
    try: res = json.loads(stdout)[result_field]
    except Exception: res = stdout
    if not isinstance(res, str): return res if isinstance(res, dict) else None
    cands = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', res, re.S)
    depth, start = 0, None
    for i, ch in enumerate(res):
        if ch == '{':
            if depth == 0: start = i
            depth += 1
        elif ch == '}' and depth:
            depth -= 1
            if depth == 0: cands.append(res[start:i + 1])
    for c in sorted(cands, key=len, reverse=True):
        try: return json.loads(c)
        except Exception: continue
    return None


def call(agent, values, cwd=None, images=(), log=None, raw_path=None):
    """Run the agent; returns (parsed JSON or None, schema errors). images: absolute paths, read from cwd only."""
    use_images = list(images) if agent.images else []
    msg = agent.message(**values) + image_block(use_images)
    si_file = None
    if agent.si_mode != 'inline':
        si_file = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False); si_file.write(agent.render(**values)[0]); si_file.close()
        si_file = si_file.name
    cmd = build(agent, si_file, use_images)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, input=msg, capture_output=True, text=True)
    if log:
        log.write(f"\n$ {' '.join(shlex.quote(c) for c in cmd)}  (agent={agent.name}, cwd={cwd}, {time.time() - t0:.0f}s, exit {r.returncode})\n{r.stderr[-2000:]}\n")
        log.flush()
    if raw_path: raw_path.write_text(r.stdout)
    out = parse(r.stdout, S['llm']['result_field'])
    errs = [] if out is None else [e.message for e in jsonschema.Draft202012Validator(agent.schema_obj).iter_errors(out)]
    return out, errs
