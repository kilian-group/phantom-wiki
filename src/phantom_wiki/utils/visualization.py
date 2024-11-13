import pydot

# TODO documentation (docstrings)
# TODO typing hints
# TODO more explanatory method names


# Function to read prolog file to facts
def prolog_to_facts(file):
    prolog_facts = []

    with open(file) as f_pl:
        for fact in f_pl.readlines():
            if len(fact) > 1:
                prolog_facts.append(fact[:-2])

    return prolog_facts


# Function to parse Prolog-style facts and add them to a Dot graph
def create_dot_graph(prolog_facts):
    graph = pydot.Dot(graph_type="digraph")  # Directed graph
    genders = {}  # Dictionary to store gender information

    for fact in prolog_facts:
        if fact.startswith("parent"):
            fact = fact.replace("parent(", "").replace(")", "")
            parent, child = fact.split(", ")
            edge = pydot.Edge(child, parent)
            graph.add_edge(edge)

        # Parse gender facts
        elif fact.startswith("male"):
            fact = fact.replace("male(", "").replace(")", "")
            genders[fact] = "male"
        elif fact.startswith("female"):
            fact = fact.replace("female(", "").replace(")", "")
            genders[fact] = "female"

    # Add nodes and color them based on gender
    for node in {n for edge in graph.get_edges() for n in [edge.get_source(), edge.get_destination()]}:
        color = "green"  # Default color if gender is unknown
        if node in genders:
            if genders[node] == "male":
                color = "lightblue"
            elif genders[node] == "female":
                color = "pink"

        # Add the node with the specified color
        graph.add_node(pydot.Node(node, style="filled", fillcolor=color))

    return graph
