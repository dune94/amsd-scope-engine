# Loads config/<name>.yml, merged with config.local/<name>.yml when it exists (untracked, organisation-specific values), and
# agents/<name>.yml. Environment values (paths, credentials) come from the untracked .env in the project folder.
import json, os, pathlib, re, yaml

PROJECT = pathlib.Path(__file__).resolve().parents[1]
LOCAL = PROJECT / 'config.local'
PLACEHOLDER = re.compile(r'\{([a-z_]+)\}')


def _load_env():
    f = PROJECT / '.env'
    if f.exists():
        for line in f.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_env()


def path(p):
    """Expands ~ and $VARS; a relative path is relative to the project folder."""
    p = pathlib.Path(os.path.expanduser(os.path.expandvars(str(p))))
    return p if p.is_absolute() else PROJECT / p


def _merge(base, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict): _merge(base[k], v)
        else: base[k] = v
    return base


def load(name):
    cfg = yaml.safe_load((PROJECT / 'config' / f'{name}.yml').read_text())
    local = LOCAL / f'{name}.yml'
    return _merge(cfg, yaml.safe_load(local.read_text()) or {}) if local.exists() else cfg


def agent_file(name):
    """agents/<name>, or config.local/agents/<name> when a local version exists (organisation-specific wording)."""
    local = LOCAL / 'agents' / name
    return local if local.exists() else PROJECT / 'agents' / name


class Agent:
    def __init__(self, name):
        d = yaml.safe_load((PROJECT / 'agents' / f'{name}.yml').read_text())
        self.__dict__.update(d)
        self.si_text = agent_file(d['system_instructions']).read_text()
        self.prompt_text = agent_file(d['prompt']).read_text()
        self.schema_obj = json.loads(agent_file(d['schema']).read_text())

    @staticmethod
    def fill(template, values):
        missing = [k for k in PLACEHOLDER.findall(template) if k not in values]
        if missing: raise KeyError(f'no value for placeholder(s) {missing}')
        return PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), template)

    def render(self, **values):
        """(system instructions, prompt) with every {placeholder} filled; params from the agent file are available as values."""
        v = dict(self.params or {}, **values)
        return self.fill(self.si_text, v), self.fill(self.prompt_text, v)

    def message(self, **values):
        """Text sent on stdin. inline: SI and prompt joined in inline_order; otherwise the prompt only (SI goes as a system prompt)."""
        si, pr = self.render(**values)
        if self.si_mode != 'inline': return pr
        return '\n\n'.join({'si': si, 'prompt': pr}[k] for k in self.inline_order)


AGENTS = ('nouns', 'pick', 'investigate', 'drivers')
