"""Compare recorded agent tool sessions without rerunning side effects."""

import copy
import difflib
import json


def strip_pointer(value, pointer):
    if not isinstance(pointer,str) or not pointer.startswith('/'):
        raise ValueError('ignore rules must be non-root JSON Pointers')
    import re
    if re.search(r'~(?![01])',pointer):
        raise ValueError('invalid JSON Pointer escape')
    keys=[k.replace('~1','/').replace('~0','~') for k in pointer[1:].split('/')]
    cursor=value
    for key in keys[:-1]:
        try:
            cursor=cursor[int(key)] if isinstance(cursor,list) else cursor[key]
        except (KeyError,IndexError,TypeError,ValueError):
            return
    key=keys[-1]
    if isinstance(cursor,dict):
        cursor.pop(key,None)
    elif isinstance(cursor,list) and key.isdigit() and int(key)<len(cursor):
        cursor[int(key)]={'$ignored':True}


def analyze(data):
    rules=data.get('ignore',[])
    def normalize(calls):
        result=copy.deepcopy(calls)
        for call in result:
            if not isinstance(call.get('tool'),str):
                raise ValueError('every call needs a tool name')
            for rule in rules: strip_pointer(call,rule)
        return result
    expected, observed=normalize(data['expected']),normalize(data['observed'])
    key=lambda c:json.dumps([c.get('tool'),c.get('arguments',{})],sort_keys=True,allow_nan=False)
    matcher=difflib.SequenceMatcher(a=list(map(key,expected)),b=list(map(key,observed)),autojunk=False)
    changes=[]
    for tag,a,b,c,d in matcher.get_opcodes():
        if tag=='equal':
            for i,j in zip(range(a,b),range(c,d)):
                if expected[i]!=observed[j]:
                    changes.append({'kind':'response_changed','expected_index':i,'observed_index':j,'expected':expected[i],'observed':observed[j]})
        else:
            changes.append({'kind':tag,'expected_range':[a,b],'observed_range':[c,d],'expected':expected[a:b],'observed':observed[c:d]})
    return {'matches':not changes,'ignored_pointers':rules,'changes':changes}


def main():
    """Read one UTF-8 JSON document and emit one machine-readable report."""
    import argparse
    import json
    import sys
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON input path, or - for stdin")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("input must be a JSON object")
        result = analyze(data)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
