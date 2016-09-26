
function createLineAxes(geom, id, label) {
  var ax = Object();

  var margin = geom.margin,
      width = geom.width,
      height = geom.height;

  /* Define an original time scale to use when rescaling the actual time scale */
  var x = d3.scaleTime().range([0, width]),
      y = d3.scaleLinear().range([height, 0]),
      x_orig = d3.scaleTime().range([0, width]);

  var svg = d3.select(id).append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

  var g = svg.append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var xDomain = [NaN, NaN],
      yDomain = [NaN, NaN];

  var xAxis = d3.axisBottom(x),
      yAxis = d3.axisLeft(y);

  var gX = g.append("g")
      .attr("class", "axis axis--x")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

  var gY = g.append("g")
      .attr("class", "axis axis--y")
      .call(yAxis);

  svg.append("text")
      .attr("class", "y label")
      .attr("x", -height-margin.top)
      .attr("y", 16)
      .attr("dy", ".75em")
      .attr("transform", "rotate(-90)")
      .text(label);

  svg.append("defs").append("clipPath")
        .attr("id", "clip")
      .append("rect")
        .attr("width", width)
        .attr("height", height);

  var zoomRect = g.append("rect")
    .attr("width", width)
    .attr("height", height)
    .attr("class", "plotArea");

  ax.xDomain = xDomain;
  ax.yDomain = yDomain;
  ax.margin = margin;
  ax.svg = svg;
  ax.g = g;
  ax.gX = gX;
  ax.gY = gY;
  ax.x = x;
  ax.y = y;
  ax.x_ = x_orig;
  ax.xAxis = xAxis;
  ax.yAxis = yAxis;
  ax.zoomRect = zoomRect;
  ax.lines = [];
  return ax;
}

/* given and axex object, add a line */
function addLine(ax, data, lineClass) {

  var xExtent = d3.extent(data, function(d) { return d.t; }),
      yExtent = d3.extent(data, function(d) { return d.y; });

  if (isFinite(ax.xDomain[0])) {
    ax.xDomain[0] = Math.min(xExtent[0], ax.xDomain[0]);
  } else {
    ax.xDomain[0] = xExtent[0];
  }

  if (isFinite(ax.xDomain[1])) {
    ax.xDomain[1] = Math.max(xExtent[1], ax.xDomain[1]);
  } else {
    ax.xDomain[1] = xExtent[1];
  }

  if (isFinite(ax.yDomain[0])) {
    ax.yDomain[0] = Math.min(yExtent[0], ax.yDomain[0]);
  } else {
    ax.yDomain[0] = yExtent[0];
  }

  if (isFinite(ax.yDomain[1])) {
    ax.yDomain[1] = Math.max(yExtent[1], ax.yDomain[1]);
  } else {
    ax.yDomain[1] = yExtent[1];
  }

  ax.x.domain(ax.xDomain);
  ax.y.domain(ax.yDomain);
  ax.x_.domain(ax.xDomain);

  ax.gX.call(ax.xAxis);
  ax.gY.call(ax.yAxis);

  var line = d3.line()
    .x(function(d) { return ax.x(d.t); })
    .y(function(d) { return ax.y(d.y); });

  var path = ax.g.append("path")
    .datum(data)
    .attr("class", "line active " + lineClass)
    .attr("d", line);

  ax.lines.push(line);
  return {"path": path, "line": line};
}

function rescaleAllLines(ax) {
  ax.g.selectAll(".line")
    .attr("d", ax.lines[0]);
}

function createVectorAxes(geom, label) {

}

function addVectors(ax, data) {

}

function zoomed() {
  var ax,
      t = d3.event.transform;
  for (var i=0; i!=axes.length; i++) {
    ax = axes[i];
    ax.x.domain(t.rescaleX(ax.x_).domain());
    ax.gX.call(ax.xAxis.scale(ax.x));
    ax.g.selectAll(".line")
      .attr("d", ax.lines[0]);
  }
}

