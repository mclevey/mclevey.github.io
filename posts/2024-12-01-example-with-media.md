---
title: Working with Images and Tables in Blog Posts
date: 2024-12-01
excerpt: A demonstration of images, tables, and other media elements in blog posts with lightbox support.
---

This post demonstrates how to include images and tables in blog posts. Click any image to view it in a lightbox.

## Images

Images can be included using standard markdown syntax. Here's an example using one of the book covers:

![Doing Computational Social Science](../images/DCSS.png)

You can also include images with captions by wrapping them in HTML figure elements:

<figure>
  <img src="../images/SHSNA.png" alt="Sage Handbook of Social Network Analysis">
  <figcaption>The Sage Handbook of Social Network Analysis, 2nd Edition (2023)</figcaption>
</figure>

## Tables

Tables are useful for presenting structured data. Here's an example comparing different network analysis packages:

| Package       | Language   | Primary Use              | License |
| ------------- | ---------- | ------------------------ | ------- |
| graph-tool    | Python/C++ | General network analysis | LGPL    |
| NetworkX      | Python     | General network analysis | BSD     |
| igraph        | R/Python/C | General network analysis | GPL     |
| metaknowledge | Python     | Bibliometric networks    | GPL     |
| Nate          | Python     | Text networks            | MIT     |

### Performance Comparison

Here's another table showing hypothetical performance metrics:

| Dataset Size | graph-tool | NetworkX | igraph |
| ------------ | ---------- | -------- | ------ |
| 1K nodes     | 0.1s       | 0.2s     | 0.15s  |
| 10K nodes    | 0.8s       | 3.2s     | 1.1s   |
| 100K nodes   | 12s        | 180s     | 25s    |
| 1M nodes     | 150s       | N/A      | 420s   |

## Combining Elements

You can combine text, images, and tables to create rich content. For example, when discussing book publications:

<figure>
  <img src="../images/F2FP.png" alt="The Face-to-Face Principle">
  <figcaption>The Face-to-Face Principle and the Internet (2022)</figcaption>
</figure>

The table below summarizes key publication details:

| Title                  | Year | Publisher | Co-authors        |
| ---------------------- | ---- | --------- | ----------------- |
| Sage Handbook of SNA   | 2023 | Sage      | Scott, Carrington |
| Doing CSS              | 2022 | Sage      | -                 |
| Face-to-Face Principle | 2022 | MIT Press | Tindall           |
| Industrial Development | 2020 | Palgrave  | Stoddart, Tindall |

## Code with Images

When writing tutorials, you might want to show code alongside visualizations:

```python
import graph_tool.all as gt

# Load the political blogs network
g = gt.collection.data["polblogs"]

# Fit a nested stochastic blockmodel
state = gt.minimize_nested_blockmodel_dl(g)

# Draw the network
state.draw(output="network.png")
```

The output would be a network visualization showing the community structure detected by the model.

## Summary

This post demonstrated:

- Basic image embedding with markdown
- Images with captions using HTML figures
- Tables with headers and data
- Combining different content types
- Lightbox functionality (click any image to enlarge)
