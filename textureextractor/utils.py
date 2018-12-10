def calculate_edge_table(v1, v2, v3):
    # x of lowest vertex,  y of lowest vertex, y of highest vertex, inverse slop
    edge12 = [v1[0] if v1[1] < v2[1] else v2[0],
              v1[1] if v1[1] < v2[1] else v2[1],
              v1[1] if v1[1] > v2[1] else v2[1],
              (v1[0] - v2[0]) / (v1[1] - v2[1]) if (v1[1] - v2[1]) != 0 else 0]
    edge23 = [v2[0] if v2[1] < v3[1] else v3[0],
              v2[1] if v2[1] < v3[1] else v3[1],
              v2[1] if v2[1] > v3[1] else v3[1],
              (v2[0] - v3[0]) / (v2[1] - v3[1]) if (v2[1] - v3[1]) != 0 else 0]
    edge31 = [v3[0] if v3[1] < v1[1] else v1[0],
              v3[1] if v3[1] < v1[1] else v1[1],
              v3[1] if v3[1] > v1[1] else v1[1],
              (v3[0] - v1[0]) / (v3[1] - v1[1]) if (v3[1] - v1[1]) != 0 else 0]

    active_edges = []
    # start with edges with lowest y
    if edge12[1] < edge23[1] or edge12[1] < edge31[1]:
        active_edges.append(edge12)
        if edge23[1] < edge31[1]:
            active_edges.append(edge23)
            inactive_edge = edge31
        else:
            active_edges.append(edge31)
            inactive_edge = edge23
    else:
        active_edges.append(edge23)
        active_edges.append(edge31)
        inactive_edge = edge12

    # check top horizontal edge in active edge list and remove
    if active_edges[0][1] == active_edges[0][2]:
        active_edges[0] = inactive_edge
        inactive_edge = None
    elif active_edges[1][1] == active_edges[1][2]:
        active_edges[1] = inactive_edge
        inactive_edge = None

    # sort active edges by x
    if active_edges[0][0] > active_edges[1][0] or active_edges[0][3] > active_edges[1][3]:
        e1 = active_edges[0]
        e2 = active_edges[1]
        active_edges = [e2, e1]

    return active_edges, inactive_edge


def triangle_area(a, b, c):
    return 0.5 * ((a[0] - c[0]) * (b[1] - c[1]) - (a[1] - c[1]) * (b[0] - c[0]))
