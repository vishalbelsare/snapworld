import sys

import swlib

# TODO (smacke): This is logically two tasks. They both deal with the
# same portion of the graph, though, so it seems as though they are
# crammed into one in order to avoid sending the graph over the network.
# Is it possible for snapworld to mandate that certain tasks run on the
# same physical node and share state over the disk? That seems like it
# would make the most sense here, though maybe that violates some sort
# of fundamental law of how BSP should work.

def GetNbr(sw):
    """
    generate the graph neighbors
    """

    taskname = sw.GetName()

    msglist = sw.GetMsgList()
    sw.log.debug("msglist %s" % str(msglist))

    ds = sw.LoadState() # TODO (smacke): What happens if there is no state to load?
    # If that happens it may make sense to assert dmsg['cmd'] == 'init' for every dmsg
    
    edges = []
    for item in msglist: # For non-init part of this task, we get 1 msg per GetDist task
        dmsg = sw.GetMsg(item)
        cmd = dmsg["cmd"]
        msg = dmsg["body"]

        if cmd == "init":
            edges.extend(msg)
        else:
            GetNeighbors(sw, ds, msg)

    if len(edges) > 0:
        # first iteration: input are edges, save the state
        ds = GetEdges(edges)
        sw.log.debug("state %s" % str(ds))
        sw.SaveState(ds) # This task is responsible for this portion of adjacency list

        dmsgout = {}
        dmsgout["src"] = sw.GetName()
        dmsgout["cmd"] = "targets"
        dmsgout["body"] = {}
        sw.Send(0,dmsgout,"2")

def GetEdges(edges):

    #print edges
    sw.log.debug("edges %s" % str(edges))
    
    # collect neighbors for each node
    nbrs = {}
    for item in edges:
        src = item[0]
        dst = item[1]
        if not nbrs.has_key(src):
            nbrs[src] = set()
        nbrs[src].add(dst)

    # convert sets to lists
    d = {}
    for key, value in nbrs.iteritems():
        d[key] = list(value)

    return d

def GetNeighbors(sw, ds, msg):
    # report node neighbors

    tdst = msg["task"]
    nodes = msg["nodes"]
    s = set()
    for node in nodes:
        snode = str(node)
        s = s.union(set(ds[snode]))

    dmsgout = {}
    dmsgout["src"] = sw.GetName()
    dmsgout["cmd"] = "nbrs"
    dmsgout["body"] = list(s)
    sw.Send(tdst,dmsgout) # this is over port 1, since that's the default

def Worker(sw):
    GetNbr(sw)

if __name__ == '__main__':
    
    sw = swlib.SnapWorld()
    sw.Args(sys.argv)

    fname = "swwork-%s.log" % (sw.GetName())

    sw.SetLog(fname)
    sw.GetConfig()

    Worker(sw)

    sw.log.info("finished")
 
