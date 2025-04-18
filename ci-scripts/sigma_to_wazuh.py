#!/usr/bin/env python3
"""
Enhanced Sigma to Wazuh converter script.
• Supports Windows rules with attribute-specific <field> tags.
• Supports Zeek rules: handles AND/OR between multiple selection groups.
  - For OR conditions, generates separate rules per selection group.
  - For AND conditions, combines all fields in one rule.
Reads Sigma .yml/.yaml from ./rules/ → writes Wazuh XML files into ./wazuh/.
"""
import os
import re
import yaml
import xml.etree.ElementTree as ET

# Input/output directories
INPUT_DIR = 'rules'
OUTPUT_DIR = 'wazuh'

# Severity map Sigma -> Wazuh numeric levels\ nLEVEL_MAP = {
    'informational': '5',
    'low':           '7',
    'medium':        '10',
    'high':          '13',
    'critical':      '15'
}

# Always add <options>no_full_log</options>
NO_FULL_LOG = True


def wildcard_to_regex(pattern: str) -> str:
    """
    Convert Sigma wildcards '*' → PCRE2 '.*', escape others.
    """
    return re.escape(pattern).replace(r'\*', '.*')


def indent(elem: ET.Element, level: int = 0):
    """Pretty-print XML indentation."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def parse_condition_map(condition: str) -> dict:
    """
    Parse expressions like 'sel1 and not sel2' or 'sel1 or sel2'
    Returns { 'selection1': neg1, 'selection2': neg2, ... }
    Where negX=True if 'not selectionX'.
    """
    tokens = re.split(r"\s+", condition)
    mapping = {}
    negate = False
    for tok in tokens:
        lt = tok.lower()
        if lt == 'not':
            negate = True
        elif lt.startswith('selection'):
            mapping[tok] = negate
            negate = False
        else:
            continue
    return mapping


def build_rule_base(rule_meta: dict) -> ET.Element:
    """
    Create common <rule> root with metadata, returns its Element.
    """
    rid    = rule_meta['id']
    title  = rule_meta['title']
    refs   = rule_meta['references']
    author = rule_meta['author']
    desc   = rule_meta['description']
    date   = rule_meta['date']
    status = rule_meta['status']
    tags   = rule_meta['tags']
    level  = level = LEVEL_MAP.get(rule_meta['level'], LEVEL_MAP['low'])
    product= rule_meta['logsource'].get('product', '')
    service= rule_meta['logsource'].get('service', '')
    category=rule_meta['logsource'].get('category', '')

    # <group name="sigma,">
    grp_root = ET.Element('group', name='sigma,')
    r = ET.SubElement(grp_root, 'rule', id=str(rid), level=level)

    # info link
    if refs:
        info = ET.SubElement(r, 'info', type='link')
        info.text = refs[0]

    # metadata comments
    for c in (f"Sigma Rule Author: {author}",
              f"Description: {desc}",
              f"Date: {date}",
              f"Status: {status}",
              f"ID: {rid}"):
        r.append(ET.Comment(c))

    # MITRE
    m = ET.SubElement(r, 'mitre')
    for t in tags:
        idn = ET.SubElement(m, 'id')
        idn.text = t

    # description
    d = ET.SubElement(r, 'description')
    d.text = title

    # options
    if NO_FULL_LOG:
        o = ET.SubElement(r, 'options')
        o.text = 'no_full_log'

    # group categories
    groups = [v for v in (category, product, service) if v]
    if groups:
        g = ET.SubElement(r, 'group')
        g.text = ','.join(groups) + ','

    return grp_root


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for fn in os.listdir(INPUT_DIR):
        if not fn.lower().endswith(('.yml', '.yaml')):
            continue
        path = os.path.join(INPUT_DIR, fn)
        with open(path, 'r', encoding='utf-8') as f:
            try:
                rule = yaml.safe_load(f)
            except Exception as e:
                print(f" Failed parsing {fn}: {e}")
                continue

        # Prepare metadata lookup
        meta = {
            'id': rule.get('id',''),
            'title': rule.get('title',''),
            'references': rule.get('references', []),
            'author': rule.get('author',''),
            'description': rule.get('description',''),
            'date': rule.get('date',''),
            'status': rule.get('status',''),
            'tags': rule.get('tags', []),
            'level': rule.get('level','low'),
            'logsource': rule.get('logsource', {})
        }
        detection = rule.get('detection', {})
        cond = detection.get('condition', '')

        product = meta['logsource'].get('product','').lower()
        is_zeek = (product == 'zeek')

        # Zeek rules with OR → multiple <rule> files
        if is_zeek and ' or ' in cond:
            cond_map = parse_condition_map(cond)
            for sel, neg in cond_map.items():
                # selection group dict
                sel_dict = detection.get(sel, {})
                gr = build_rule_base(meta)
                # add full_log fields for each pattern
                for key, vals in sel_dict.items():
                    lst = vals if isinstance(vals, list) else [vals]
                    pats = [wildcard_to_regex(v) for v in lst]
                    regex = '(?i)'
                    if len(pats) > 1:
                        regex += f'(?:{"|".join(pats)})'
                    else:
                        regex += pats[0]
                    fld = ET.SubElement(gr.find('rule'), 'field',
                                        name='full_log', negate=('yes' if neg else 'no'), type='pcre2')
                    fld.text = regex
                # write file
                indent(gr)
                rid = meta['id']
                out = os.path.join(OUTPUT_DIR, f'rule_{rid}_{sel}.xml')
                ET.ElementTree(gr).write(out, encoding='utf-8', xml_declaration=True)
                print(f" Written {out}")
        else:
            # Single rule: Zeek AND or Windows
            gr = build_rule_base(meta)
            r_el = gr.find('rule')
            if is_zeek:
                # all selections together
                for sel_name, sel_dict in detection.items():
                    if not sel_name.startswith('selection'):
                        continue
                    # determine negate
                    neg = False
                    if ' and not '+sel_name in cond or cond.startswith('not '+sel_name):
                        neg = True
                    for key, vals in sel_dict.items():
                        lst = vals if isinstance(vals, list) else [vals]
                        pats = [wildcard_to_regex(v) for v in lst]
                        regex = '(?i)'
                        if len(pats)>1:
                            regex += f'(?:{"|".join(pats)})'
                        else:
                            regex += pats[0]
                        ET.SubElement(r_el, 'field', name='full_log',
                                      negate=('yes' if neg else 'no'), type='pcre2').text = regex
            else:
                # Windows attribute-specific
                selection = detection.get('selection', {})
                for key, vals in selection.items():
                    base = key.split('|')[0]
                    nm = f"win.eventdata.{base[0].lower()}{base[1:]}"
                    lst = vals if isinstance(vals, list) else [vals]
                    regex = '(?i)'+ '|'.join(wildcard_to_regex(v) for v in lst)
                    ET.SubElement(r_el, 'field', name=nm, negate="no", type="pcre2").text = regex
                fp = detection.get('falsepositive', {})
                for key,val in fp.items():
                    base = key.split('|')[0]
                    nm = f"win.eventdata.{base[0].lower()}{base[1:]}"
                    pat = '(?i)^'+ re.escape(val)
                    ET.SubElement(r_el, 'field', name=nm, negate="yes", type="pcre2").text = pat
            # write file
            indent(gr)
            out = os.path.join(OUTPUT_DIR, f'rule_{meta['id']}.xml')
            ET.ElementTree(gr).write(out, encoding='utf-8', xml_declaration=True)
            print(f" Written {out}")

if __name__ == '__main__':
    main()
