from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = [[0] * vertices for _ in range(vertices)]
        self.orig_graph = [[0] * vertices for _ in range(vertices)]
        self.steps = []  

    def add_edge(self, u, v, capacity):
        self.graph[u][v] = capacity
        self.orig_graph[u][v] = capacity

    def dfs(self, s, t, parent):
        visited = [False] * self.V
        stack = [s]
        visited[s] = True

        while stack:
            u = stack.pop()
            for v, capacity in enumerate(self.graph[u]):
                if not visited[v] and capacity > 0:
                    stack.append(v)
                    visited[v] = True
                    parent[v] = u
                    if v == t:
                        return True
        return False

    def ford_fulkerson(self, source, sink):
        parent = [-1] * self.V
        max_flow = 0

        while self.dfs(source, sink, parent):
            path_flow = float("Inf")
            s = sink
            path = []
            
            while s != source:
                path.insert(0, s)
                path_flow = min(path_flow, self.graph[parent[s]][s])
                s = parent[s]
            path.insert(0, source)

            max_flow += path_flow
            v = sink
            
            while v != source:
                u = parent[v]
                self.graph[u][v] -= path_flow
                self.graph[v][u] += path_flow
                v = parent[v]
                
            # Store both the path and the flow added in this step
            self.steps.append({"path": path, "flow": path_flow})

        return max_flow

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schedule', methods=['POST'])
def schedule():
    data = request.json
    batches = [int(x.strip()) for x in data['batches'].split(',') if x.strip()]
    classrooms = [int(x.strip()) for x in data['classrooms'].split(',') if x.strip()]
    timeslots = [x.strip() for x in data['timeslots'].split(',') if x.strip()]

    B, C, T = len(batches), len(classrooms), len(timeslots)
    total_nodes = 1 + B + C + T + 1
    
    g = Graph(total_nodes)
    source = 0
    sink = total_nodes - 1
    
    offset_b = 1
    offset_c = B + 1
    offset_t = B + C + 1

    nodes = [{"id": 0, "label": "Source", "level": 0}]
    for i in range(B): nodes.append({"id": offset_b + i, "label": f"B{i+1} ({batches[i]})", "level": 1})
    for j in range(C): nodes.append({"id": offset_c + j, "label": f"C{j+1} ({classrooms[j]})", "level": 2})
    for k in range(T): nodes.append({"id": offset_t + k, "label": timeslots[k], "level": 3})
    nodes.append({"id": sink, "label": "Sink", "level": 4})

    edges = []

    for i in range(B):
        g.add_edge(source, offset_b + i, 1)
        edges.append({"source": source, "target": offset_b + i, "capacity": 1})

    for i in range(B):
        for j in range(C):
            if batches[i] <= classrooms[j]:
                g.add_edge(offset_b + i, offset_c + j, 1)
                edges.append({"source": offset_b + i, "target": offset_c + j, "capacity": 1})

    for j in range(C):
        for k in range(T):
            g.add_edge(offset_c + j, offset_t + k, 1)
            edges.append({"source": offset_c + j, "target": offset_t + k, "capacity": 1})

    for k in range(T):
        g.add_edge(offset_t + k, sink, C)
        edges.append({"source": offset_t + k, "target": sink, "capacity": C})

    max_classes = g.ford_fulkerson(source, sink)

    room_to_times = {j: [] for j in range(C)}
    for j in range(C):
        node_c = offset_c + j
        for k in range(T):
            node_t = offset_t + k
            if g.orig_graph[node_c][node_t] == 1 and g.graph[node_c][node_t] == 0:
                room_to_times[j].append(k)

    results = []
    for i in range(B):
        node_b = offset_b + i
        if g.orig_graph[source][node_b] == 1 and g.graph[source][node_b] == 0:
            for j in range(C):
                node_c = offset_c + j
                if g.orig_graph[node_b][node_c] == 1 and g.graph[node_b][node_c] == 0:
                    assigned_t_index = room_to_times[j].pop()
                    results.append(f"Batch {i+1} ({batches[i]}) -> Room {j+1} ({classrooms[j]}) at {timeslots[assigned_t_index]}")
                    break

    return jsonify({
        "nodes": nodes,
        "edges": edges,
        "steps": g.steps,
        "max_classes": max_classes,
        "schedule": results
    })

if __name__ == '__main__':
    app.run(debug=True)