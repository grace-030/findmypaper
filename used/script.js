const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("svg");

d3.json("graph.json").then(data => {
  const { nodes, links } = data;

  // Initialize simulation
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(30))
    .force("charge", d3.forceManyBody().strength(-10))
    .force("center", d3.forceCenter(width / 2, height / 2));

  // Draw links
  const link = svg.append("g")
    .attr("stroke", "#aaa")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke-opacity", 0.5);

  // Draw nodes
  const node = svg.append("g")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", 3)
    .attr("fill", d => d3.interpolateCool(d.pagerank))  // use pagerank for coloring
    .call(drag(simulation));

  // Tooltip
  node.append("title").text(d => d.title);

  // Update positions
  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);
  });

  // Dragging logic
  function drag(simulation) {
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
  }
});
