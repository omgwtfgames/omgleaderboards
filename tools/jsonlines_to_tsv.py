# -*- coding: utf-8 -*-
# This tool converts the JSON Lines output by export_to_jsonlines.py
# into TSV (tab-separated) format. You should edit the extra_fields
# variable to reflect any JSON dictionary key inside the 'extra' field.
#
# Usage:
# jsonlines_to_tsv.py scores.json >all-scores.tsv
# jsonlines_to_tsv.py golden-scarab scores.json >gs-scores.tsv
#

import sys
import json

# this specifies the order of the fields to output
# regular fields
fieldnames = [u'game_id', u'date', u'score', u'nickname',
              u'platform', u'__id__', u'__name__', u'__key__']

# fields that are lists (output comma separated)
list_fields = [u'timeframes']

# the dictionary keys for the 'extra' field, which become their own columns
extra_fields = [u'multiplier', u'time']

null_symbol = u'__NULL__'

if __name__ == "__main__":
    game_id = None
    if len(sys.argv) > 2:
        game_id = sys.argv[1]
        infilename = sys.argv[2]
    elif len(sys.argv) == 2:
        infilename = sys.argv[1]

    print u'\t'.join(fieldnames + list_fields + extra_fields)

    with open(infilename, 'r') as f:
        for l in f:
            s = json.loads(l)
            if game_id and s['game_id'] != game_id:
                continue

            fields = [unicode(s.get(fieldname, null_symbol)) for fieldname in fieldnames]

            # fields that are lists get comma separated
            for fieldname in list_fields:
                if fieldname in s:
                    fields += [u','.join(s[fieldname])]
                else:
                    fields += [null_symbol]

            # anything listed in the 'extra' field as a dictionary gets
            # split out into their own columns
            if isinstance(s['extra'], dict):
                fields += [unicode(s['extra'].get(fieldname, null_symbol))
                           for fieldname in extra_fields]
            else:
                fields += [null_symbol] * len(extra_fields)

            print u'\t'.join(fields)