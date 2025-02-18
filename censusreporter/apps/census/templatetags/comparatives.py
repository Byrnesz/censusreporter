import json
from django import template
from django.utils.safestring import mark_safe

from logging import getLogger

logger = getLogger('census.templatetags.comparatives')

register = template.Library()

@register.inclusion_tag('profile/_blocks/_comparative_list_item.html')
def build_comparative_item(sumlev, stat, stat_type, geography):
    this_place = f"{geography['this']['full_name']} {geography['this']['full_geoid']}"
    if sumlev == 'CBSA':
        place_name = 'the %s' % geography['parents'][sumlev]['full_name']
    else:
        place_name = geography['parents'][sumlev]['short_name']

    index = stat['index'][sumlev]
    stat_prefix_phrase = mark_safe(f"<strong>{ place_name }</strong>")
    try:
        if index and stat_type != 'count': # we can "madlib" it
            # stat_prefix_phrase has markup
            stat_prefix_phrase = mark_safe(f"{comparison_index_phrase(index)} the {stat_type_to_number_noun(stat_type)} in { place_name }")
    except ValueError as e:
        logger.error(f"Unexpected error computing stat_prefix_phrase for {this_place} compared to {place_name} {json.dumps(stat['metadata'])}")
        logger.exception(e)


    item_context = {
        'place_name': place_name,
        'stat_type': stat_type,
        'value': stat['values'][sumlev],
        'index': index,
        'error': stat['error'][sumlev],
        'error_ratio': stat['error_ratio'][sumlev],
        'numerator': stat['numerators'][sumlev],
        'numerator_error': stat['numerator_errors'][sumlev],
        'stat_prefix_phrase': stat_prefix_phrase
    }
    return item_context

def comparison_index_phrase(value):
    '''
    Each stat on the profile page can have nation-, state- and county-level
    values, indexed to 100 for comparisons (that is, expressed as a percentage
    of that statistic's value for the profile geography). That index value can
    be passed into this template filter to generate a comparative phrase.

    The COMPARISON_PHRASE_MAP defines the comparative phrases; the dict keys
    are the lower boundary of the range of values that result in that phrase.

    For example, the effective range of index values that return the phrase
    "about half" would be 45 to 55.
    '''
    # make sure we have an int for comparison
    index = round(float(value))

    # get lower boundaries for each phrase in the map
    thresholds = list(sorted(COMPARISON_PHRASE_MAP.keys()))

    # get highest boundary that's less than the index value we've been passed
    phrase_key = max(filter(lambda t: t <= index, thresholds))

    phrase_bits = COMPARISON_PHRASE_MAP[phrase_key]
    phrase = "<strong>%s</strong> %s" % (phrase_bits[0], phrase_bits[1])
    return phrase

def stat_type_to_number_noun(stat_type):
    if stat_type == 'dollar':
        return 'amount'
    elif stat_type == 'percentage':
        return 'rate'
    return 'figure'

COMPARISON_PHRASE_MAP = {
    206: ["more than double", ""],
    195: ["about double", ""],
    180: ["nearly double", ""],
    161: ["more than 1.5 times", ""],
    145: ["about 1.5 times", ""],
    135: ["about 1.4 times", ""],
    128: ["about 1.3 times", ""],
    122: ["about 25 percent higher", "than"],
    115: ["about 20 percent higher", "than"],
    107: ["about 10 percent higher", "than"],
    103: ["a little higher", "than"],
    98: ["about the same as", ""],
    94: ["a little less", "than"],
    86: ["about 90 percent", "of"],
    78: ["about 80 percent", "of"],
    72: ["about three-quarters", "of"],
    64: ["about two-thirds", "of"],
    56: ["about three-fifths", "of"],
    45: ["about half", ""],
    37: ["about two-fifths", "of"],
    30: ["about one-third", "of"],
    23: ["about one-quarter", "of"],
    17: ["about one-fifth", "of"],
    13: ["less than a fifth", "of"],
    8: ["about 10 percent", "of"],
    0: ["less than 10 percent", "of"],
}
