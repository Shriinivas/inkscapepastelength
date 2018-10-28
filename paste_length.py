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

import inkex, cubicsuperpath, bezmisc, simpletransform, sys

class PasteLengthEffect(inkex.Effect):

    def __init__(self):

        inkex.Effect.__init__(self)

        self.OptionParser.add_option('-s', '--scale', action = 'store',
          type = 'float', dest = 'scale', default = '1',
          help = 'Additionally scale the length by')

        self.OptionParser.add_option('-f', '--scaleFrom', action = 'store',
          type = 'string', dest = 'scaleFrom', default = 'center',
          help = 'Scale Path From')

        self.OptionParser.add_option('-p', '--precision', action = 'store',
          type = 'int', dest = 'precision', default = '5',
          help = 'Number of significant digits')

        self.OptionParser.add_option("--tab", action="store", 
          type="string", dest="tab", default="sampling", help="Tab") 

    def scaleCubicSuper(self, cspath, scaleFactor, scaleFrom):

        xmin, xmax, ymin, ymax = simpletransform.refinedBBox(cspath)
        
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
                
    def getPartsFromCubicSuper(self, cspath):
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
        
    def getLength(self, cspath, tolerance):
        parts = self.getPartsFromCubicSuper(cspath)
        curveLen = 0
        
        for i, part in enumerate(parts):
            for j, seg in enumerate(part):
                curveLen += bezmisc.bezierlengthSimpson((seg[0], seg[1], seg[2], seg[3]), 
                    tolerance = tolerance)
                
        return curveLen

    def effect(self):
        scale = self.options.scale
        scaleFrom = self.options.scaleFrom
        
        tolerance = 10 ** (-1 * self.options.precision)
        
        printOut = False
        selections = self.selected        
        pathNodes = self.document.xpath('//svg:path',namespaces=inkex.NSS)
        outStrs = [str(len(pathNodes))]

        paths = [(pathNode.get('id'), cubicsuperpath.parsePath(pathNode.get('d'))) \
            for pathNode in  pathNodes if (pathNode.get('id') in selections.keys())]

        if(len(paths) > 1):
            srcPath = paths[-1][1]
            srclen = self.getLength(srcPath, tolerance)
            paths = paths[:len(paths)-1]
            for key, cspath in paths:
                curveLen = self.getLength(cspath, tolerance)
                
                self.scaleCubicSuper(cspath, scaleFactor = scale * (srclen / curveLen), \
                scaleFrom = scaleFrom)
                selections[key].set('d', cubicsuperpath.formatPath(cspath))
        else:
            inkex.errormsg(_("Please select at least two paths, with the path whose \
            length is to be copied at the top. You may have to convert the shape \
            to path with path->Object to Path."))

effect = PasteLengthEffect()
effect.affect()
