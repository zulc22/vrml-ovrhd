from vrml.vrml97.parser import buildParser
from vrml.vrml97.scenegraph import SceneGraph
import sys, os
import charset_normalizer

# to prevent issues if more than one file uses a .wrl or if they somehow use recursive inlines
ALREADY_PROCESSED = []

VRMLPARSER = buildParser()

depth=0
def fixup_vrml(file: str):
    global depth
    depth+=1
    file_display = os.path.basename(file)
    depth_indicator = "-"*depth
    print(depth_indicator, "Opening",file_display,"...")
    with open(file, 'rb') as f:
        cn = charset_normalizer.from_fp(f)
        cs = cn.best()
        print(depth_indicator, "Charset detected as",cs.encoding,f"(aka {'/'.join(cs.encoding_aliases)})")
        wrldata = str(cs)
    print(depth_indicator, "Parsing",file_display,"...")
    wrl = VRMLPARSER.parse(wrldata)[1][1] # type: SceneGraph
    print(depth_indicator, "Scanning",file_display,"...")
    fixup_node(wrl)
    print(depth_indicator, "Fixed",fixed_verts_stack[-1],"verts")
    if fixed_verts_stack[-1] > 0:
        print(depth_indicator, "Saving",file_display,"...")
        wrldata = wrl.toString()
        with open(file,'w') as f:
            f.write(wrldata)
    depth-=1

def fixup_node(node):

    if hasattr(node, 'geometry'):
        checkdupedverts(node.geometry)

    if not hasattr(node, 'children'): return
    for n in node.children:
        fixup_node(n)

fixed_verts_stack=[0]
def checkdupedverts(geo):
    # count usage of verts
    dupedverts = {}
    for c in geo.coordIndex:
        if c == -1: continue
        if c in dupedverts: dupedverts[c] += 1
        else: dupedverts[c] = 1
    # filter to duplicated verts
    dupedverts = {k:v for (k,v) in dupedverts.items() if v>1}
    if len(dupedverts) == 0: return
    global fixed_verts_stack
    fixed_verts_stack[-1] += sum([v-1 for v in dupedverts.values()])
    import numpy as np
    for k in dupedverts:
        occ=0
        for i,c in enumerate(geo.coordIndex.copy()):
            if c==k: occ+=1
            else: continue
            if occ>1:
                geo.coord.point = np.append(geo.coord.point, np.reshape(geo.coord.point[k].copy(), (1,-1)), axis=0)
                geo.coordIndex[i] = len(geo.coord.point)-1
                # print(f"occ#{occ} ci[{i}]: {c} -> {geo.coordIndex[i]}")
                # import code; code.interact(local=locals())

file = sys.argv[1]
# file="sapariblend/entry.wrl"
fixup_vrml(file)

