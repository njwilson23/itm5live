
function createTimeSeriesAxes(geom, id, label) {
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
  ax.series = d3.map();
  return ax;
}

/* given and axes object, add a line */
function addScalarTimeSeries(ax, data, className) {

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

  var path = ax.g.append("path").datum(data)
    .attr("class", "line active " + className)
    .attr("d", line);

  ax.series.set(className, line);
  return {"path": path, "line": line};
}

function addVectorTimeSeries(ax, data, className) {

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
    ax.yDomain[1] = Math.max(yExtent[1], ax.yDomain[1], 5);
  } else {
    ax.yDomain[1] = Math.max(yExtent[1], 5);
  }

  ax.x.domain(ax.xDomain);
  ax.y.domain(ax.yDomain);
  ax.x_.domain(ax.xDomain);

  ax.gX.call(ax.xAxis);
  ax.gY.call(ax.yAxis);

  var g = ax.g.append("g").attr("class", "active " + className);

  var line = g.selectAll("line")
      .data(data);

  line.enter()
      .append("line")
      .attr("x1", function(d) { return ax.x(d.t) })
      .attr("y1", function(d) { return ax.y(d.y) })
      .attr("x2", function(d) { return ax.x(d.t)+d.vx })
      .attr("y2", function(d) { return ax.y(d.y)+d.vy })
      .attr("class", "vec "+className)
    .merge(line);

  var circle = g.selectAll("circle")
      .data(data);

  circle.enter().append("circle")
      .attr("cx", function(d) {return ax.x(d.t)})
      .attr("cy", function(d) {return ax.y(d.y)})
      .attr("r", 1.8)
      .attr("class", "vec active "+className)
    .merge(circle);
}

function rescaleAxes(ax) {
  ax.g.selectAll(".line")
    .attr("d", ax.series.values()[0]);

  ax.g.selectAll("circle.vec")
    .attr("cx", function(d) {
      return ax.x(d.t);
    });

  ax.g.selectAll("line.vec")
    .attr("x1", function(d) {
      return ax.x(d.t);
    })
    .attr("x2", function(d) {
      var v = normalizeVec(100*d.east, 100*d.north);
      return ax.x(d.t)+d.vx;
    });
}

function zoomed() {
  var ax, t = d3.event.transform;
  for (var i=0; i!=axes.length; i++) {
    ax = axes[i];
    ax.x.domain(t.rescaleX(ax.x_).domain());
    ax.gX.call(ax.xAxis.scale(ax.x));
    rescaleAxes(ax);
  }
}

function filterNulls(d) {
  var k = Object.keys(d);
  for (var i=0; i!=k.length; i++) {
      if (d[k[i]] === null) {
      return false;
      }
  }
  return true;
}

function normalizeVec(u, v) {
      var mag = Math.sqrt(u*u + v*v);
      if (mag == 0) {
          return {mag: mag, u: 0, v: 0};
      } else {
          return {mag: mag, u: u/mag, v: v/mag};
      }
}
