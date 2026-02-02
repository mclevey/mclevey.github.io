---
title: Modeling and Visualizing Network Structure with graph-tool
date: 2024-11-12
excerpt: I iteratively develop network visualizations of Adamic and Glance's political blogs network and show how to fit a simple nested stochastic blockmodel.
---

I iteratively develop network visualizations of Adamic and Glance's political blogs network and show how to fit a simple nested stochastic blockmodel to the observed network.

**Categories:** Python, graph-tool, Networks, Nested Stochastic Blockmodels, Bayesian Data Analysis, Generative Modeling, Visualization

## Setup

```python
import numpy as np
import graph_tool.all as gt
import matplotlib as mpl
from icsspy.networks import rotate_positions

print(f"Using graph-tool version {gt.__version__}")
```

Load the data.

```python
g = gt.collection.data["polblogs"]
print(g)
```

## Property Maps

We can look up the political class for any given node by passing its integer ID. For example, vertex 30:

```python
g.vp.value[30]
```

To view all classifications, we can iterate over the vertices and print each vertex ID followed by its class label.

```python
for v in g.vertices():
    print(v, g.vp.value[v])
```

```python
political_colors = {0: "#2F357E", 1: "#D72F32"}  # color map
vertex_political_colors = g.new_vertex_property("string")  # new vertex property

# assign colors to each vertex based on the political classification
for v in g.vertices():
    vertex_political_colors[v] = political_colors[g.vp.value[v]]
```

As a first step, let's recreate the political blogs figures we've seen so far (including those based on the nested SBM). We'll assign node positions using the **stable force directed placement** function, `sfdp_layout()`. This will more-or-less recreate the force directed layout from the original.

```python
pos = gt.sfdp_layout(g)

f1 = gt.graph_draw(
    g, pos,
    vertex_fill_color=vertex_political_colors,
    output_size=(1200, 1200),
    inline=True
)
```

Let's just focus on the giant component for a cleaner visualization. We'll also rotate the graph's position to match the figures more closely.

```python
giant = gt.extract_largest_component(g, directed=True)

pos = gt.sfdp_layout(giant)
pos = rotate_positions(pos, a=90)

f2 = gt.graph_draw(
    giant, pos,
    vertex_fill_color=vertex_political_colors,
    output_size=(1200, 1200),
    inline=True
)
```

## Fitting a First NSBM

Next, we fit an SBM and color the nodes based on their estimated block membership.

```python
blockstate = gt.minimize_nested_blockmodel_dl(giant)
blockstate_level_0 = blockstate.levels[0]
blockstate_level_0
```

We can use the `.draw()` method for blockstate objects to visualize the network with inferred communities.

```python
f3 = blockstate_level_0.draw(
    pos=pos,
    output_size=(1200, 1200),
)
```

As a refinement step **based on model criticism**, we'll adjust the force-directed layout by adding an attractive force between nodes in the same block. This is done by passing the following arguments to `sfdp_layout()`:

- `groups`: A vertex property map that assigns nodes to specific groups, in this case, block assignments at the lowest level of the nested SBM (`blockstate_level_0.b`). This adds additional attractive forces for block membership in the layout.
- `gamma`: Controls the strength of the attractive force for nodes in the same block. A small value corresponds to a weak force and more spread out clusters, while a larger value results in more compact clusters.

```python
pos_refined = gt.sfdp_layout(g, groups=blockstate_level_0.b, gamma=.04)
pos_refined = rotate_positions(pos_refined, 125)  # make it horizontal
```

## Divided They Blog?

### Adjusting Node Colors & Exploring Hierarchy

For the final adjustment, let's assign node colors based on political classification rather than block membership and use a layout that is designed to emphasize the hierarchical structure of the network.

```python
f5 = blockstate.draw(
    vertex_fill_color=vertex_political_colors,
    output_size=(1200, 1200),
    inline=True,
)
```

This visualization reveals the hierarchical structure more clearly. The blue square node right in the middle of the network represents the entire graph merged into one group at the highest level of the block hierarchy. As you move outward from the center, the graph splits into smaller and smaller blocks, which correspond to different political blogs at the lowest level of the block hierarchy.

You may notice that the nested SBM reveals a more complex structure than a simple left-right division. The hierarchy shows internal differentiation within each political cluster, revealing sub-communities that were not as apparent in the force-directed layout.

### Summary

With that, we've successfully recreated the series of political blog network figures using `graph-tool`. We learned how to:

- Extract the giant component from a network
- Fit our first nested Stochastic Blockmodel (NSBM)
- Create a series of visualizations of the network and its hierarchical block structure
- Adjust force-directed layouts to add additional attractors for group memberships based on simple model criticism
- Modify and refine the visual properties of networks at different levels of the block hierarchy

In the next part of the tutorial, we'll explore the Enron email networks, applying similar techniques and deepening our understanding of community detection in large networks.
