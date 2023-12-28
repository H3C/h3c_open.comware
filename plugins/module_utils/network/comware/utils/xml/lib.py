"""This module provides several utility functions
for dealing with XML text and ``etree.Element``
XML objects.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.namespaces import NCCONFIG, \
    NCDATA, NCACTION, NETCONFBASE, NETCONFBASE_C, NCDATA_C

try:
    from lxml.builder import ElementMaker

    HAS_LXML = True
except ImportError:
    HAS_LXML = False


def config_element_maker():
    if HAS_LXML:
        return ElementMaker(namespace=NCCONFIG, nsmap={None: NCCONFIG})


def data_element_maker():
    if HAS_LXML:
        return ElementMaker(namespace=NCDATA, nsmap={None: NCDATA})


def action_element_maker():
    if HAS_LXML:
        return ElementMaker(namespace=NCACTION, nsmap={None: NCACTION})


def nc_element_maker():
    if HAS_LXML:
        return ElementMaker(namespace=NETCONFBASE, nsmap={None: NETCONFBASE})


def config_params(pmap, key_map, value_map=None, E=config_element_maker(), fill_in=True):
    if value_map is None:
        value_map = {}
    params = []

    for key, value in list(pmap.items()):
        if fill_in:
            key2 = key_map.get(key, key)
        else:
            key2 = key_map.get(key, None)

        if key2:
            params.append(
                getattr(E, key2)(value_map.get(key, {}).get(value, value)))

    return params


def operation_kwarg(operation=None):
    if operation is None:
        return {}

    return {
        NETCONFBASE_C + 'operation': operation
    }


def _findall_with_ns(query, ele, ns=''):
    return ele.findall('.//{%s}%s' % (ns, query))


def findall_in_data(query, ele):
    return _findall_with_ns(query, ele, ns=NCDATA)


def _find_with_ns(query, ele, ns=''):
    return ele.find('.//{%s}%s' % (ns, query))


def find_in_data(query, ele):
    return _find_with_ns(query, ele, ns=NCDATA)


def find_in_action(query, ele):
    return _find_with_ns(query, ele, ns=NCACTION)


def findall_in_action(query, ele):
    return _findall_with_ns(query, ele, ns=NCACTION)


def find_in_config(query, ele):
    return _find_with_ns(query, ele, ns=NCCONFIG)


def elem_to_dict(elem, ns, key_map, value_map=None):
    """Convert an XML etree.Element to a desired dictionary
    as specified by the key map and value map.
    Args:
        elem (etree.Element): An ancestor element
            of the tags specified in the key map.
        ns (string): The namespace to use
            when searching for XML tags.
        key_map (dict): A mapping from desired
            dictionary keys to XML tag names.
        value_map (dict): A mapping from XML tag names to
            dictionaries of mappings from XML text
            values to desired dictionary values.
    Returns:
        The desired dictionary.
    """
    if value_map is None:
        value_map = {}
    to_dict = {}
    for k, v in key_map.items():
        field = elem.find('.//{0}{1}'.format(ns, v))
        if field is not None:
            text = field.text
            to_dict[k] = value_map.get(v, {}).get(text, text)

    return to_dict


def data_elem_to_dict(elem, key_map, value_map=None):
    if value_map is None:
        value_map = {}
    return elem_to_dict(elem, NCDATA_C, key_map, value_map=value_map)


def reverse_value_map(key_map, value_map):
    """Utility function for creating a
    "reverse" value map from a given key map and value map.
    """
    r_value_map = {}
    for k, v in value_map.items():
        sub_values = r_value_map[key_map[k]] = {}
        for k2, v2 in v.items():
            sub_values[v2] = k2

    return r_value_map


def remove_namespaces(xml):
    """Remove the namespaces from an
    ``etree.Element`` object and return
    the modified object.
    """
    for elem in xml.getiterator():
        split_elem = elem.tag.split('}')
        if len(split_elem) > 1:
            elem.tag = split_elem[1]
    return xml


def get_text(xml, tag):
    """Return the text from a given tag and XML element.
    """
    elem = xml.find(tag)
    if elem is not None:
        return elem.text.strip()
