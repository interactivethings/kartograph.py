
"""
API 2.0
helper methods for validating options dictionary
"""

import os.path, proj, errors


Error = errors.KartographOptionParseError


def is_str(s):
    return isinstance(s, (str, unicode))


def parse_options(opts):
    """
    check out that the option dict is filled correctly
    """
    # projection
    parse_proj(opts)
    parse_layers(opts)
    parse_bounds(opts)
    parse_export(opts)


def parse_proj(opts):
    """
    checks projections
    """
    if 'proj' not in opts:
        opts['proj'] = {}
    prj = opts['proj']
    if 'id' not in prj:
        if 'bounds' not in opts:
            prj['id'] = 'robinson'
        else:
            prj['id'] = 'laea'
    if prj['id'] not in proj.projections:
        raise Error('unknown projection')
    prjClass = proj.projections[prj['id']]
    for attr in prjClass.attributes():
        if attr not in prj:
            prj[attr] = "auto"


def parse_layers(opts):
    if 'layers' not in opts:
        opts['layers'] = []
    l_id = 0
    g_id = 0
    s_id = 0
    for layer in opts['layers']:
        if 'styles' not in layer:
            layer['styles'] = {}
        if 'src' not in layer and 'special' not in layer:
            raise Error('you need to define the source for your layers')
        if 'src' in layer:
            if not os.path.exists(layer['src']):
                raise Error('layer source not found: ' + layer['src'])
            if 'id' not in layer:
                layer['id'] = 'layer_' + str(l_id)
                l_id += 1
        elif 'special' in layer:
            if layer['special'] == 'graticule':
                if 'id' not in layer:
                    layer['id'] = 'graticule'
                    if g_id > 0:
                        layer['id'] += '_' + str(g_id)
                    g_id += 1
                if 'fill' not in layer['styles']:
                    layer['styles']['fill'] = 'None'
                parse_layer_graticule(layer)
            elif layer['special'] == 'sea':
                if 'id' not in layer:
                    layer['id'] = 'sea'
                    if s_id > 0:
                        layer['id'] += '_' + str(s_id)
                    s_id += 1

        parse_layer_attributes(layer)
        parse_layer_filter(layer)
        parse_layer_join(layer)
        parse_layer_simplify(layer)
        parse_layer_subtract(layer)
        parse_layer_cropping(layer)


def parse_layer_attributes(layer):
    if 'attributes' not in layer:
        layer['attributes'] = []
        return
    attrs = []
    for attr in layer['attributes']:
        if is_str(attr):
            if isinstance(layer['attributes'], list):
                attrs.append({'src': attr, 'tgt': attr})
            elif isinstance(layer['attributes'], dict):
                attrs.append({'src': attr, 'tgt': layer['attributes'][attr]})
        elif isinstance(attr, dict) and 'src' in attr and 'tgt' in attr:
            attrs.append(attr)
    layer['attributes'] = attrs


def parse_layer_filter(layer):
    if 'filter' not in layer:
        layer['filter'] = False
        return
    return  # todo: check valid filter syntax (recursivly, place code in filter.py)
    filter = layer['filter']
    if 'type' not in filter:
        filter['type'] = 'include'
    if 'attribute' not in filter:
        raise Error('layer filter must define an attribute to filter on')
    if 'equals' in filter:
        if isinstance(filter['equals'], (str, unicode, int, float)):
            filter['equals'] = [filter['equals']]
    elif 'greater-than' in filter:
        try:
            filter['greater-than'] = float(filter['greater-than'])
        except ValueError:
            raise Error('could not convert filter value "greater-than" to float')
    elif 'less-than' in filter:
        try:
            filter['less-than'] = float(filter['less-than'])
        except ValueError:
            raise Error('could not convert filter value "less-than" to float')
    else:
        raise Error('you must define either "equals", "greater-than" or "less-than" in the filter')


def parse_layer_join(layer):
    if 'join' not in layer:
        layer['join'] = False
        return
    if layer['join'] is False:
        return

    join = layer['join']
    if 'group-by' not in join:
        raise Error('missing attribute "group-by": you need to specify an attribute by which the features should be joined.')
    if 'groups' not in join:
        join['groups'] = None
    if 'group-as' not in join:
        join['group-as'] = False


def parse_layer_simplify(layer):
    if 'unify-precision' not in layer:
        layer['unify-precision'] = None
    if 'simplify' not in layer:
        layer['simplify'] = 2.0
        return
    if layer['simplify'] is False:
        return
    try:
        layer['simplify'] = float(layer['simplify'])
    except ValueError:
        raise Error('could not convert simplification amount to float')


def parse_layer_subtract(layer):
    if 'subtract-from' not in layer:
        layer['subtract-from'] = False
        return
    if isinstance(layer['subtract-from'], (str, unicode)):
        layer['subtract-from'] = [layer['subtract-from']]


def parse_layer_cropping(layer):
    if 'crop-to' not in layer:
        layer['crop-to'] = False
        return


def parse_layer_graticule(layer):
    if 'latitudes' not in layer:
        layer['latitudes'] = []
    elif isinstance(layer['latitudes'], (int, float)):
        step = layer['latitudes']
        layer['latitudes'] = [0]
        for lat in _xfrange(step, 90, step):
            layer['latitudes'] += [lat, -lat]

    if 'longitudes' not in layer:
        layer['longitudes'] = []
    elif isinstance(layer['longitudes'], (int, float)):
        step = layer['longitudes']
        layer['longitudes'] = [0]
        for lon in _xfrange(step, 181, step):
            if lon == 180:
                p = [lon]
            else:
                p = [lon, -lon]
            layer['longitudes'] += p


def _xfrange(start, stop, step):
    while (step > 0 and start < stop) or (step < 0 and start > step):
        yield start
        start += step


def parse_bounds(opts):
    if 'bounds' not in opts:
        opts['bounds'] = {}
        #return
    bounds = opts['bounds']
    if 'mode' not in bounds:
        bounds['mode'] = 'bbox'

    if 'data' not in bounds:
        bounds['data'] = [-180, -90, 180, 90]
        bounds['mode'] = 'bbox'

    mode = bounds['mode']
    data = bounds['data']

    if "padding" not in bounds:
        bounds["padding"] = 0

    if mode == "bbox":
        try:
            if len(data) == 4:
                for i in range(0, 4):
                    data[i] = float(data[i])
            else:
                raise Error('bounds mode bbox requires array with exactly 4 values [lon0,lat0,lon1,lat]')
        except Error as err:
            raise err
        except:
            raise Error('bounds mode bbox requires array with exactly 4 values [lon0,lat0,lon1,lat]')
    elif mode == "points":
        try:
            for i in range(0, len(data)):
                pt = data[i]
                if len(pt) == 2:
                    pt = map(float, pt)
                else:
                    raise Error('bounds mode points requires array with (lon,lat) tuples')
        except Error as err:
            raise err
        except:
            raise Error('bounds mode points requires array with (lon,lat) tuples')
    elif mode in ("polygons", "polygon"):
        bounds['mode'] = mode = "polygons"
        if "layer" not in data or not is_str(data["layer"]):
            raise Error('you must specify a layer for bounds mode ' + mode)
        if "attribute" not in data or not is_str(data["attribute"]):
            data["attribute"] = None
        if "values" not in data:
            if data["attribute"] is None:
                data["values"] = None
            else:
                raise Error('you must specify a list of values to match in bounds mode ' + mode)
        if is_str(data["values"]):
            data["values"] = [data["values"]]
        if "min-area" in data:
            try:
                data["min-area"] = float(data["min-area"])
            except:
                raise Error('min_area must be an integer or float')
        else:
            data['min-area'] = 0


def parse_export(opts):
    if "export" not in opts:
        opts["export"] = {}
    exp = opts["export"]
    if "width" not in exp and "height" not in exp:
        exp["width"] = 1000
        exp["height"] = "auto"
    elif "height" not in exp:
        exp["height"] = "auto"
    elif "width" not in exp:
        exp["width"] = "auto"

    if "ratio" not in exp:
        exp["ratio"] = "auto"
    if "round" not in exp:
        exp["round"] = False
    else:
        exp["round"] = int(exp["round"])
