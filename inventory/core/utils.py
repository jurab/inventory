
import ast
import functools
import inspect
import json
import pprint
import re
import urllib.parse
import urllib.request

from collections import Counter, OrderedDict
from copy import copy
from functools import reduce
from itertools import groupby
from textwrap import indent as indent_fn
from typing import Any, Callable, Dict, Iterable, Sequence, Tuple, Type, TypeVar

from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import OperationalError, connection
from django.db.models import (
    Case,
    Field,
    IntegerField,
    Model,
    PositiveIntegerField,
    QuerySet,
    Value,
    When,
)
from django.db.models.aggregates import Count
from django.utils.deprecation import MiddlewareMixin


def request(url, data, method, headers, timeout=3):

    if method == 'GET':
        url = f"{url}?{urllib.parse.urlencode(data)}"
        r = urllib.request.Request(url)
        for item in headers.items():
            r.add_header(*item)
        response = urllib.request.urlopen(r, timeout=timeout)
        data = response.read().decode('utf-8')
        return data

    if method == 'POST':
        data = json.dumps(data).encode('utf-8')
        request = urllib.request.Request(url, data=data, headers=headers)  # this will make the method "POST"
        response = urllib.request.urlopen(request, timeout=timeout).read()
        return response

    raise ValueError(f"Unknown HTTP method {method}")


def parse_event(event):
    query_param_string = event['rawQueryString']
    query_kwargs = dict([tuple(kwarg.split('=')) for kwarg in query_param_string.split('&')])
    method = event['requestContext']['http']['method']

    return method, query_kwargs


def duple(d, fields):
    return (d[field] for field in fields)


def rgetattr(obj, attr, *args):
    """
    Recursive getattr function.
    """
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))


def rget(obj, attr, *args):
    """
    Recursive getattr function.
    """
    def _get(obj, attr):
        return None if not obj else obj.get(attr, *args)
    return functools.reduce(_get, [obj] + attr.split('.'))


T = TypeVar('T', bound=Model)


def aggregate_to_dict(
    values: Sequence[Tuple[Any, ...]], idx: int, fnc: Callable[..., Any] = sum
) -> Dict[Any, Any]:
    """
    Takes a list of lists, groups by idx and aggregates by fnc

    Example: [('a', 1, 10), ('b', 2, 3), ('a', 2, 20)] -> {'a': [3, 30], 'b': [2, 3]}
    """
    index_function = lambda x: x[idx]
    if len(values[0]) == 2:  # We assume all values have same length
        return {key: fnc(item[1] for item in group) for key, group in groupby(
            sorted(values, key=index_function), key=index_function
        )}

    indices = list(range(len(values[0])))
    indices.pop(idx)
    grouped = {key: [[item[i] for i in indices] for item in group] for key, group in groupby(
        sorted(values, key=index_function), key=index_function
    )}

    return {key: [fnc(item[i] for item in group) for i in range(len(group[0]))] for key, group in grouped.items()}


def decapitalize(string):
    return string[0].lower() + string[1:]


def group_by(data, attribute):

    def _get_final_attribute(item, attributes):
        attributes = attributes.split('.')
        out = getattr(item, attributes[0])

        for attribute in attributes[1:]:
            out = getattr(out, attribute)
        return out

    out = OrderedDict()

    for item in data:
        if type(attribute) == str:
            key = _get_final_attribute(item, attribute)
            out[key] = out.get(key, []) + [item]
        if type(attribute) == int:
            key = item[attribute]
            item = item[:attribute] + item[attribute + 1:]
            out[key] = out.get(key, []) + [item]
    return out


def fk_and_filter(qs, column, ids):
    column_q = column + '__in'
    return qs.filter(**{column_q: ids}).annotate(obj_count=Count(column)).filter(obj_count=len(ids))


def dictionary_annotation(
    qs: QuerySet[T],
    key_column_name: str,
    new_column_name: str,
    field_type: Type[Field],
    data_dict: Dict[Any, Any],
    default: Any = None,
) -> QuerySet[T]:
    """Lookup a value in a dictionary based on a value in the DB for each object and annotate each separately in 1 query."""

    cases = [When(**{key_column_name: key, 'then': Value(data_dict.get(key, default))}) for key in data_dict.keys()]
    out = qs.annotate(
        **{new_column_name: Case(*cases, output_field=field_type(), default=default)}
    )

    return out


def where(iterable, default=None, **conditions):
    """For condition a=1 return the first item in iterable where item.a==1."""
    conditions = {key.replace('__', '.'): val for key, val in conditions.items()}
    for item in iterable:
        for attr, val in conditions.items():
            if rgetattr(item, attr, None) != val:
                break
        else:
            return item

    return default


def case_order_qs(qs, prior_ordering, fields_lookups_values, exclude_no_case=False):
    """
    Order a qs by prior ordering and then case by case based on the fields_lookups_values.

    Example: first return items that start with a string, followed bu items that contain the string,
             followed by everything else. Pre-order by id.

             fields_lookups_values = [
                (field, 'startswith', search_string),
                (field, 'icontains', search_string),
             ]
    """
    reverse_enumerated_lookups = zip(reversed(range(len(fields_lookups_values))), fields_lookups_values)
    cases = [When(**{f"{field}__{lookup}": value}, then=Value(i + 1)) for i, (field, lookup, value) in reverse_enumerated_lookups]

    qs = qs.annotate(
        _searchresultpriority=Case(
            *cases,
            output_field=PositiveIntegerField(),
            default=0
        )
    ).order_by('-_searchresultpriority', prior_ordering)

    if exclude_no_case:
        qs = qs.exclude(_searchresultpriority=0)

    return qs


def eval_or_none(expression):
    """Safely evaluate a python expression including strings and None"""
    if type(expression) is not str:
        return expression
    elif not expression:
        return None
    elif expression in ('True', 'False'):
        return ast.literal_eval(expression)
    elif re.match(r'^[a-zA-Z0-9_-]+$', expression):
        return str(expression)
    else:
        return ast.literal_eval(expression)


def apply_custom_filters(qs, filters, kwargs):
    for filter_field, method in filters.items():
        assert hasattr(method, 'apply'), f"`apply` method not found on {method}"
        value = eval_or_none(kwargs.get(filter_field, None))
        if value:
            qs = method.apply(qs, value)

    return qs


def camel_to_snake(camel):
    out = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', out).lower()


def sort_qs_by_ids(qs, ids):
    """Sort a queryset based on an iterable of ids."""
    cases = [When(pk=pk, then=sort_order) for sort_order, pk in enumerate(ids)]
    out = qs.annotate(sort_order=Case(*cases, output_field=IntegerField())).order_by('sort_order')

    return out


def has_reverse_relationship(obj):
    obj_has_reverse = False
    if obj.id is not None:
        for reverse in [f for f in obj._meta.get_fields() if f.auto_created and not f.concrete]:
            name = reverse.get_accessor_name()
            has_reverse_one_to_one = reverse.one_to_one and hasattr(obj, name)
            has_reverse_other = not reverse.one_to_one and getattr(obj, name).count()
            if has_reverse_one_to_one or has_reverse_other:
                obj_has_reverse = True
    return obj_has_reverse


def get_index_or_default(item, order, default=9999):
    try:
        return order.index(item)
    except ValueError:
        return default


def inherit_from(Child, Parent, persist_meta=False):
    """Return a class that is equivalent to Child(Parent) including Parent bases."""
    PersistMeta = copy(Child.Meta) if hasattr(Child, 'Meta') else None

    if persist_meta:
        Child.Meta = PersistMeta

    # Prepare bases
    child_bases = inspect.getmro(Child)
    parent_bases = inspect.getmro(Parent)
    bases = tuple([item for item in parent_bases if item not in child_bases]) + child_bases

    # Construct the new return type
    try:
        Child = type(Child.__name__, bases, Child.__dict__.copy())
    except AttributeError as e:
        if str(e) == 'Meta':
            raise AttributeError('Attribute Error in graphene library. Try setting persist_meta=True in the inherit_from method call.')
        raise e
    except TypeError as e:
        e.message = f"Likely a meta class mismatch. {type(Child)} and {type(Parent)} not compatible for inheritance."
        raise e

    if persist_meta:
        Child.Meta = PersistMeta

    return Child


def get_method_parent_class(meth):
    for cls in inspect.getmro(meth.im_class):
        if meth.__name__ in cls.__dict__:
            return cls
    return None


def get_registered_node_type(name):
    for NodeType in settings.GRAPHENE_NODES:
        if NodeType.__name__ == name:
            return NodeType
    raise ValueError('Could not find NodeType', name)


def get_primitive_node_type(name):
    for NodeType in settings.GRAPHENE_PRIMITIVE_NODES:
        if NodeType.__name__ == name:
            return NodeType
    raise ValueError('Could not find _NodeType', name)


def copy_class(TargetClass, with_bases=True):
    """Copy class either as a complete equivalent, or create a class with exactly the same attributes, but no bases by with_bases=False."""
    return type(TargetClass.__name__, TargetClass.__bases__ if with_bases else tuple(), dict(TargetClass.__dict__.items()))


def match_type_to(to_mutate, to_apply):
    return type(to_apply)(to_mutate)


def flatten(l):
    if l is None:
        return None
    return [item for sublist in l for item in sublist]


class DisableCsrfCheck(MiddlewareMixin):

    def process_request(self, req):
        attr = '_dont_enforce_csrf_checks'
        if not getattr(req, attr, False):
            setattr(req, attr, True)


class NoQuery:

    def __init__(self, msg='', allowed_count=0, strict=False, print_sql=False):
        self.msg = msg + ' '
        self.allowed_count = allowed_count
        self.strict = strict
        self.print_sql = print_sql

    def __enter__(self):
        self.start = len(connection.queries)
        return None

    def __exit__(self, _type, value, traceback):

        queries = connection.queries
        queries = [query for query in queries if 'silk_request' not in query['sql']]

        query_count = len(queries)

        msg = self.msg + f"{query_count - self.start}/{self.allowed_count} allowed queries sent."

        if self.start + self.allowed_count < query_count:
            if self.strict:
                raise OperationalError(msg)
            else:
                print(msg)
        return None


def print_admin_form_changes(form):
    data = []
    for name, field in form.fields.items():
        prefixed_name = form.add_prefix(name)
        data_value = field.widget.value_from_datadict(form.data, form.files, prefixed_name)
        if not field.show_hidden_initial:
            # Use the BoundField's initial as this is the value passed to
            # the widget.
            initial_value = form[name].initial
        else:
            initial_prefixed_name = form.add_initial_prefix(name)
            hidden_widget = field.hidden_widget()
            try:
                initial_value = field.to_python(hidden_widget.value_from_datadict(
                    form.data, form.files, initial_prefixed_name))
            except forms.ValidationError:
                # Always assume data has changed if validation fails.
                data.append(name)
                continue
        if field.has_changed(initial_value, data_value):
            print(name, data_value)


def clone_throughs(throughs, **kwargs):

    if not throughs:
        return

    to_remove = ['id']
    for key in kwargs.keys():
        if '_id' in key:
            to_remove += [key, key.replace('_id', '')]
        else:
            to_remove += [key, f'{key}_id']

    Model = throughs.model
    params = {'id': None, **kwargs}
    to_remove = {attr: None for attr in to_remove}

    for t in throughs:
        t.__dict__.update(**to_remove)
        for key, value in params.items():
            setattr(t, key, value)

    Model.objects.bulk_create(throughs)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def color_string(string, colors):
    return reduce(lambda a, b: a + b, colors) + string + Colors.END


def colored_print(string, colors):
    print(color_string(string, colors))


def debug_print_conditions(message='', **kwargs):
    out = [color_string(name, [Colors.RED, Colors.GREEN][condition]) for name, condition in kwargs.items()]
    print(message, *out)


def align_string(s, n):
    s = s + ' ' * (n - len(s))
    return s[:n]


def model_to_str(model):
    return '.'.join((model._meta.app_label, model._meta.object_name))


def get_duplicates(iterable):
    return [item for item, count in Counter(iterable).items() if count > 1]


def validate_unique(iterable):
    duplicate_keys = get_duplicates([key for key, value in iterable])
    if duplicate_keys:
        raise KeyError(f'Duplicate keys found in {type(iterable)}: {", ".join(duplicate_keys)}')


def get_ids(list_or_qs):
    if not list_or_qs:
        return set()

    if type(list_or_qs) == QuerySet:
        return set(list_or_qs.values_list('id', flat=True))

    try:
        return set(map(int, list_or_qs))  # items are int castable values
    except TypeError:
        return {int(getattr(item, 'id', None)) for item in list_or_qs}


def filter_ids_strict(ids, queryset):
    """Filter a queryset by id and raise an error if any of the ids don't exist."""
    out = queryset.filter(id__in=ids)
    if out.count() != len(ids):
        missing = get_ids(ids) - get_ids(out.values_list('id', flat=True))
        raise queryset.model.DoesNotExist(f"{queryset.model.__name__} {','.join(map(str, missing))} not found.")
    return out


def logfmt(obj, indent=0, no_sort=False) -> str:
    """Used for prettyprinting in logs.
    Custom indentation of output can be specified with indent param.
    If set or Sequence is passed as obj it will be sorted.
    """
    if isinstance(obj, (set, frozenset, Sequence)):
        if no_sort:
            obj = list(obj)
        else:
            obj = sorted(obj)
    return indent_fn(pprint.pformat(obj, compact=True), ' ' * indent)


def sceround(pkscores: Iterable[Tuple[Any, float]], precision=3):
    i = 10**precision
    return [(a, round(b * i) / i)for a, b in pkscores]


def names_enum(*l):
    return ((item, item.capitalize()) for item in l)


def round_or_none(number, decimal_places):
    return round(number, decimal_places) if number else None


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper


def has_annotation(qs, field):
    return field in qs.query.annotations
