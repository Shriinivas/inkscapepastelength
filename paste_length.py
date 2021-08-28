#!/usr/bin/env python

'''
Inkscape extension to copy length of the source path to the selected
destination path(s)

Copyright (C) 2018  Shrinivas Kulkarni

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import inkex

# TODO: Find inkscape version
try:
    from inkex.paths import Path, CubicSuperPath
    from inkex import bezier
    ver = 1.0
except:
    import cubicsuperpath, bezmisc, simpletransform
    ver = 0.92

######### Function variants for 1.0 and 0.92 - Start ##########

# Used only in 0.92
def getPartsFromCubicSuper(cspath):
    parts = []
    for subpath in cspath:
        part = []
        prevBezPt = None
        for i, bezierPt in enumerate(subpath):
            if(prevBezPt != None):
                seg = [prevBezPt[1], prevBezPt[2], bezierPt[0], bezierPt[1]]
                part.append(seg)
            prevBezPt = bezierPt
        parts.append(part)
    return parts

def formatPath(cspath):
    if(ver == 1.0):
        return cspath.__str__()
    else:
        return cubicsuperpath.formatPath(cspath)

def getParsedPath(d):
    if(ver == 1.0):
        return CubicSuperPath(Path(d).to_superpath())
    else:
        return cubicsuperpath.parsePath(d)

def getBoundingBox(cspath):
    if(ver == 1.0):
        bbox = cspath.to_path().bounding_box()
        return bbox.left, bbox.right, bbox.top, bbox.bottom
    else:
        return simpletransform.refinedBBox(cspath)

def getLength(cspath, tolerance):
    if(ver == 1.0):
        return bezier.csplength(cspath)[1]
    else:
        parts = getPartsFromCubicSuper(cspath)
        curveLen = 0

        for i, part in enumerate(parts):
            for j, seg in enumerate(part):
                curveLen += bezmisc.bezierlengthSimpson((seg[0], seg[1], seg[2], seg[3]), \
                tolerance = tolerance)

        return curveLen

def getSelections(effect):
    if(ver == 1.0):
        return {n.get('id'): n for n in effect.svg.selection.filter(inkex.PathElement)}
    else:
        return effect.selected

######### Function variants for 1.0 and 0.92 - End ##########

class PasteLengthEffect(inkex.Effect):

    def __init__(self):

        inkex.Effect.__init__(self)
        if(ver == 1.0):
            addFn= self.arg_parser.add_argument
            typeFloat = float
            typeInt = int
            typeString = str
        else:
            addFn = self.OptionParser.add_option
            typeFloat = 'float'
            typeInt = 'int'
            typeString = 'string'

        addFn('-s', '--scale', action = 'store', type = typeFloat, dest = 'scale', default = '1',
          help = 'Additionally scale the length by')

        addFn('-f', '--scaleFrom', action = 'store', type = typeString, \
            dest = 'scaleFrom', default = 'center', help = 'Scale Path From')

        addFn('-p', '--precision', action = 'store', type = typeInt, dest = 'precision', \
            default = '5', help = 'Number of significant digits')

        addFn("--tab", action = "store", type = typeString, dest = "tab", default = "sampling", \
            help="Tab")

    def scaleCubicSuper(self, cspath, scaleFactor, scaleFrom):

        xmin, xmax, ymin, ymax = getBoundingBox(cspath)

        if(scaleFrom == 'topLeft'):
            oldOrigin= [xmin, ymin]
        elif(scaleFrom == 'topRight'):
            oldOrigin= [xmax, ymin]
        elif(scaleFrom == 'bottomLeft'):
            oldOrigin= [xmin, ymax]
        elif(scaleFrom == 'bottomRight'):
            oldOrigin= [xmax, ymax]
        else: #if(scaleFrom == 'center'):
            oldOrigin= [xmin + (xmax - xmin) / 2., ymin + (ymax - ymin) / 2.]

        newOrigin = [oldOrigin[0] * scaleFactor , oldOrigin[1] * scaleFactor ]

        for subpath in cspath:
            for bezierPt in subpath:
                for i in range(0, len(bezierPt)):

                    bezierPt[i] = [bezierPt[i][0] * scaleFactor,
                        bezierPt[i][1] * scaleFactor]

                    bezierPt[i][0] += (oldOrigin[0] - newOrigin[0])
                    bezierPt[i][1] += (oldOrigin[1] - newOrigin[1])

    def effect(self):
        scale = self.options.scale
        scaleFrom = self.options.scaleFrom

        tolerance = 10 ** (-1 * self.options.precision)

        printOut = False
        selections = getSelections(self)
        pathNodes = self.document.xpath('//svg:path',namespaces = inkex.NSS)
        outStrs = [str(len(pathNodes))]

        paths = [(pathNode.get('id'), getParsedPath(pathNode.get('d'))) \
            for pathNode in  pathNodes if (pathNode.get('id') in selections.keys())]

        if(len(paths) > 1):
            srcPath = paths[-1][1]
            srclen = getLength(srcPath, tolerance)
            paths = paths[:len(paths)-1]
            for key, cspath in paths:
                curveLen = getLength(cspath, tolerance)

                self.scaleCubicSuper(cspath, scaleFactor = scale * (srclen / curveLen), \
                scaleFrom = scaleFrom)
                selections[key].set('d', formatPath(cspath))
        else:
            inkex.errormsg(_("Please select at least two paths, with the path whose " +
                "length is to be copied at the top. You may have to convert the shape " +
                "to path with path->Object to Path."))

if(ver == 1.0): PasteLengthEffect().run()
else: PasteLengthEffect().affect()
